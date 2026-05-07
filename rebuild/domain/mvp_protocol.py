"""
rebuild.mvp_protocol — MVP (Minimum Viable Protocol) for rebuild communication.

Protocol Specification:
  - JSON-based request/response over HTTP/WebSocket
  - Supports commands, events, and streaming
  - Compatible with DSL and NLP commands

Protocol Message Format:
  {
    "version": "1.0",
    "type": "command|event|response|error",
    "id": "unique-message-id",
    "timestamp": "ISO-8601",
    "payload": { ... }
  }
"""
from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any


class MessageType(Enum):
    """MVP protocol message types."""
    COMMAND = "command"
    EVENT = "event"
    RESPONSE = "response"
    ERROR = "error"
    STREAM = "stream"


@dataclass
class MVPMessage:
    """MVP protocol message."""
    version: str = "1.0"
    message_type: MessageType = MessageType.COMMAND
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "version": self.version,
            "type": self.message_type.value,
            "id": self.message_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
        })

    @classmethod
    def from_json(cls, json_str: str) -> "MVPMessage":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls(
            version=data.get("version", "1.0"),
            message_type=MessageType(data.get("type", "command")),
            message_id=data.get("id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            payload=data.get("payload", {}),
        )


class MVPProtocolHandler:
    """Handler for MVP protocol communication."""

    def __init__(self):
        self._message_handlers = {
            MessageType.COMMAND: self._handle_command,
            MessageType.EVENT: self._handle_event,
        }
        self._command_dispatch: Dict[str, Any] = {
            "walk": self._handle_walk,
            "analyze": self._handle_analyze,
            "evolution": self._handle_evolution,
            "auto_pr": self._handle_auto_pr,
            "dsl": self._handle_dsl,
            "nlp": self._handle_nlp,
        }

    def handle_message(self, message: MVPMessage) -> MVPMessage:
        """Handle an incoming MVP message."""
        # Handle both string and enum message types
        msg_type = message.message_type
        if isinstance(msg_type, str):
            try:
                msg_type = MessageType(msg_type)
            except ValueError:
                msg_type = MessageType.ERROR

        handler = self._message_handlers.get(msg_type)
        if not handler:
            return MVPMessage(
                message_type=MessageType.ERROR,
                payload={"error": f"Unknown message type: {message.message_type}"},
            )
        return handler(message)

    def _handle_command(self, message: MVPMessage) -> MVPMessage:
        """Handle a command message."""
        command = message.payload.get("command")
        params = message.payload.get("parameters", {})

        if not command:
            return MVPMessage(
                message_type=MessageType.ERROR,
                payload={"error": "Missing 'command' in payload"},
            )

        handler = self._command_dispatch.get(command)
        if handler is None:
            return MVPMessage(
                message_type=MessageType.ERROR,
                payload={"error": f"Unknown command: {command}"},
            )
        return handler(params)

    def _handle_event(self, message: MVPMessage) -> MVPMessage:
        """Handle an event message."""
        event_type = message.payload.get("event_type")
        return MVPMessage(
            message_type=MessageType.RESPONSE,
            payload={"status": "event_received", "event_type": event_type},
        )

    def _handle_walk(self, params: Dict[str, Any]) -> MVPMessage:
        """Handle walk command."""
        return MVPMessage(
            message_type=MessageType.RESPONSE,
            payload={
                "command": "walk",
                "parameters": params,
                "status": "parsed",
            },
        )

    def _handle_analyze(self, params: Dict[str, Any]) -> MVPMessage:
        """Handle analyze command."""
        return MVPMessage(
            message_type=MessageType.RESPONSE,
            payload={
                "command": "analyze",
                "parameters": params,
                "status": "parsed",
            },
        )

    def _handle_evolution(self, params: Dict[str, Any]) -> MVPMessage:
        """Handle evolution command."""
        return MVPMessage(
            message_type=MessageType.RESPONSE,
            payload={
                "command": "evolution",
                "parameters": params,
                "status": "parsed",
            },
        )

    def _handle_auto_pr(self, params: Dict[str, Any]) -> MVPMessage:
        """Handle auto-pr command."""
        return MVPMessage(
            message_type=MessageType.RESPONSE,
            payload={
                "command": "auto_pr",
                "parameters": params,
                "status": "parsed",
            },
        )

    def _handle_dsl(self, params: Dict[str, Any]) -> MVPMessage:
        """Handle DSL command."""
        from ..domain.dsl import DSLParser, DSLInterpreter

        dsl_string = params.get("dsl")
        if not dsl_string:
            return MVPMessage(
                message_type=MessageType.ERROR,
                payload={"error": "Missing 'dsl' parameter"},
            )

        try:
            parser = DSLParser()
            interpreter = DSLInterpreter()
            cmd = parser.parse(dsl_string)
            result = interpreter.execute(cmd)
            return MVPMessage(
                message_type=MessageType.RESPONSE,
                payload={
                    "command": "dsl",
                    "dsl": dsl_string,
                    "result": result,
                    "status": "executed",
                },
            )
        except Exception as e:
            return MVPMessage(
                message_type=MessageType.ERROR,
                payload={"error": str(e)},
            )

    def _handle_nlp(self, params: Dict[str, Any]) -> MVPMessage:
        """Handle NLP command."""
        from ..application.services.nlp_service import NLPService

        text = params.get("text")
        if not text:
            return MVPMessage(
                message_type=MessageType.ERROR,
                payload={"error": "Missing 'text' parameter"},
            )

        try:
            nlp = NLPService()
            cmd = nlp.parse(text)
            dsl = nlp.to_dsl(cmd)
            return MVPMessage(
                message_type=MessageType.RESPONSE,
                payload={
                    "command": "nlp",
                    "text": text,
                    "intent": cmd.intent.value,
                    "parameters": cmd.parameters,
                    "confidence": cmd.confidence,
                    "dsl": dsl,
                    "status": "parsed",
                },
            )
        except Exception as e:
            return MVPMessage(
                message_type=MessageType.ERROR,
                payload={"error": str(e)},
            )


class MVPServer:
    """MVP protocol server for handling incoming connections."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8899):
        self.host = host
        self.port = port
        self.handler = MVPProtocolHandler()

    def start(self) -> None:
        """Start the MVP server."""
        import http.server
        import socketserver

        class MVPRequestHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")

                try:
                    message = MVPMessage.from_json(body)
                    response = server.handler.handle_message(message)

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(response.to_json().encode())
                except Exception as e:
                    error_msg = MVPMessage(
                        message_type=MessageType.ERROR,
                        payload={"error": str(e)},
                    )
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(error_msg.to_json().encode())

            def log_message(self, format, *args):
                pass  # Suppress logging

        server = self
        with socketserver.TCPServer((self.host, self.port), MVPRequestHandler) as httpd:
            print(f"MVP Server running on http://{self.host}:{self.port}")
            httpd.serve_forever()
