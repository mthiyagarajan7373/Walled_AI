
"""Thread-safe MCP authorization request manager."""

import json
import logging
import threading
import time
import uuid

from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


try:
    from flask import Flask
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


logger = logging.getLogger("mcp_monitor")


class RequestStatus(Enum):
    PENDING = "pending"
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"


@dataclass
class MCPRequest:
    id: str
    timestamp: float
    server: str
    tool: str
    parameters: Dict[str, Any]
    request_type: str
    status: RequestStatus = RequestStatus.PENDING
    user_decision: Optional[str] = None
    claude_instance: Optional[str] = "claude_desktop"


class MCPMonitor:

    def __init__(
        self,
        config_path=None,
        proxy_port=8765,
        web_port=5000,
        authorization_timeout=300,
        max_history=1000,
    ):
        self.config_path = Path(config_path) if config_path else None
        self.proxy_port = proxy_port
        self.web_port = web_port
        self.authorization_timeout = authorization_timeout
        self.max_history = max_history

        self.requests = OrderedDict()
        self.events = {}

        self.lock = threading.RLock()
        self.running = False
        self.shutdown_event = threading.Event()

    def load_claude_config(self):
        """Load Claude Desktop configuration without modifying it."""

        if not self.config_path or not self.config_path.exists():
            logger.warning("Claude configuration not found")
            return {"mcpServers": {}}

        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                config = json.load(file)

            if not isinstance(config, dict):
                raise ValueError("Configuration must be a JSON object")

            servers = config.get("mcpServers", {})

            if not isinstance(servers, dict):
                raise ValueError("mcpServers must be an object")

            return config

        except (OSError, json.JSONDecodeError, ValueError):
            logger.exception("Unable to load Claude configuration")
            raise

    def create_request(self, data):
        if not isinstance(data, dict):
            raise ValueError("Request must be a dictionary")

        arguments = data.get("arguments", {})

        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be an object")

        request_id = str(uuid.uuid4())

        req = MCPRequest(
            id=request_id,
            timestamp=time.time(),
            server=str(data.get("server", "unknown")),
            tool=str(data.get("tool", "unknown")),
            parameters=arguments.copy(),
            request_type=str(data.get("request_type", "tool_call")),
        )

        with self.lock:
            if self.shutdown_event.is_set():
                raise RuntimeError("Authorization monitor is shutting down")

            self.requests[request_id] = req
            self.events[request_id] = threading.Event()

            self._cleanup_history()

        logger.info(
            "New MCP request: server=%s tool=%s id=%s",
            req.server,
            req.tool,
            req.id,
        )

        return req

    def _cleanup_history(self):
        """Remove oldest completed requests while retaining pending ones."""

        while len(self.requests) > self.max_history:
            removable = next(
                (
                    key for key, value in self.requests.items()
                    if value.status != RequestStatus.PENDING
                    and key not in self.events
                ),
                None,
            )

            if removable is None:
                break

            self.requests.pop(removable, None)

    def wait_for_decision(self, data, timeout=None):
        req = self.create_request(data)

        timeout = (
            self.authorization_timeout if timeout is None else timeout
        )

        with self.lock:
            event = self.events[req.id]

        completed = event.wait(timeout=max(0, timeout))

        with self.lock:
            if not completed and req.status == RequestStatus.PENDING:
                req.status = RequestStatus.TIMEOUT
                req.user_decision = "timeout"

            result = (
                "allow"
                if req.status == RequestStatus.ALLOWED
                else "block"
            )

            self.events.pop(req.id, None)
            self._cleanup_history()

        logger.info(
            "Authorization completed: id=%s decision=%s",
            req.id,
            result,
        )

        return result

    def handle_decision(self, request_id, decision):
        if decision not in ("allow", "block"):
            return False

        with self.lock:
            req = self.requests.get(request_id)

            if req is None or req.status != RequestStatus.PENDING:
                return False

            if self.shutdown_event.is_set():
                return False

            req.user_decision = decision

            req.status = (
                RequestStatus.ALLOWED
                if decision == "allow"
                else RequestStatus.BLOCKED
            )

            event = self.events.get(request_id)

            if event:
                event.set()

            logger.info(
                "User decision: id=%s decision=%s",
                request_id,
                decision,
            )

            return True

    def get_requests(self):
        with self.lock:
            return dict(self.requests)

    def shutdown(self):
        """Fail closed and wake all waiting authorization requests."""

        self.shutdown_event.set()

        with self.lock:
            self.running = False

            for request_id, req in self.requests.items():
                if req.status == RequestStatus.PENDING:
                    req.status = RequestStatus.BLOCKED
                    req.user_decision = "shutdown"

                event = self.events.get(request_id)

                if event:
                    event.set()

        logger.info("MCP monitor shutdown completed")

    def monitor_loop(self):
        while (
            self.running
            and not self.shutdown_event.is_set()
        ):
            self.shutdown_event.wait(1)
