# Walled AI — MCP Authorization Gateway

**Walled AI** is a local authorization layer for the Model Context Protocol (MCP). It intercepts MCP tool calls from Claude Desktop / Claude Web and presents them in a web-based security dashboard where the user can explicitly **allow** or **block** each request before it executes.

The system enforces a **fail-closed** policy: if the dashboard is unreachable or the user does not respond within the timeout window, the request is denied.

## Features

| Feature | Description |
|---------|-------------|
| **Real-time MCP monitoring** | Intercepts `read_file`, `write_file`, and `list_files` tool calls before execution |
| **User authorization dashboard** | Web UI (`Flask`) showing pending requests with Allow / Block decisions |
| **Fail-closed security** | Requests are denied if the dashboard is unavailable or times out |
| **Filesystem sandboxing** | All file operations are confined to a configurable root directory; absolute and traversal paths are rejected |
| **File size limits** | 1 MB cap on reads and writes |
| **Concurrent request support** | Thread-safe request queue with per-request event handling |
| **Request history** | Pending and recent decisions tracked with timestamps, server, tool, and parameters |
| **HTTP & stdio MCP transports** | `gateway.py` (stdio) and `gateway_http.py` (streamable-HTTP on port 8000) |
| **Transport security** | DNS rebinding protection and allow-listed hosts/origins |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Desktop / Claude Web              │
└───────────────────────────────┬─────────────────────────────┘
                                │ MCP (stdio / streamable-HTTP)
                                ▼
┌─────────────────────────────────────────────────────────────┐
│  Walled AI MCP Authorization Gateway (FastMCP)              │
│  • read_file / write_file / list_files                      │
│  • Sandbox path enforcement                                 │
│  • 1 MB file size limit                                     │
└───────────────┬───────────────────────────┬─────────────────┘
                │ authorization POST        │ dashboard
                ▼                           ▼
┌───────────────────────────┐   ┌─────────────────────────────┐
│  MCP Monitor              │   │  Flask Web Dashboard        │
│  (mcp_monitor/__init__.py)│   │  (mcp_monitor/web_interface)│
│  • Thread-safe queue      │   │  • /                        │
│  • wait_for_decision      │   │  • POST /mcp/authorize      │
│  • handle_decision        │   │  • POST /decision           │
│  • Fail-closed shutdown   │   │  • GET  /api/requests       │
└───────────────────────────┘   └─────────────────────────────┘
```

### Components

| File | Purpose |
|------|---------|
| `run.py` | Entry point. Starts the Flask dashboard (port 5055) and the MCP monitor loop (proxy port 8765). |
| `gateway.py` | FastMCP server (stdio transport) exposing filesystem tools that require authorization. |
| `gateway_http.py` | FastMCP server over streamable-HTTP (port 8000) for remote/Claude Web connections. |
| `mcp_monitor/__init__.py` | `MCPMonitor`: thread-safe request manager, `RequestStatus` enum, `MCPRequest` dataclass. |
| `mcp_monitor/web_interface.py` | Flask app with the authorization API and embedded dashboard HTML/CSS/JS. |
| `mcp_monitor/templates/` | Dashboard templates (`base.css`, `head.html`, `index.html`, `script.html`). |
| `test_files/` | Sandbox directory used for file read/write/list operations. |
| `test_app.py` | Smoke test for the Flask web interface. |
| `requirements.txt` | Python dependencies. |

## Installation

### Prerequisites

* Python 3.8+
* `pip`

### Install dependencies

```bash
cd Walled_AI-main
pip install -r requirements.txt
```

`requirements.txt`:

```
flask>=3.0,<4.0
mcp>=1.0,<2.0
pytest>=8.0,<10.0
```

## Configuration

Configuration is handled through environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_MONITOR_URL` | `http://127.0.0.1:5055/mcp/authorize` | Dashboard authorization endpoint called by the gateway |
| `MCP_TEST_ROOT` | `<repo>/test_files` | Sandbox root directory for filesystem operations |
| `AUTH_TIMEOUT` | `305` (gateway) / `300` (monitor) | Seconds to wait for a user decision before denying |
| `MAX_FILE_SIZE` | `1_000_000` | Maximum bytes for read/write operations |

## Usage

### 1. Start the dashboard and monitor

```bash
python run.py
```

Output:

```
============================================================
Walled AI - MCP Authorization System
============================================================
[*] Claude config: /Users/.../Library/Application Support/Claude/claude_desktop_config.json
[*] MCP servers: [...]
[SUCCESS] Dashboard: http://127.0.0.1:5055
[*] Press Ctrl+C to stop
```

Open **http://127.0.0.1:5055** in your browser to view pending requests and make Allow / Block decisions.

### 2. Run the MCP gateway (stdio)

```bash
python gateway.py
```

This launches the FastMCP server on stdio, suitable for Claude Desktop's local MCP server configuration.

### 3. Run the MCP gateway over HTTP

```bash
python gateway_http.py
```

Output:

```
Starting Walled AI HTTP MCP Server
MCP endpoint: http://127.0.0.1:8000/mcp
```

Use this when connecting Claude Web or remote clients to `http://127.0.0.1:8000/mcp`.

### 4. Connect Claude Desktop

Add Walled AI to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "walled-ai": {
      "command": "python",
      "args": ["C:/RN/Walled_AI-main/gateway.py"]
    }
  }
}
```

Restart Claude Desktop. Every filesystem tool call will now appear in the Walled AI dashboard for your approval.

## API Reference

The Flask dashboard exposes these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | GET | Security dashboard HTML (pending requests + recent decisions) |
| `POST /mcp/authorize` | JSON | Submits a request for authorization and blocks until the user decides (used by `gateway.py`) |
| `POST /decision` | JSON | Records a user Allow / Block decision (`{ request_id, decision }`) |
| `GET /api/requests` | JSON | Returns `{ pending: [...], all: [...] }` for dashboard polling |

### Request payload (`/mcp/authorize`)

```json
{
  "server": "filesystem",
  "tool": "read_file",
  "arguments": { "path": "example.txt" },
  "request_type": "tool_call"
}
```

### Decision payload (`/decision`)

```json
{
  "request_id": "<uuid>",
  "decision": "allow"
}
```

`decision` must be `"allow"` or `"block"`.

## Security Model

1. **Intercept before execution** — No filesystem tool runs until `request_authorization()` returns `"allow"`.
2. **Sandbox confinement** — `resolve_safe_path()` rejects absolute paths, null bytes, and any path resolving outside `MCP_TEST_ROOT`.
3. **Size limits** — Reads and writes are capped at 1 MB.
4. **Fail-closed** — Network errors, timeouts, invalid responses, and shutdown all result in denial.
5. **Transport security** — DNS rebinding protection and allow-listed hosts/origins on both stdio and HTTP MCP servers.

## Project Structure

```
Walled_AI-main/
├── README.md
├── requirements.txt
├── run.py                      # Entry point: dashboard + monitor
├── gateway.py                  # FastMCP stdio server (filesystem tools)
├── gateway_http.py             # FastMCP streamable-HTTP server (port 8000)
├── test_app.py                 # Flask smoke test
├── test_files/                 # Default sandbox directory
│   ├── test.txt
│   └── blocked_test.txt
├── mcp_monitor/
│   ├── __init__.py             # MCPMonitor, MCPRequest, RequestStatus
│   ├── web_interface.py        # Flask app + authorization API
│   └── templates/
│       ├── base.css
│       ├── head.html
│       ├── index.html
│       └── script.html
└── __pycache__/
```

## Testing

Run the Flask interface smoke test:

```bash
python test_app.py
```

Expected output:

```
Status: 200
Body: <!DOCTYPE html>...
```

Run the full test suite with pytest:

```bash
pytest
```

## License

MIT License
