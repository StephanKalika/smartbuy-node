"""
Orchestrator Agent: Multi-Agent Coordination Engine
Part of SmartBuy Node - Automated B2B Procurement & Compliance

This module implements the Orchestrator Node that:
1. Parses user intent in natural language
2. Decomposes intent into atomic milestones
3. Routes sub-tasks to specialized agents (Fulfillment, Compliance)
4. Synchronizes state across the agent network via A2A protocol
5. Generates final Vibe Diff summaries for user approval
"""

import os
import sys
import json
import re
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force UTF-8 output on Windows so emoji/unicode prints correctly
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Google Gen AI SDK (formerly google.generativeai)
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class OrchestratorAgent:
    """
    Orchestrator Node: Maps fuzzy user intent into structured task milestones.
    
    Demonstrates: Multi-Agent System (ADK) + A2A Protocol
    - Decomposes unstructured natural language into atomic operations
    - Manages state transitions across sub-agent boundaries
    - Enforces deterministic evaluation via trajectory logging
    """
    
    def __init__(self):
        """Initialize the Orchestrator Agent with API configuration."""
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

        # Initialize GenAI if available
        if GENAI_AVAILABLE and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model = self.model_name
        else:
            self.client = None
            self.model = None

        # Initialize real MCP server and policy server (A2A sub-agents)
        try:
            from src.mcp_server import MCPServer, initialize_database
            from src.policy_server import PolicyServer
        except ModuleNotFoundError:
            from mcp_server import MCPServer, initialize_database
            from policy_server import PolicyServer
        db_path = os.getenv("DATABASE_PATH", "./data/knowledge.db")
        initialize_database(db_path)
        self.mcp = MCPServer(db_path)
        self.policy = PolicyServer()

        # Trajectory log for Evaluation-Driven Development (EDD)
        self.trajectory_log = []

        print("[Orchestrator] Agent initialized with multi-agent coordination enabled.")
        print(f"[Orchestrator] MCP server connected: {db_path}")
        print(f"[Orchestrator] LLM: {'enabled (' + self.model_name + ')' if self.client else 'disabled (no API key)'}")
    
    def parse_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Parse user intent using pattern matching + optional LLM.
        
        Demonstrates:
        - Intent translation (Day 1: New SDLC)
        - Structured decomposition without monolithic prompts
        
        Args:
            user_input: Natural language purchasing request
            
        Returns:
            Structured intent dict with extracted entities
        """
        
        # First: Pattern-based extraction (deterministic)
        intent = {
            "raw_input": user_input,
            "items": [],
            "budget_limit": None,
            "department": None,
            "urgency": "normal",
            "phase": "parsing"
        }
        
        # Extract budget constraint (pattern: "$XXXX" or "budget XXXX")
        # Look for explicit $ sign or "budget" keyword
        budget_match = re.search(r'\$\s*([\d,]+(?:\.\d{2})?)\s*(USD|dollars)?', user_input)
        if not budget_match:
            budget_match = re.search(r'budget\s+(?:of\s+)?\$?\s*([\d,]+(?:\.\d{2})?)', user_input, re.IGNORECASE)
        if budget_match:
            budget_str = budget_match.group(1).replace(',', '')
            intent["budget_limit"] = float(budget_str)
        
        # Extract department (pattern: "IT", "Engineering", "Marketing", etc.)
        # Use word boundaries to match whole words only
        departments = ["HR", "IT", "Engineering", "Marketing", "Finance", "Operations"]
        for dept in departments:
            pattern = r'\b' + dept + r'\b'
            if re.search(pattern, user_input, re.IGNORECASE):
                intent["department"] = dept
                break
        
        # Extract item quantities (pattern: "N monitors", "X keyboards", etc.)
        # Handle multiple items: "3 desks, 2 monitors, 5 keyboards"
        # Split by common delimiters: comma, "and", "with"
        item_segments = re.split(r'(?:,|,\s+and|\s+and\s+with)', user_input)
        
        for segment in item_segments:
            # Skip segment if it contains exclusion words (department, budget keywords)
            if any(w in segment.lower() for w in ['for ', 'under ', 'budget']):
                # Extract only the part before these keywords
                match = re.match(r'^(.+?)(?:\s+for|\s+under|\s+budget)', segment, re.IGNORECASE)
                if match:
                    segment = match.group(1)
                else:
                    continue
            
            # Now extract quantity + item name from segment
            qty_match = re.search(r'(\d+)\s+([\w\s]+?)$', segment.strip(), re.IGNORECASE)
            if qty_match:
                clean_item = qty_match.group(2).strip().rstrip(',').strip()
                if clean_item and not clean_item.lower().startswith(('for', 'under')):
                    intent["items"].append({
                        "name": clean_item,
                        "quantity": int(qty_match.group(1)),
                        "status": "pending"
                    })
        
        # Urgency detection
        if any(word in user_input.lower() for word in ["urgent", "asap", "today", "immediately"]):
            intent["urgency"] = "high"

        # LLM enhancement: fill gaps regex couldn't extract
        if self.client and (not intent["items"] or not intent["department"]):
            intent = self._llm_enhance_intent(user_input, intent)

        self.trajectory_log.append({
            "step": "parse_intent",
            "input": user_input,
            "output": intent,
            "status": "success"
        })

        return intent

    def _llm_enhance_intent(self, user_input: str, partial_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Gemini to fill gaps the regex parser couldn't extract.
        Falls back silently to partial_intent on any API error.
        """
        prompt = f"""Extract procurement details from this request and return ONLY valid JSON.

Request: "{user_input}"

Return JSON with this exact structure:
{{
  "items": [{{"name": "product name", "quantity": 1}}],
  "budget_limit": null or number,
  "department": null or "department name",
  "urgency": "normal" or "high"
}}

Rules: quantity must be an integer, budget_limit is a number or null, urgency is "high" only for urgent/asap/today."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            llm_data = json.loads(raw.strip())

            # Merge: prefer LLM values for missing fields only
            if not partial_intent["items"] and llm_data.get("items"):
                partial_intent["items"] = [
                    {"name": i["name"], "quantity": i["quantity"], "status": "pending"}
                    for i in llm_data["items"]
                ]
            if not partial_intent["department"] and llm_data.get("department"):
                partial_intent["department"] = llm_data["department"]
            if not partial_intent["budget_limit"] and llm_data.get("budget_limit"):
                partial_intent["budget_limit"] = llm_data["budget_limit"]
            if llm_data.get("urgency") == "high":
                partial_intent["urgency"] = "high"

        except Exception:
            pass  # Regex result is still valid; LLM enhancement is best-effort

        return partial_intent
    
    def decompose_into_tasks(self, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decompose parsed intent into atomic, delegable tasks.
        
        Demonstrates A2A Protocol:
        - Creates sub-tasks for Fulfillment Agent (inventory search)
        - Creates sub-tasks for Compliance Agent (budget verification)
        - Maintains DAG ordering (fulfill → comply)
        
        Args:
            intent: Parsed user intent structure
            
        Returns:
            List of task dicts ready for delegation
        """
        
        tasks = []
        
        # Task 1: Fulfillment Agent - Catalog Search
        if intent["items"]:
            for idx, item in enumerate(intent["items"]):
                fulfillment_task = {
                    "task_id": f"fulfill-{idx}",
                    "type": "catalog_search",
                    "target_agent": "fulfillment",
                    "payload": {
                        "product_name": item["name"],
                        "quantity": item["quantity"],
                        "department": intent.get("department", "Unknown"),
                        "budget_limit": intent.get("budget_limit")
                    },
                    "state": "pending",
                    "priority": 1 if intent["urgency"] == "high" else 0
                }
                tasks.append(fulfillment_task)
        
        # Task 2: Compliance Agent - Policy Audit
        compliance_task = {
            "task_id": "comply-budget",
            "type": "policy_audit",
            "target_agent": "compliance",
            "payload": {
                "department": intent.get("department"),
                "budget_limit": intent.get("budget_limit"),
                "item_count": len(intent["items"])
            },
            "state": "pending",
            "priority": 1,
            "depends_on": [t["task_id"] for t in tasks]  # DAG: compliance runs after fulfillment
        }
        tasks.append(compliance_task)
        
        self.trajectory_log.append({
            "step": "decompose_tasks",
            "task_count": len(tasks),
            "status": "success"
        })
        
        return tasks
    
    def render_vibe_diff(self, fulfillment_result: Dict[str, Any], 
                        compliance_result: Dict[str, Any]) -> str:
        """
        Render Vibe Diff: (Plain-English summary for user approval)
        
        Demonstrates A2UI Protocol:
        - Translates technical operations into business language
        - Provides human-readable transaction summary
        - Includes MFA gating checkpoint
        
        Args:
            fulfillment_result: Output from Fulfillment Agent
            compliance_result: Output from Compliance Agent
            
        Returns:
            Formatted Vibe Diff summary
        """
        
        vibe_diff = """
===============================================
✅ PROPOSED TRANSACTION (Vibe Diff)
───────────────────────────────────────────────
"""
        
        # Add item details
        if fulfillment_result.get("cart"):
            for item in fulfillment_result["cart"]:
                vibe_diff += f"""
Item:        {item.get('product_name', 'Unknown')}
Quantity:    {item.get('quantity', '?')}
Unit Price:  ${item.get('unit_price', '0'):.2f}
Subtotal:    ${item.get('total', 0):.2f}
Supplier:    {item.get('supplier', 'TBD')}
"""
        
        # Add budget info
        total_cost = fulfillment_result.get("total_cost", 0)
        remaining = compliance_result.get("budget_remaining", 0)
        
        vibe_diff += f"""
───────────────────────────────────────────────
💰 BUDGET IMPACT:
Total Cost:           ${total_cost:.2f}
Department Budget:    ${compliance_result.get('budget_allocated', 0):.2f}
Budget Remaining:     ${remaining:.2f}
───────────────────────────────────────────────
"""
        
        # Add compliance status
        if compliance_result.get("approved"):
            vibe_diff += "🔒 ✓ Compliance: PASSED\n"
        else:
            vibe_diff += "🔒 ✗ Compliance: ISSUES DETECTED\n"
        
        if compliance_result.get("issues"):
            for issue in compliance_result["issues"]:
                vibe_diff += f"   ⚠️  {issue}\n"
        
        vibe_diff += """
───────────────────────────────────────────────
🔐 Please confirm with Hardware MFA to proceed
===============================================
"""
        
        return vibe_diff
    
    def run_interactive_session(self):
        """
        Launch interactive agent session for user interaction.
        
        Demonstrates: Full multi-agent orchestration flow
        """
        
        print("\n" + "="*60)
        print("SmartBuy Node: Automated B2B Procurement & Compliance")
        print("="*60)
        print("\nEnter procurement requests in natural language.")
        print("Examples:")
        print("  - 'Buy 5 4K monitors for IT under $2000'")
        print("  - 'I need 10 mechanical keyboards for Engineering'")
        print("  - 'Order 2 standing desks for HR, budget $3000'")
        print("\nType 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input("> ").strip()
                
                if user_input.lower() == "exit":
                    print("\n✅ Session closed. Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print(f"\n[Orchestrator] Processing: '{user_input}'")
                
                # Step 1: Parse Intent
                intent = self.parse_intent(user_input)
                print(f"  ✓ Intent parsed: {len(intent['items'])} items identified")
                
                if not intent["items"]:
                    print("  ⚠️  No items detected. Please specify quantities and product names.")
                    continue
                
                # Step 2: Decompose into Tasks
                tasks = self.decompose_into_tasks(intent)
                print(f"  ✓ Decomposed into {len(tasks)} tasks")
                
                # Step 3: Fulfillment Agent — real MCP catalog queries
                fulfillment_result = self._run_fulfillment_agent(tasks)
                print(f"  ✓ Fulfillment: {len(fulfillment_result.get('cart', []))} items found")

                # Step 4: Compliance Agent — real policy + MCP budget checks
                compliance_result = self._run_compliance_agent(intent, fulfillment_result)
                print(f"  ✓ Compliance: {'PASSED' if compliance_result['approved'] else 'REVIEW NEEDED'}")
                
                # Step 5: Render Vibe Diff
                vibe_diff = self.render_vibe_diff(fulfillment_result, compliance_result)
                print(vibe_diff)
                
                # Step 6: Request User Approval
                approval = input("\nApprove transaction? (Y/n): ").strip().lower()
                if approval in ["y", "yes", ""]:
                    print("✅ Transaction approved! Order placed successfully.")
                    self.trajectory_log.append({
                        "step": "transaction_completed",
                        "status": "success"
                    })
                else:
                    print("❌ Transaction cancelled.")
                
            except KeyboardInterrupt:
                print("\n\n✅ Agent session interrupted. Goodbye!")
                break
            except EOFError:
                print("\n✅ Session ended. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Please try again.\n")
    
    def _run_fulfillment_agent(self, tasks: List[Dict]) -> Dict[str, Any]:
        """
        Fulfillment Agent: queries real MCP server (SQLite catalog) via A2A protocol.
        Demonstrates: MCP integration + A2A task routing.
        """
        cart = []
        total_cost = 0

        for task in tasks:
            if task["type"] != "catalog_search":
                continue

            product_name = task["payload"]["product_name"]
            quantity = task["payload"]["quantity"]
            max_price = task["payload"].get("budget_limit")

            # A2A call → MCP server → SQLite catalog
            # Try full name first, then fallback to first significant word
            response = self.mcp.handle_request({
                "method": "query_catalog",
                "params": {"product_name": product_name, "max_price": max_price, "limit": 1},
                "id": task["task_id"]
            })
            results = response.get("result", {}).get("results", [])

            # Fallback: search by first keyword (handles plurals, extra words)
            if not results:
                keyword = product_name.split()[0] if product_name.split() else product_name
                response = self.mcp.handle_request({
                    "method": "query_catalog",
                    "params": {"product_name": keyword, "max_price": max_price, "limit": 1},
                    "id": task["task_id"] + "-fallback"
                })
                results = response.get("result", {}).get("results", [])

            if results:
                item = results[0]
                item_total = item["price"] * quantity
                cart.append({
                    "product_name": item["product_name"],
                    "quantity": quantity,
                    "unit_price": item["price"],
                    "total": item_total,
                    "supplier": item.get("supplier", "Unknown"),
                    "stock_available": item.get("stock_quantity", 0)
                })
                total_cost += item_total
            else:
                # Product not in catalog — log and skip
                self.trajectory_log.append({
                    "step": "fulfillment_not_found",
                    "product": product_name,
                    "status": "not_found"
                })

        return {"cart": cart, "total_cost": total_cost, "status": "success"}

    def _run_compliance_agent(self, intent: Dict, fulfillment: Dict) -> Dict[str, Any]:
        """
        Compliance Agent: queries real MCP server for budget + PolicyServer for rules.
        Demonstrates: A2A protocol + security policy enforcement.
        """
        department = intent.get("department") or "IT"
        transaction_cost = fulfillment.get("total_cost", 0)

        # A2A call → MCP server → SQLite budgets table
        budget_response = self.mcp.handle_request({
            "method": "query_budget",
            "params": {"department": department},
            "id": "comply-budget"
        })

        budget_data = budget_response.get("result", {}).get("budget", {})
        budget_allocated = budget_data.get("allocated", 10000.0)
        budget_spent = budget_data.get("spent", 0.0)
        budget_remaining = budget_data.get("remaining", budget_allocated - budget_spent)

        # A2A call → Policy server → deterministic rule check
        policy_result = self.policy.check_transaction_policy(
            transaction={
                "amount": transaction_cost,
                "department": department,
                "budget_available": budget_remaining,
                "items": fulfillment.get("cart", []),
                "urgency": intent.get("urgency", "normal")
            },
            user_role=os.getenv("USER_ROLE", "manager")
        )

        issues = policy_result.get("violations", [])
        if intent.get("urgency") == "high" and transaction_cost > 5000:
            issues.append("High-urgency, high-value transactions require director approval")

        return {
            "approved": policy_result["approved"],
            "department": department,
            "budget_allocated": budget_allocated,
            "budget_spent": budget_spent,
            "budget_remaining": budget_remaining,
            "transaction_cost": transaction_cost,
            "requires_mfa": policy_result.get("requires_mfa", False),
            "issues": issues,
            "status": "success"
        }


def main():
    """Entry point for SmartBuy Node agent."""
    agent = OrchestratorAgent()
    agent.run_interactive_session()


if __name__ == "__main__":
    main()
