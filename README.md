# SmartBuy Node: Automated B2B Procurement & Compliance Agent

**Track:** Agents for Business

## Executive Summary & Problem Statement

In contemporary enterprise landscapes, procurement operations represent a massive friction point within corporate agility and the development lifecycle. Procurement departments waste hundreds of hours manually processing unstructured product requests from managers, manually auditing decentralized departmental budgets, verifying third-party legal compliance, and reviewing contracts.

Traditional automation fails here because these workflows inhabit an unbounded problem-solving space filled with ambiguous data structures, shifting contextual criteria, and human-in-the-loop dependencies.

**SmartBuy Node** solves this core operational bottleneck. Developed as a capstone application for the Kaggle 5-Day AI Agents Intensive Course, it transitions corporate procurement from fragile, ad-hoc natural language prompts into a highly structured, hardened, multi-agent framework.

SmartBuy Node enables any corporate employee to express purchasing intent in natural language. The agentic harness then autonomously:
- Reads corporate database schemas
- Verifies real-time account balances
- Parses product catalogs via standard network pipes
- Audits compliance policies
- Outputs a plain-English "Vibe Diff" summary paired with hardware multi-factor authentication (MFA) gating for executive sign-off

---

## 🛠️ System Architecture

SmartBuy Node completely abandons the brittle "Swiss Army knife" single-agent monolith pattern. Instead, it implements an immutable Directed Acyclic Graph (DAG) state distribution and specializes its components across network boundaries.

```
  [ Human Operator ] 
           │  ▲
           │  │ Vibe Diff (Plain-English Summary + Hardware MFA)
           ▼  │
┌────────────────────────────────────────────────┐
│  Orchestrator Agent (Google ADK Core)          │
│  - Intent translation                          │
│  - Milestone decomposition                     │
│  - State synchronization                       │
└───────────┬───────────────────────────┬────────┘
            │                           │
       A2A Protocol                 A2A Protocol
            ▼                           ▼
   ┌─────────────────────┐    ┌──────────────────────┐
   │ Fulfillment Agent   │    │ Compliance Agent     │
   │ - Catalog search    │    │ - Permission gating  │
   │ - Inventory check   │    │ - Policy auditing    │
   │ - Cart compilation  │    │ - Anomaly masking    │
   └────────┬────────────┘    └──────────┬───────────┘
            │                            │
        MCP Protocol               Policy Engine
            ▼                            ▼
   ┌─────────────────────┐    ┌──────────────────────┐
   │ SQLite/BigQuery     │    │ Hybrid Validator     │
   │ MCP Server          │    │ (YAML + LLM Judge)   │
   │ (Inventory DB)      │    │                      │
   └─────────────────────┘    └──────────────────────┘
```

---

## 🧪 Core Course Concepts Demonstrated

To fulfill the rigorous capstone evaluation rubric, SmartBuy Node explicitly demonstrates three mandatory concepts covered in the intensive curriculum:

### 1. Multi-Agent System & Agent-to-Agent (A2A) Interoperability

Instead of utilizing a single "Swiss Army knife" prompt with tool bloat, the logic is separated into an event-driven team using the **Agent-to-Agent (A2A) Protocol**.

- **Orchestrator Node:** Maps high-level fuzzy human intent into structured milestones, coordinates state handoffs over a decentralized file message bus, and insulates individual context windows from attention decay.
- **Fulfillment Specialist:** A specialized sub-agent hardwired strictly to commercial catalog actions, eliminating parameter hallucination during inventory checks.
- **Compliance Specialist:** A downstream isolation node responsible for structural gating and regulatory safety reviews.

### 2. Model Context Protocol (MCP) Integration

The agent's harness completely bypasses custom REST integration layers by consuming an open-standard **MCP Server** (`knowledge-base`).

- **Local Transport Protocol:** Communicates via standard input/output (`stdio`) using JSON-RPC 2.0 frames encapsulated inside localized subprocesses.
- **Capability Matrix:** The server securely exposes bounded SQLite tools (`query_knowledge` and `add_knowledge`) to query live inventory tables and catalog data without exposing raw system keys or broad project administrative rights.

### 3. Just-In-Time (JIT) Credential Downscoping & Sandboxing

The workspace enforces a **Zero Ambient Authority** architecture to eliminate the Confused Deputy vulnerability:

- When the agent dynamically provisions execution scripts to calculate item cost overages, the execution runtime intercepts the shell command, forcing it into an ephemeral, network-isolated container via **Terminal Sandboxing**.
- The isolated runner receives hyper-restricted, task-bound credentials explicit to that unique script execution. Read/write capabilities are structurally restricted to targeted project file trees using a deny-by-default manifest.

---

## 📂 Project Repository Structure

```
smartbuy-node/
├── .agent/
│   └── skills/
│       └── b2b-procurement/
│           └── SKILL.md                 # Progressive context loader
├── config/
│   └── policies.yaml                    # Deterministic gating matrices
├── src/
│   ├── __init__.py
│   ├── main.py                          # Google ADK runtime loop initialization
│   ├── mcp_server.py                    # SQLite MCP server outlet
│   ├── policy_server.py                 # Hybrid structural/semantic validator
│   └── context_resolver.py              # Regex utility for context hygiene
├── tests/
│   ├── __init__.py
│   └── test_suite.py                    # Evaluation sets & trajectory assertions
├── .env.example                         # Environment template
├── .gitignore
├── requirements.txt                     # Python dependencies
└── README.md                            # This file
```

---

## 🚀 Step-by-Step Setup Instructions

### Prerequisites

- Python 3.11+
- `pip` or `uv` package manager
- Valid Google GenAI or Vertex AI API credentials

### 1. Clone & Install Dependencies

```bash
# Clone the repository
git clone https://github.com/your-username/smartbuy-node.git
cd smartbuy-node

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the template
cp .env.example .env

# Edit .env and add your credentials
# GOOGLE_API_KEY=xxx
# GEMINI_PROJECT_ID=xxx
# DATABASE_PATH=./data/knowledge.db
```

### 3. Initialize the Local MCP Database

```bash
python -c "
import sqlite3
db = sqlite3.connect('data/knowledge.db')
db.execute('''
    CREATE TABLE IF NOT EXISTS catalog (
        id INTEGER PRIMARY KEY,
        product_name TEXT UNIQUE,
        price REAL,
        stock_quantity INTEGER,
        department TEXT,
        supplier TEXT,
        tags TEXT
    )
''')
db.execute('''
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY,
        department TEXT UNIQUE,
        allocated REAL,
        spent REAL,
        remaining REAL
    )
''')
# Sample data
db.execute('''INSERT OR IGNORE INTO catalog (product_name, price, stock_quantity, department, supplier, tags)
    VALUES ('4K Monitor', 350.00, 45, 'IT', 'Dell', 'hardware,monitor')''')
db.execute('''INSERT OR IGNORE INTO budgets (department, allocated, spent, remaining)
    VALUES ('IT', 10000.00, 3500.00, 6500.00)''')
db.commit()
print('Database initialized successfully!')
"
```

### 4. Execute the Evaluation-Driven Development Gate

```bash
# Run the test suite to verify structural integrity
python -m pytest tests/test_suite.py -v
```

### 5. Launch the Local Interactive Workspace

```bash
# Start the agent in interactive mode
python src/main.py

# You'll see a prompt like:
# > User: "We need to order 3 developer screens for the onboarding cohort next week."
```

---

## 💻 Technical Implementation Details

### Multi-Agent Orchestration Flow

1. **User Input:** `"Buy 5 4K monitors for the IT department under $2000 total"`
2. **Orchestrator Agent Parsing:**
   - Extracts: items=[4K Monitor x5], budget_limit=$2000, department=IT
   - Creates sub-tasks → routes to Fulfillment Agent
3. **Fulfillment Agent Execution:**
   - Queries MCP Server: `SELECT * FROM catalog WHERE product_name LIKE '4K%' AND department='IT'`
   - Compiles cart with pricing details
   - Returns: `[{"item": "4K Monitor", "qty": 5, "unit_price": 350, "total": 1750}]`
4. **Compliance Agent Review:**
   - Checks: Budget remaining >= $1750 ✓
   - Validates: No PII in transaction ✓
   - Generates Vibe Diff: "Spend $1750 from IT budget (remaining: $4750)"
5. **User Approval:** Hardware MFA gate → transaction approved → order placed

### Security Architecture

**Zero Ambient Authority:**
- Agent does NOT have persistent access to credentials or database
- Each sub-agent receives task-specific, ephemeral tokens
- All database queries wrapped in `try-catch` with audit logging

**JIT Downscoping:**
- Read-only tokens for catalog queries: valid 60 seconds
- Write tokens for orders: require explicit approval gate
- Context hygiene: PII scrubbed with regex before LLM processing

**Terminal Sandboxing:**
- Dynamic shell commands executed in isolated Docker container (if available)
- Fallback: subprocess with restricted environment variables
- All output sanitized via `context_resolver.py`

---

## 📊 Project Journey & Evaluation

### Evaluation-Driven Development (EDD)

We avoided writing code blindly. The project was engineered with a versioned golden dataset of multi-turn procurement scenarios before writing prompt files. Trajectory evaluation is enforced via test assertions using `IN_ORDER` matching modes, ensuring that the agents invoke tools in secure, deterministic sequences.

### The Vibe Diff & A2UI

To prevent user verification fatigue, the system leverages the Agent-to-User Interface (A2UI) protocol to output declarative UI intent strings. Human operators are presented with interactive layout cards showing a clear "Vibe Diff"—a plain-English summary translating underlying SQL operations back into business terms before final approval via hardware cryptographic security keys.

---

## 🔑 Key Architectural Insights

1. **Specialization over Monoliths:** Breaking single-agent logic into narrowly-scoped sub-agents reduces hallucination and improves reliability.
2. **Open Protocols:** MCP, A2A, and A2UI provide framework interoperability without vendor lock-in.
3. **Security as Architecture:** Zero ambient authority and JIT downscoping are enforced at the runtime level, not via prompts alone.
4. **Deterministic Evaluation:** Multi-turn trajectories validated by trajectory analysis, not just final-answer correctness.

---

## 📝 Files Overview

| File | Purpose |
|------|---------|
| `main.py` | Orchestrator agent loop + user interface |
| `mcp_server.py` | MCP server exposing SQLite catalog/budget tables |
| `policy_server.py` | Hybrid deterministic + semantic policy validator |
| `context_resolver.py` | Regex-based context hygiene (PII scrubbing) |
| `policies.yaml` | YAML gatekeeping rules (role-based access) |
| `SKILL.md` | Agent skill definition & progressive disclosure |
| `test_suite.py` | Trajectory-based evaluation tests |

---

## 🎥 Demo Usage

```
> "I need to purchase 10 mechanical keyboards for the developers, budget $1500 max"

[Orchestrator] Parsing intent... ✓
  - Items: Mechanical Keyboard x10
  - Budget limit: $1500
  - Department: [Inferred from user context]

[Fulfillment] Querying catalog... ✓
  - Found: Logitech MX Keys ($99 each, stock: 50+)
  - Estimated total: $990
  - Supplier: TechWorld

[Compliance] Auditing... ✓
  - Budget available: $4200
  - No violations
  - User role: Manager (can approve)

[Vibe Diff]
===============================================
✅ PROPOSED TRANSACTION
───────────────────────────────────────────────
Item:     Logitech MX Keys Mechanical Keyboard
Quantity: 10
Unit Price: $99.00
Subtotal: $990.00
Department: Engineering
Budget Remaining After: $3,210.00
───────────────────────────────────────────────
🔒 Please confirm with Hardware MFA to proceed
===============================================

Approve? (Y/n): Y
[MFA] Waiting for hardware confirmation...
✅ Transaction approved. Order placed successfully!
```

---

## 📚 References & Course Materials

This project demonstrates core concepts from:
- **Day 1:** The New SDLC With Vibe Coding (Agentic Engineering principles)
- **Day 2:** Agent Tools & Interoperability (MCP Protocol)
- **Day 3:** Agent Skills (Skill Anatomy & Progressive Disclosure)
- **Day 4:** Vibe Coding Agent Security and Evaluation
- **Day 5:** Spec-Driven Production Grade Development (Antigravity, Sandboxing)

---

## 📄 License

This project is licensed under **CC-BY 4.0** as required by the Kaggle competition.

---

## 🚀 Next Steps

1. Review the code in `src/` directory
2. Run: `python src/main.py` to start the interactive agent
3. Test with various procurement scenarios
4. Check `tests/test_suite.py` for validation details
5. View `config/policies.yaml` for security rule definitions

**Questions?** Refer to the inline code comments or review the course materials linked above.