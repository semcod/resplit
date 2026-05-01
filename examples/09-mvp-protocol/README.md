# MVP (Minimum Viable Protocol) Examples

This directory contains examples of using the Rebuild MVP protocol for programmatic communication with the rebuild system.

## Starting the MVP Server

### Start MVP server on default port (8899):
```bash
python3 -m rebuild mvp
```

### Start MVP server on custom port:
```bash
python3 -m rebuild mvp --host 0.0.0.0 --port 9000
```

## Protocol Specification

### Message Format
```json
{
  "version": "1.0",
  "type": "command|event|response|error",
  "id": "unique-message-id",
  "timestamp": "ISO-8601",
  "payload": { ... }
}
```

### Message Types
- `command`: Execute a rebuild command
- `event`: Publish an event (for streaming)
- `response`: Response to a command
- `error`: Error message
- `stream`: Streaming data

## Supported Commands

### DSL Command
Execute a DSL string via MVP protocol:

```json
{
  "version": "1.0",
  "type": "command",
  "id": "msg-001",
  "timestamp": "2026-05-01T19:00:00Z",
  "payload": {
    "command": "dsl",
    "parameters": {
      "dsl": "walk repo:/home/tom/github/maskservice/c2004 days:1"
    }
  }
}
```

### NLP Command
Parse natural language via MVP protocol:

```json
{
  "version": "1.0",
  "type": "command",
  "id": "msg-002",
  "timestamp": "2026-05-01T19:00:00Z",
  "payload": {
    "command": "nlp",
    "parameters": {
      "text": "analyze code for duplicates"
    }
  }
}
```

### Walk Command
Direct walk command:

```json
{
  "version": "1.0",
  "type": "command",
  "id": "msg-003",
  "timestamp": "2026-05-01T19:00:00Z",
  "payload": {
    "command": "walk",
    "parameters": {
      "repo": "/home/tom/github/maskservice/c2004",
      "days": 7,
      "deploy": "docker-compose"
    }
  }
}
```

## Example: Using curl

### Send DSL command:
```bash
curl -X POST http://localhost:8899 \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0",
    "type": "command",
    "id": "msg-001",
    "timestamp": "2026-05-01T19:00:00Z",
    "payload": {
      "command": "dsl",
      "parameters": {
        "dsl": "walk repo:/home/tom/github/maskservice/c2004 days:1"
      }
    }
  }'
```

### Send NLP command:
```bash
curl -X POST http://localhost:8899 \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0",
    "type": "command",
    "id": "msg-002",
    "timestamp": "2026-05-01T19:00:00Z",
    "payload": {
      "command": "nlp",
      "parameters": {
        "text": "analyze code for duplicates"
      }
    }
  }'
```

## Example: Python Client

```python
import json
import requests

MVP_SERVER = "http://localhost:8899"

def send_mvp_command(command, parameters):
    """Send a command to the MVP server."""
    import uuid
    from datetime import datetime

    message = {
        "version": "1.0",
        "type": "command",
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "command": command,
            "parameters": parameters
        }
    }

    response = requests.post(MVP_SERVER, json=message)
    return response.json()

# Example: Execute DSL
result = send_mvp_command("dsl", {"dsl": "walk repo:/home/tom/github/maskservice/c2004 days:1"})
print(result)

# Example: Parse NLP
result = send_mvp_command("nlp", {"text": "analyze code for duplicates"})
print(result)
```

## Example: JavaScript Client

```javascript
const MVP_SERVER = "http://localhost:8899";

async function sendMVPCommand(command, parameters) {
  const message = {
    version: "1.0",
    type: "command",
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    payload: {
      command: command,
      parameters: parameters
    }
  };

  const response = await fetch(MVP_SERVER, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(message)
  });

  return await response.json();
}

// Example: Execute DSL
sendMVPCommand("dsl", { dsl: "walk repo:/home/tom/github/maskservice/c2004 days:1" })
  .then(result => console.log(result));

// Example: Parse NLP
sendMVPCommand("nlp", { text: "analyze code for duplicates" })
  .then(result => console.log(result));
```

## Response Format

### Success Response
```json
{
  "version": "1.0",
  "type": "response",
  "id": "msg-001",
  "timestamp": "2026-05-01T19:00:01Z",
  "payload": {
    "status": "executed",
    "result": { ... }
  }
}
```

### Error Response
```json
{
  "version": "1.0",
  "type": "error",
  "id": "msg-001",
  "timestamp": "2026-05-01T19:00:01Z",
  "payload": {
    "error": "Error message"
  }
}
```

## Use Cases

1. **Remote Control**: Control rebuild from external applications
2. **Integration**: Integrate with CI/CD pipelines
3. **Web UI**: Build custom web interfaces
4. **Automation**: Schedule automated analysis jobs
5. **Multi-language Clients**: Use from any language with HTTP support
