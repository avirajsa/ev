# EV — Omnipresent AI Assistant Cloud Backend

EV (inspired by E.D.I.T.H / F.R.I.D.A.Y / J.A.R.V.I.S) is a central AI Assistant Cloud Backend capable of persistent memory, Model Context Protocol (MCP) integrations, OpenRouter dynamic LLM fallback, and real-time remote orchestration of distributed client devices (Laptops, Mobile Phones, IoT microcontrollers).

---

## Architecture Overview

```
                          ┌────────────────────────┐
                          │   Client Ecosystem     │
                          └──────────┬─────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │ (Voice / STT Streaming)   │ (Secure WSS RPC)          │ (Telemetry/Sensors)
         ▼                           ▼                           ▼
  ┌──────────────┐           ┌──────────────┐            ┌──────────────┐
  │ Mobile App   │           │ Laptop App   │            │ IoT / Embed  │
  └──────┬───────┘           └──────┬───────┘            └──────┬───────┘
         │                          │                           │
 WSS + JWT Auth             WSS RPC + Auth Token       WSS / MQTT + Key
         │                          │                           │
 ┌───────┴──────────────────────────┴───────────────────────────┴────────┐
 │                   EV CLOUD GATEWAY & AUTH ROUTER                     │
 └──────────────────────────────────┬────────────────────────────────────┘
                                    │
 ┌──────────────────────────────────┴────────────────────────────────────┐
 │                            EV AGENT CORE                              │
 │                                                                       │
 │  ┌───────────────────┐    ┌───────────────────┐   ┌────────────────┐ │
 │  │ LLM Orchestrator  │───►│ MCP Tool Client   │───│ External Tools │ │
 │  └─────────┬─────────┘    └───────────────────┘   └────────────────┘ │
 │            │                                                          │
 │            ▼                                                          │
 │  ┌───────────────────┐    ┌───────────────────┐                       │
 │  │ Task Dispatcher   │───►│ Device Registry   │                       │
 │  │ (Remote OS Exec)  │    │ & Node Router     │                       │
 │  └───────────────────┘    └───────────────────┘                       │
 └──────────────────────────────────┬────────────────────────────────────┘
                                    │
 ┌──────────────────────────────────┴────────────────────────────────────┐
 │                           MEMORY & DATABASE                           │
 │                                                                       │
 │  ┌───────────────────┐    ┌───────────────────┐   ┌────────────────┐ │
 │  │  Relational DB    │    │  Vector Database  │   │  Redis Cache/  │ │
 │  │  (Users, Devices) │    │ (Semantic Memory) │   │  PubSub State  │ │
 │  └───────────────────┘    └───────────────────┘   └────────────────┘ │
 └───────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Zero-Friction Setup with `uv` & `make`

[Astral `uv`](https://github.com/astral-sh/uv) is used for ultra-fast, reproducible dependency management and execution.

### 1. Prerequisites
Install `uv` (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Configure Environment
Copy `.env.example` to `.env` and set your OpenRouter API Key:
```bash
cp .env.example .env
```

### 3. Quick Start Commands (via `Makefile`)

| Command | Action |
| :--- | :--- |
| **`make install`** | Create virtual environment and install all dependencies via `uv` |
| **`make dev`** | Run development server at `http://localhost:8000` with auto-reload |
| **`make test`** | Run pytest suite (`uv run pytest`) |
| **`make docker-up`** | Launch full Docker Compose stack (FastAPI + PostgreSQL + Redis) |
| **`make docker-down`**| Stop Docker Compose stack |
| **`make clean`** | Clear cache files (`__pycache__`, `.pytest_cache`, `.venv`) |

Visit `http://localhost:8000/docs` to view interactive OpenAPI Swagger docs.

---

## 🐳 One-Command Docker Deployment (Production)

Deploy the entire EV stack (FastAPI backend + PostgreSQL pgvector + Redis) frictionlessly using Docker:

### 1. Build and Launch Stack
```bash
docker compose up -d --build
```

### 2. Verify Container Status & Logs
```bash
# View active container status
docker compose ps

# Stream backend logs
docker compose logs -f ev-backend
```

---

## 🚀 GitHub Actions CI/CD Pipeline

Continuous Integration is configured in `.github/workflows/ci.yml`:
- **Automated Testing**: Triggers on `push` and `pull_request` to `main`/`master`.
- **Environment Setup**: Uses `astral-sh/setup-uv` for fast dependency caching and Python 3.12 execution.
- **Docker Validation**: Verifies production multi-stage `Dockerfile` build integrity via `docker/build-push-action`.

---

## 🔑 LLM OpenRouter Auto-Fallback Configuration

EV uses `app/core/llm_router.py` to route traffic through OpenRouter with automatic failover across models:

In your `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
PRIMARY_MODEL=anthropic/claude-3.5-sonnet
FALLBACK_MODELS=["openai/gpt-4o","google/gemini-2.0-flash-001","meta-llama/llama-3.3-70b-instruct"]
```

**How Failover Works**:
If a request encounters a Rate Limit (429), Insufficient Quota/Tokens (400/402), or Provider Error (5xx), EV automatically retries with the next model in `FALLBACK_MODELS` without interrupting the conversation or dropping payload context.

---

## 🔌 Connecting Client Devices (Laptop & Mobile Apps)

Client applications connect over WebSockets at `/ws/connect`:

```text
ws://<YOUR_SERVER_HOST>:8000/ws/connect?token=ev_device_shared_secret_token_12345&device_id=laptop-macbook-1&device_name=MacBook-Pro&device_type=laptop&capabilities=["gui","terminal"]
```

### Example WebSocket Client Registration (Python)
```python
import websockets
import asyncio
import json

async def connect_laptop_node():
    url = "ws://localhost:8000/ws/connect?token=ev_device_shared_secret_token_12345&device_id=my-laptop&device_name=MacBook&device_type=laptop&capabilities=[\"gui\",\"terminal\"]"
    async with websockets.connect(url) as ws:
        ack = await ws.recv()
        print("Connected to EV Cloud Backend:", ack)
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get("type") == "rpc_request":
                request_id = data["request_id"]
                action = data["action"]
                # Perform remote action (e.g. open app, run script)
                response = {
                    "type": "rpc_response",
                    "request_id": request_id,
                    "status": "success",
                    "result": {"output": f"Executed action: {action}"}
                }
                await ws.send(json.dumps(response))

asyncio.run(connect_laptop_node())
```
