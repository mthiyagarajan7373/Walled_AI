
#!/usr/bin/env python3

from gateway import mcp
from mcp.server.transport_security import TransportSecuritySettings

if __name__ == "__main__":
    print("Starting Walled AI HTTP MCP Server")
    print("MCP endpoint: http://127.0.0.1:8000/mcp")

    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8000
    mcp.settings.streamable_http_path = "/mcp"

    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "old-vienna-graphs-under.trycloudflare.com",
            "old-vienna-graphs-under.trycloudflare.com:443",
            "shakespeare-specials-perform-meat.trycloudflare.com",
            "shakespeare-specials-perform-meat.trycloudflare.com:443",
            "127.0.0.1:8000",
            "localhost:8000",
        ],
        allowed_origins=[
            "https://apollo-tape-monsters-conviction.trycloudflare.com",
        ],
    )

    mcp.run(transport="streamable-http")

