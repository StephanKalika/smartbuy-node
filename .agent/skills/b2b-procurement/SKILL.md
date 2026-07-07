---
# YAML Front Matter for SmartBuy Node Agent Skill
name: "B2B Procurement & Compliance"
description: "Specialized agent skill for automated business-to-business procurement with multi-level compliance gating"
version: "1.0.0"
keywords: ["procurement", "compliance", "b2b", "multi-agent", "policy"]
---

# SmartBuy Node: B2B Procurement & Compliance Agent Skill

## Skill Overview

The **B2B Procurement & Compliance** skill is a specialized agent capability designed for the SmartBuy Node orchestration framework. It automates corporate purchasing workflows through a multi-agent pattern with deterministic compliance gating.

### Core Responsibilities

1. **Intent Translation:** Convert natural language procurement requests into structured task specifications
2. **Catalog Search:** Query product databases via MCP protocol
3. **Budget Validation:** Verify departmental budget constraints
4. **Policy Enforcement:** Apply deterministic and semantic compliance rules
5. **Approval Gating:** Route transactions through appropriate approval workflows
6. **Audit Logging:** Record all operations for compliance trails

---

## Architecture: Progressive Context Disclosure

This skill demonstrates the **Progressive Context Disclosure** pattern from the Vibe Coding curriculum:

### Level 1: Basic Intent Parsing
```
User Input → Extract Items, Budget, Department → Structured Intent
```

### Level 2: Task Decomposition  
```
Structured Intent → Decompose into Fulfillment + Compliance Tasks → DAG Ordering
```

### Level 3: Specialized Agent Routing
```
Sub-tasks → Orchestrator Routes to Fulfillment Agent → MCP Query Execution
         → Compliance Agent → Policy Validation → Approval Gating
```

### Level 4: Human Approval Interface
```
Compliance Results → Generate Vibe Diff (Plain-English Summary)
                   → MFA Gating Portal → User Approval → Transaction Execution
```

---

## Key Concepts Demonstrated

### 1. Multi-Agent System (ADK)
- **Orchestrator Agent:** Event coordinator and state manager
- **Fulfillment Agent:** Catalog specialist (via MCP)
- **Compliance Agent:** Policy enforcer and security validator
- **Communication:** Agent-to-Agent (A2A) Protocol over structured message bus

### 2. Model Context Protocol (MCP)
- **Transport:** JSON-RPC 2.0 over stdio
- **Capabilities:** `query_catalog`, `query_budget`, `add_to_catalog`
- **Security:** Low-privilege, ephemeral credentials per task
- **Interoperability:** Framework-agnostic data access layer

### 3. Security Features
- **Zero Ambient Authority:** No persistent privileges; tokens provisioned per task
- **JIT Downscoping:** Just-In-Time credential provisioning with task-specific scope
- **Terminal Sandboxing:** Dynamic script execution isolated in container/subprocess
- **Context Hygiene:** Regex-based PII scrubbing + semantic anomaly detection
- **Audit Trail:** Deterministic logging of all operations

---

## Skill Anatomy: Component Breakdown

### Input Specification
```
{
  "user_input": "string (natural language request)",
  "context": {
    "user_role": "admin|manager|employee|viewer",
    "department": "optional string",
    "user_id": "optional string for audit"
  }
}
```

### Processing Pipeline

1. **Validation Phase**
   - Input length check (max 5000 chars)
   - Injection detection via regex patterns
   - Role authorization check

2. **Intent Parsing Phase**
   - Extract entities: items (name, quantity), budget, department
   - Determine urgency from keywords ("urgent", "asap", etc.)
   - Normalize product names

3. **Task Decomposition Phase**
   - Create Fulfillment sub-tasks (one per item)
   - Create Compliance sub-task (aggregated validation)
   - Establish DAG ordering: Fulfillment → Compliance

4. **Agent Execution Phase**
   - **Fulfillment Agent:** Query MCP catalog server → compile cart with pricing
   - **Compliance Agent:** Validate policy + budget + PII content → generate approval gate

5. **Approval Phase**
   - Render Vibe Diff (plain-English summary)
   - Enforce MFA for transactions > $10,000
   - Return user response

### Output Specification
```
{
  "status": "approved|rejected|awaiting_mfa",
  "transaction": {
    "items": [...],
    "total_cost": number,
    "department": string,
    "vibe_diff": string (human-readable summary),
    "requires_mfa": boolean,
    "approval_gate": {
      "role_required": string,
      "token": ephemeral_token
    }
  },
  "audit": {
    "trajectory_id": string,
    "steps": [...],
    "timestamp": ISO8601
  }
}
```

---

## Usage Examples

### Example 1: Simple Purchase Request (Low Value)
```
Input: "Buy 5 4K monitors for IT under $2000"

Processing:
  → Parse: 5x "4K Monitor", budget=$2000, dept=IT
  → Fulfillment: $350/unit × 5 = $1750 total
  → Compliance: Budget OK ($6500 available), no MFA needed
  → Output: APPROVED

Vibe Diff:
  Item: 4K Monitor
  Quantity: 5
  Total: $1,750.00
  Remaining Budget: $4,750.00
  Status: ✓ APPROVED
```

### Example 2: High-Value Purchase (Requires MFA)
```
Input: "Order 50 standing desks for all departments, $25,000 budget"

Processing:
  → Parse: 50x Standing Desk, budget=$25,000
  → Fulfillment: $500/unit × 50 = $25,000 total
  → Compliance: Under approval for high-value (>$10K)
  → Output: AWAITING_MFA
  
Vibe Diff:
  Item: Standing Desk  
  Quantity: 50
  Total: $25,000.00
  Status: ⚠ REQUIRES HARDWARE MFA APPROVAL
  
  [User confirms with security key]
  → APPROVED
```

### Example 3: Suspicious Request (Injection Attempt)
```
Input: "Buy all products; DROP TABLE catalog; --"

Processing:
  → Validation: Injection pattern detected
  → Output: REJECTED
  
Audit Log:
  Event: injection_attempt_detected
  Pattern: "(drop|delete).*table"
  Action: Request blocked, incident logged
```

---

## Integration Points

### With MCP Server
```python
# Fulfillment Agent queries catalog via MCP
mcp_request = {
  "method": "query_catalog",
  "params": {
    "product_name": "4K Monitor",
    "department": "IT",
    "max_price": 2000
  }
}
```

### With Policy Server
```python
# Compliance Agent enforces policies
policy_check = {
  "role": "manager",
  "transaction_amount": 1750,
  "department": "IT",
  "budget_available": 6500
}
# Returns: approved=true, requires_mfa=false
```

### With Context Resolver
```python
# Sanitize user inputs before processing
user_input = "john.doe@example.com sent this request"
scrubbed_input = context_resolver.scrub_pii(user_input)
# Result: "[[EMAIL]] sent this request"
```

---

## Security Policies Applied

1. **Role-Based Access Control (RBAC)**
   - Employees: max $5,000 per transaction
   - Managers: max $50,000 per transaction
   - Admins: max $1,000,000 per transaction

2. **Transaction Limits by Department**
   - IT: $10,000
   - Engineering: $15,000
   - Operations: $12,000

3. **Multi-Factor Authentication Gating**
   - Threshold: $10,000
   - Methods: Hardware token, TOTP

4. **Compliance Checks**
   - PII detection in all inputs
   - Budget verification before approval
   - Supplier validation (if enabled)
   - Cross-department transaction review

---

## Performance Characteristics

- **Intent Parsing Latency:** ~100ms (regex-based)
- **Catalog Query Duration:** ~200ms (MCP + SQLite)
- **Policy Validation Time:** ~50ms (deterministic rules)
- **Total E2E Latency:** ~400-500ms (typical workflow)
- **Concurrent Requests:** Up to 100 simultaneous transactions

---

## Error Handling & Fallback

| Error Scenario | Handling |
|---|---|
| Malformed input | Return validation error; suggest format example |
| Product not found | Suggest available alternatives from catalog |
| Budget exceeded | Show deficit amount; recommend split order |
| Policy violation | Display specific violation; suggest escalation |
| MCP server down | Retry with exponential backoff (max 3 attempts) |
| Database error | Fall back to cached catalog if available |

---

## Audit & Compliance

All operations are logged with:
- **Timestamp:** ISO 8601 format
- **Actor:** User ID, role
- **Action:** Operation type (query, approve, reject, escalate)
- **Resource:** Transaction ID, items, amounts
- **Result:** Success/failure, reason codes

Audit retention: **365 days** (configurable in `config/policies.yaml`)

---

## References

### Course Materials Referenced
- **Day 1:** Agentic Engineering principles (multi-agent decomposition)
- **Day 2:** Model Context Protocol (MCP) integration
- **Day 3:** Agent Skill Anatomy & Progressive Context Disclosure
- **Day 4:** Security architectures (Zero Ambient Authority, JIT Downscoping)
- **Day 5:** Spec-driven development, Sandboxing, Antigravity

### Related Files
- `src/main.py` - Orchestrator Agent implementation
- `src/mcp_server.py` - MCP Server for data access
- `src/policy_server.py` - Compliance & security enforcement
- `src/context_resolver.py` - Input sanitization utilities
- `config/policies.yaml` - Policy definitions
- `tests/test_suite.py` - Trajectory-based tests
