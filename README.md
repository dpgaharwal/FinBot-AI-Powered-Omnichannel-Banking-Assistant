# FinBot — AI-Powered Omnichannel Banking Assistant

A production-grade AI banking assistant built with LangGraph multi-agent architecture, MCP-MySQL live data retrieval, RAG on banking policies, Razorpay EMI payments, RabbitMQ event-driven notifications, and omnichannel support (WhatsApp + Web).

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CHANNEL LAYER                        │
│         WhatsApp (Twilio)  +  Web Chat (WebSocket)      │
│     Multi-device login · Typing indicators · Presence   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 ORCHESTRATION LAYER                      │
│                  LangGraph Graph                         │
│                                                         │
│         Memory Node (short-term + long-term)            │
│                      ↓                                  │
│                  Router Node                            │
│                    ├── Balance/Txn Agent                │
│                    ├── Policy Agent (RAG)               │
│                    ├── Dispute/Refund Agent             │
│                    ├── Payment Agent (Razorpay)         │
│                    └── Human Handoff Node               │
└──────┬──────────────────────┬──────────────────────────┘
       │                      │
┌──────▼──────┐      ┌────────▼────────┐
│  DATA LAYER │      │  PAYMENTS LAYER │
│             │      │                 │
│ MySQL (MCP) │      │ Razorpay EMI    │
│ Qdrant RAG  │      │                 │
│ HF Embeddings│     │ RabbitMQ Events │
└─────────────┘      │ EMI Paid →      │
                     │ Notification    │
                     └─────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────┐
│              OBSERVABILITY + SAFETY LAYER                │
│                                                         │
│  LangSmith Tracing   ·   Audit Logs (MySQL)             │
│  PII Guardrails      ·   Prompt Injection Detection     │
│  Rate Limiting       ·   RBI/PCI-DSS Aligned            │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python + FastAPI | Async REST + WebSocket server |
| Real-time | WebSocket (WSS/TLS) | Live chat, streaming, presence |
| Orchestration | LangGraph 0.2.28 | Multi-agent routing + shared state |
| LLM | Ollama (llama3) | Local LLM, zero API cost |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | Local embeddings, zero API cost |
| Vector DB | Qdrant | RAG document storage + retrieval |
| Live Data | MySQL + MCP Server | LLM queries DB via MCP protocol |
| Payments | Razorpay (EMI/installments) | Real payment order creation |
| Events | RabbitMQ (aio-pika) | Async event publishing + consuming |
| Channels | Twilio WhatsApp + WebSocket | Omnichannel messaging |
| Auth | JWT (python-jose) | Secure endpoint access |
| Observability | LangSmith | LLM traces + latency |
| Safety | Custom guardrails | PII masking + injection blocking |
| Rate Limiting | slowapi | Request throttling |
| Deploy | Docker + docker-compose | One-command full stack |

---

## Agents

| Agent | Intent Trigger | Data Source | What it does |
|---|---|---|---|
| Memory Node | Every message | LangGraph checkpointer | Short + long term memory |
| Router | Every message | LLM classification | Classifies intent, routes to agent |
| Balance/Txn | balance, transactions | MCP-MySQL | Fetches live account + txn data |
| Policy | policy | Qdrant RAG | Semantic search on bank policies |
| Dispute/Refund | dispute | MCP + RAG | Live txns + refund policies combined |
| Payment | loan, EMI | Razorpay + MySQL | Creates order, records payment |
| Human Handoff | handoff | MySQL audit_logs | Creates ticket, escalates to human |

---

## Memory Architecture

```
Short-term Memory
    └── LangGraph Checkpointer
        └── Stores current session messages
        └── Context carries across turns in same session

Long-term Memory
    └── Conversation Summaries (LLM-generated)
        └── Triggered after 6+ messages
        └── Summarizes resolved topics
        └── Injected as system context in next turns
```

---

## Event-Driven Flow

```
User: "I want to pay my EMI"
         │
         ▼
  LangGraph Router (intent: loan)
         │
         ▼
  Payment Agent
    ├── get_loan_details() → MySQL
    ├── create_emi_order() → Razorpay API
    ├── record_emi_payment() → MySQL txn + loan update
    └── publish_emi_paid_event() → RabbitMQ emi.paid queue
         │
         ▼
  Background Consumer Thread
    └── handle_emi_notification()
        └── send_whatsapp_message() → Twilio → Customer WhatsApp
```

---

## Security & Compliance

| Feature | Implementation |
|---|---|
| Authentication | JWT tokens, 60-min expiry |
| PII Masking | Account numbers, PAN, CVV, phone masked in output |
| Prompt Injection | Pattern detection, request blocked + audit logged |
| Rate Limiting | slowapi, per IP |
| Audit Trail | Every action logged: timestamp, user, action, outcome |
| Compliance | RBI/PCI-DSS aligned framing |
| Transport | WSS/TLS encrypted WebSocket |

---

## Database Schema

```sql
customers     — id, name, email, phone, kyc_status
accounts      — id, customer_id, account_number, type, balance, status
transactions  — id, account_id, type, amount, description, status
loans         — id, customer_id, loan_type, principal, emi_amount, remaining_emis
audit_logs    — id, user_id, action, details, outcome, created_at
```

---

## Eval Results

| Metric | Score |
|---|---|
| Routing Accuracy | 100% (10/10 test cases) |
| RAG Retrieval | Cosine similarity > 0.6 on relevant queries |
| Payment Flow | End-to-end Razorpay + MySQL + RabbitMQ verified |

---

## Quick Start

### Prerequisites
- Docker + docker-compose
- Ollama installed with llama3 (`ollama pull llama3`)
- Python 3.11+
- Twilio account (WhatsApp sandbox)
- Razorpay test account

### 1. Clone

```bash
git clone https://github.com/dpgaharwal/FinBot-AI-Powered-Omnichannel-Banking-Assistant.git
cd FinBot-AI-Powered-Omnichannel-Banking-Assistant
```

### 2. Environment Setup

```bash
cp .env.example .env
```

Fill in `.env`:

```env
# App
APP_SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# LangSmith
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=finbot
LANGCHAIN_TRACING_V2=true

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=finbot
MYSQL_USER=finbot_user
MYSQL_PASSWORD=finbot123

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=finbot_docs

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Razorpay
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

### 3. Start Infrastructure

```bash
docker-compose up -d
```

### 4. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Embed Policies

```bash
python3 data/ingest.py
```

### 6. Start Server

```bash
uvicorn app.main:app --reload
```

### 7. Test

```bash
# Get token
curl -X POST http://localhost:8000/api/v1/token

# WebSocket test
python3 -c "
import websocket
token = 'YOUR_TOKEN'
ws = websocket.create_connection(f'ws://localhost:8000/api/v1/ws/chat?token={token}')
ws.send('What is my account balance?')
while True:
    msg = ws.recv()
    print(msg)
    if msg == '[END]':
        break
ws.close()
"
```

---

## Run Evals

```bash
python3 tests/eval.py
```

Expected output:
```
Routing Accuracy: 10/10 = 100.0%
```

---

## Services

| Service | URL |
|---|---|
| FinBot API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| RabbitMQ Dashboard | http://localhost:15672 (guest/guest) |
| Qdrant Dashboard | http://localhost:6333/dashboard |

---

## Project Structure

```
finbot/
├── app/
│   ├── agents/
│   │   ├── graph.py          # LangGraph wiring
│   │   ├── state.py          # FinBotState TypedDict
│   │   ├── router.py         # Intent classifier
│   │   ├── balance_agent.py  # MCP-MySQL balance/txn
│   │   ├── policy_agent.py   # RAG policy answers
│   │   ├── dispute_agent.py  # MCP + RAG dispute
│   │   ├── payment_agent.py  # Razorpay EMI
│   │   ├── handoff_agent.py  # Human escalation
│   │   └── memory.py         # Short + long term memory
│   ├── routes/
│   │   ├── chat.py           # WebSocket endpoint
│   │   └── whatsapp.py       # Twilio webhook
│   ├── services/
│   │   ├── mcp_server.py     # MySQL MCP tool registry
│   │   ├── rag.py            # Qdrant RAG pipeline
│   │   ├── payment.py        # Razorpay integration
│   │   ├── events.py         # RabbitMQ publish/consume
│   │   ├── whatsapp.py       # Twilio messaging
│   │   ├── audit.py          # Audit log service
│   │   └── guardrails.py     # PII + injection safety
│   ├── middleware/
│   │   ├── auth.py           # JWT create/verify
│   │   └── rate_limit.py     # slowapi limiter
│   └── core/
│       └── config.py         # Pydantic settings
├── data/
│   ├── bank_policies.py      # 15 bank policy documents
│   └── ingest.py             # Embed policies into Qdrant
├── database/
│   ├── schema.sql            # MySQL schema
│   └── seed.sql              # Mock data
├── tests/
│   └── eval.py               # Routing accuracy eval
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---