
#!/usr/bin/env python3
"""Walled AI - MCP Authorization Gateway.

A local FastMCP server that requires user authorization before
executing its filesystem tools.
"""

import json
import logging
import os
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# --------------------------------------------------
# Configuration
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger("walled_ai.gateway")


mcp = FastMCP(
    "Walled AI Authorization Gateway",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "127.0.0.1:8000",
            "localhost:8000",
            "old-vienna-graphs-under.trycloudflare.com",
            "old-vienna-graphs-under.trycloudflare.com:443",
            "shakespeare-specials-perform-meat.trycloudflare.com",
            "shakespeare-specials-perform-meat.trycloudflare.com:443"
        ],
        allowed_origins=[
            "https://shakespeare-specials-perform-meat.trycloudflare.com",
        ],
    ),
)


DASHBOARD_URL = os.environ.get(
    "MCP_MONITOR_URL",
    "http://127.0.0.1:5055/mcp/authorize",
)

ROOT = Path(
    os.environ.get(
        "MCP_TEST_ROOT",
        str(Path(__file__).parent / "test_files"),
    )
).resolve()

ROOT.mkdir(parents=True, exist_ok=True)

AUTH_TIMEOUT = 305
MAX_FILE_SIZE = 1_000_000


# --------------------------------------------------
# Filesystem security
# --------------------------------------------------

def resolve_safe_path(relative_path: str) -> Path:
    """Resolve a path and reject paths outside the sandbox."""

    if not isinstance(relative_path, str):
        raise ValueError("Path must be a string")

    if not relative_path or "\x00" in relative_path:
        raise ValueError("Invalid path")

    supplied = Path(relative_path)

    if supplied.is_absolute():
        raise ValueError("Absolute paths are not permitted")

    candidate = (ROOT / supplied).resolve()

    try:
        candidate.relative_to(ROOT)
    except ValueError:
        raise PermissionError(
            "Access denied: path outside authorized directory"
        )

    return candidate


# --------------------------------------------------
# Authorization
# --------------------------------------------------

def request_authorization(
    tool: str,
    arguments: Dict[str, Any],
) -> None:
    """Wait for an explicit dashboard approval.

    Any communication error or unexpected response denies access.
    """

    payload = {
        "server": "filesystem",
        "tool": tool,
        "arguments": arguments,
        "request_type": "tool_call",
    }

    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        DASHBOARD_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=AUTH_TIMEOUT,
        ) as response:

            if response.status != 200:
                raise PermissionError(
                    "Authorization service returned an invalid status"
                )

            raw_response = response.read(65536)

        result = json.loads(raw_response.decode("utf-8"))

        if not isinstance(result, dict):
            raise PermissionError(
                "Invalid authorization response"
            )

        decision = result.get("decision")

        if decision != "allow":
            raise PermissionError(
                "MCP request denied by user authorization"
            )

        logger.info(
            "Request approved: tool=%s",
            tool,
        )

    except (
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
    ) as exc:

        logger.error(
            "Authorization service failure: %s",
            exc,
        )

        raise PermissionError(
            "Authorization unavailable. Request denied."
        ) from exc


# --------------------------------------------------
# MCP tools
# --------------------------------------------------

@mcp.tool()
def read_file(path: str) -> str:
    """Read a UTF-8 file inside the authorized test directory."""

    request_authorization(
        "read_file",
        {"path": path},
    )

    target = resolve_safe_path(path)

    try:
        with target.open("rb") as file:
            size = os.fstat(file.fileno()).st_size

            if size > MAX_FILE_SIZE:
                raise ValueError("File exceeds the 1 MB limit")

            content = file.read(MAX_FILE_SIZE + 1)

        if len(content) > MAX_FILE_SIZE:
            raise ValueError("File exceeds the 1 MB limit")

        return content.decode("utf-8")

    except FileNotFoundError:
        raise FileNotFoundError("File not found")

    except UnicodeDecodeError:
        raise ValueError("File is not valid UTF-8 text")


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write a UTF-8 file inside the authorized test directory."""

    if not isinstance(content, str):
        raise ValueError("Content must be a string")

    if len(content.encode("utf-8")) > MAX_FILE_SIZE:
        raise ValueError("Content exceeds the 1 MB limit")

    request_authorization(
        "write_file",
        {
            "path": path,
            "content": content,
        },
    )

    target = resolve_safe_path(path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Revalidate after creating parent directories.
    target = resolve_safe_path(path)

    target.write_text(
        content,
        encoding="utf-8",
    )

    logger.info("File written: %s", target.name)

    return f"Successfully wrote file: {path}"


@mcp.tool()
def list_files(path: str = ".") -> list[str]:
    """List files inside the authorized test directory."""

    request_authorization(
        "list_files",
        {"path": path},
    )

    target = resolve_safe_path(path)

    if not target.is_dir():
        raise NotADirectoryError("Directory not found")

    return sorted(
        item.name
        for item in target.iterdir()
        if item.is_file()
    )


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":

    logger.info("Starting Walled AI MCP Authorization Gateway")
    logger.info("Sandbox directory: %s", ROOT)

    mcp.run(transport="stdio")
