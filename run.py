
#!/usr/bin/env python3

import sys
import os
import time
from pathlib import Path
from threading import Thread

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_monitor import MCPMonitor, FLASK_AVAILABLE
from mcp_monitor.web_interface import create_web_interface


def main():
    print("=" * 60)
    print("Walled AI - MCP Authorization System")
    print("=" * 60)

    claude_config_path = (
        Path.home()
        / "Library"
        / "Application Support"
        / "Claude"
        / "claude_desktop_config.json"
    )

    print(f"[*] Claude config: {claude_config_path}")

    monitor = MCPMonitor(
        config_path=claude_config_path,
        proxy_port=8765,
        web_port=5055
    )

    config = monitor.load_claude_config()

    print("[*] MCP servers:", list(config.get("mcpServers", {}).keys()))

    if not FLASK_AVAILABLE:
        print("[ERROR] Flask is not installed.")
        return

    app = create_web_interface(monitor, port=5055)

    web_thread = Thread(
        target=lambda: app.run(
            host="127.0.0.1",
            port=5055,
            debug=False,
            use_reloader=False,
            threaded=True
        ),
        daemon=True
    )

    monitor.running = True

    monitor_thread = Thread(
        target=monitor.monitor_loop,
        daemon=True
    )

    web_thread.start()
    monitor_thread.start()

    print("[SUCCESS] Dashboard: http://127.0.0.1:5055")
    print("[*] Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        monitor.running = False

        web_thread.join(timeout=2)
        monitor_thread.join(timeout=2)

        print("[*] Application stopped")


if __name__ == "__main__":
    main()
