# AI Process Recovery Agent – LangGraph – Human-in-the-Loop

A production-grade, end-to-end **Autonomous Business Workflow Recovery System** powered by **LangGraph Agentic AI**, **FastAPI**, **SQLAlchemy**, and a high-tech **Cyber Obsidian Mission Control Interface**.

---

## 🌟 Key Highlights

- **Autonomous Agentic Self-Healing**: Monitors business workflows in real-time, intercepts step failures, executes structured Root-Cause Analysis (RCA), selects safe predefined recovery tools, requests human approvals when needed, verifies API state changes, and resumes workflows to completion.
- **Strict Light 3D Aesthetic**: Designed with an ultra-premium, modern light palette (soft lavender, mint, pastel coral, light cyan, peach) featuring layered glassmorphism, 3D shadows, isometric workflow maps, and a reactive AI Orb. **Zero dark theme or deep blue elements.**
- **Real-Time Streaming**: Integrated Server-Sent Events (SSE) `/api/events` with automatic polling fallback ensures zero-latency visual reactivity across all 8 operational views.
- **Zero-Key Deterministic Fallback**: Built-in deterministic structured reasoning heuristic engine ensures 100% out-of-the-box functionality offline without requiring OpenAI, Anthropic, or Gemini API keys (while seamlessly supporting them via `.env`).
- **Chaos Engineering & Fault Injection Studio**: Live control center to simulate payment timeouts, warehouse stock depletion, HTTP 503 service outages, and logistics carrier disconnects with real-time AI remediation.

---

## 🏗️ Architecture Overview

```
                                  ┌────────────────────────┐
                                  │   Light 3D SaaS UI     │
                                  │ (8 Visual Views + Orb) │
                                  └───────────┬────────────┘
                                              │ REST / SSE
                                              ▼
                                  ┌────────────────────────┐
                                  │    FastAPI Backend     │
                                  └───────────┬────────────┘
                                              │
                   ┌──────────────────────────┼──────────────────────────┐
                   ▼                          ▼                          ▼
          ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
          │  Workflow State │       │   LangGraph AI  │       │ Chaos Simulator │
          │     Machine     │       │  Recovery Graph │       │ & Business APIs │
          └────────┬────────┘       └────────┬────────┘       └────────┬────────┘
                   │                         │                         │
                   └─────────────────────────┼─────────────────────────┘
                                             │
                                             ▼
                                  ┌────────────────────┐
                                  │ SQLite / SQL DB    │
                                  │ Workflows, Steps,  │
                                  │ Failures, Actions, │
                                  │ Approvals, Audits  │
                                  └────────────────────┘
```

---

## 🔄 LangGraph State Graph Workflow

```
[START]
   │
   ▼
[MONITOR_WORKFLOW]
   │
   ▼
[DETECT_FAILURE] ── (Logs Audit: FAILURE_DETECTED)
   │
   ▼
[ANALYZE_FAILURE] ── (Structured LLM / Heuristic Root Cause Analysis)
   │
   ▼
[CREATE_RECOVERY_PLAN] ── (Generates Discrete Remediation Steps & Selects Tool)
   │
   ▼
[CHECK_APPROVAL_REQUIRED]
   │
   ├─► (Approval Required & PENDING) ──► [WAIT_FOR_HUMAN_APPROVAL]
   │                                              │
   │                                     (Operator Approves)
   │                                              │
   ▼                                              ▼
[EXECUTE_ACTION] ◄────────────────────────────────┘
   │
   ▼
[VERIFY_RECOVERY]
   │
   ├─► (Verified OK) ──► [WORKFLOW_COMPLETED] ──► [END]
   │
   └─► (Failed Verification & Retries Left) ──► [ANALYZE_FAILURE] (Re-plan Loop)
```

---

## 📂 Project Structure

```
ai-process-recovery-agent/
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI server, CORS, lifespan, SSE broadcaster
│   ├── config.py                # Pydantic settings & environment configuration
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                # SQLAlchemy engine & session factory
│   │   ├── models.py            # Workflow, Step, Failure, RecoveryAction, Approval, AuditLog, ServiceMetric
│   │   └── seed.py              # Pre-populates 10 realistic workflows across diverse states
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic validation schemas
│   ├── business_apis/           # Simulated external microservices with fault injection
│   │   ├── __init__.py
│   │   ├── state.py             # Products catalog, carriers, and active chaos flags
│   │   ├── payment_service.py   # /api/business/payment/process (timeout, declined, 503)
│   │   ├── inventory_service.py # /api/business/inventory/{id} (live stock & alternatives)
│   │   ├── order_service.py     # /api/business/orders (create, modify, replace item)
│   │   ├── delivery_service.py  # /api/business/delivery/schedule (FedEx, UPS switch)
│   │   └── notification_service.py # /api/business/notification/send
│   ├── workflow_engine/
│   │   ├── __init__.py
│   │   └── engine.py            # Core 5-step state machine & recovery coordinator
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── state.py             # LangGraph RecoveryState TypedDict
│   │   ├── tools.py             # 12 controlled deterministic tools
│   │   ├── llm.py               # Flexible LLM provider + smart heuristic fallback engine
│   │   ├── nodes.py             # LangGraph node implementations
│   │   └── graph.py             # Compiled StateGraph & conditional routing
│   └── routes/
│       ├── __init__.py
│       ├── workflows.py         # Workflow CRUD, stats, and timeline
│       ├── approvals.py         # Human-in-the-loop approve/reject endpoints
│       ├── failures.py          # Failure logs and recovery actions viewer
│       ├── audit_logs.py        # Chronological audit timeline query
│       ├── services.py          # Microservices health & Chaos Fault Injector
│       ├── demo.py              # 5 Executable Demo Scenarios
│       ├── settings.py          # Engine parameters & LLM configuration
│       └── events.py            # Real-time SSE streaming router
├── frontend/
│   ├── index.html               # 3D SaaS Single Page Application Shell
│   ├── css/
│   │   ├── design-system.css    # Pastel palette, glassmorphism tokens, shadows
│   │   ├── layout.css           # 3D spatial grids, sidebar, topbar
│   │   ├── components.css       # Floating 3D cards, pastel action buttons, workflow nodes
│   │   └── animations.css       # Keyframes: orb float, energy route pulse, node glow
│   └── js/
│       ├── api.js               # REST client & Server-Sent Events subscriber
│       ├── store.js             # Reactive central state store
│       ├── components/
│       │   ├── aiOrb.js         # Reactive 3D AI Agent Orb
│       │   ├── workflowMap.js   # 3D Interactive Live Workflow Map
│       │   ├── workflowTimeline.js # 3D Branched Recovery Timeline
│       │   └── healthRing.js    # 3D Segmented SVG Health Ring
│       ├── pages/
│       │   ├── dashboard.js     # Page 1: Command Center Dashboard
│       │   ├── workflows.js     # Page 2: Workflow Explorer
│       │   ├── workflowDetail.js# Page 3: 3D Workflow Timeline Inspector
│       │   ├── failures.js      # Page 4: Failure & Recovery Center
│       │   ├── approvals.js     # Page 5: Human-in-the-Loop Approval Center
│       │   ├── audit.js         # Page 6: Audit Logs Timeline
│       │   ├── services.js      # Page 7: Business Services & Chaos Studio
│       │   └── settings.js      # Page 8: Settings & Engine Configuration
│       └── app.js               # Router, notifications, and demo launcher
├── tests/
│   ├── test_business_apis.py    # Business microservices & fault tests
│   ├── test_workflow_engine.py  # Lifecycle & state progression tests
│   ├── test_agent_graph.py      # LangGraph nodes, tools, and recovery tests
│   └── test_api_routes.py       # FastAPI integration tests
├── .env.example
├── requirements.txt
├── run.py                       # Single-command startup runner
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Modern Web Browser (Chrome, Edge, Firefox, Safari)

### 2. Installation
```bash
# Clone or navigate to the project directory
cd ai-process-recovery-agent

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch Application
```bash
python run.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser!

---

## ⚡ Interactive Demo Scenarios

You can run any of the 5 pre-packaged end-to-end recovery scenarios directly from the topbar demo selector:

1. **Demo 1 — Inventory Out of Stock & Approval Gate** (`inventory_out_of_stock`):
   - Initial product `Zenith ProBook 15` has 0 stock.
   - Payment succeeds -> Inventory check fails.
   - AI agent diagnoses root cause, recommends identical-cost upgrade edition `Zenith ProBook 15 Plus (1TB SSD)`.
   - Routes request to **Approval Center**. Operator clicks **APPROVE RECOVERY**.
   - Agent modifies order, audits warehouse allocation, completes confirmation, and schedules carrier delivery.
2. **Demo 2 — Payment Timeout Recovery** (`payment_timeout`):
   - Payment gateway times out after 4000ms.
   - AI intercepts failure, executes secondary gateway retry, verifies fund settlement, and completes order.
3. **Demo 3 — Inventory 503 Outage & Backoff** (`inventory_service_down`):
   - Warehouse API cluster returns HTTP 503.
   - AI triggers exponential backoff self-healing cycle, restores connection, and completes order.
4. **Demo 4 — Logistics Carrier Switchover** (`delivery_failed`):
   - FedEx dispatch gateway offline.
   - AI automatically switches parcel booking to partner carrier `UPS Next Day`, acquires tracking manifest, and completes shipment.
5. **Demo 5 — High Value Review** (`high_value_recovery`):
   - $2,499.99 transaction triggers policy-mandated manual sign-off requirement for Senior Operations Director.

---

## 🧪 Running Automated Tests

```bash
python -m pytest -v tests/
```

---

## 🛡️ License
MIT License. Built for Autonomous AI Agent Research.
