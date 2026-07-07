"""
Test Suite: Evaluation-Driven Development
Part of SmartBuy Node - Automated B2B Procurement & Compliance

This module implements trajectory-based evaluation tests:
1. Multi-turn session convergence validation
2. Tool invocation sequence verification
3. Policy compliance assertions
4. Data integrity checks

Demonstrates Evaluation-Driven Development (Day 5)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.main import OrchestratorAgent
from src.policy_server import PolicyServer, TokenScope
from src.context_resolver import ContextResolver
from src.mcp_server import MCPServer, initialize_database


class ProcurementTestSuite:
    """Comprehensive test suite for SmartBuy Node."""
    
    def __init__(self):
        """Initialize test suite."""
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def run_all_tests(self):
        """Execute all tests."""
        print("\n" + "="*60)
        print("SmartBuy Node: Test Suite")
        print("="*60 + "\n")
        
        # Test groups
        self.test_orchestrator_intent_parsing()
        self.test_task_decomposition()
        self.test_policy_enforcement()
        self.test_context_sanitization()
        self.test_mcp_server()
        self.test_trajectory_validation()
        
        # Summary
        self._print_summary()
    
    def test_orchestrator_intent_parsing(self):
        """Test: Orchestrator can parse natural language intent correctly."""
        print("[TEST] Intent Parsing")
        
        agent = OrchestratorAgent()
        test_cases = [
            {
                "input": "Buy 5 4K monitors for IT under $2000",
                "expected": {
                    "has_items": True,
                    "item_count": 1,
                    "has_budget": True,
                    "has_department": True
                }
            },
            {
                "input": "I need 10 mechanical keyboards for Engineering",
                "expected": {
                    "has_items": True,
                    "item_count": 1,
                    "has_department": True
                }
            },
            {
                "input": "Order 3 standing desks, 2 monitors, 5 keyboards for HR with $5000 budget",
                "expected": {
                    "has_items": True,
                    "item_count": 3,
                    "has_budget": True,
                    "has_department": True
                }
            }
        ]
        
        for test in test_cases:
            intent = agent.parse_intent(test["input"])
            
            # Validate parsing
            passed = (
                (intent["items"] is not None) == test["expected"]["has_items"] and
                len(intent["items"]) == test["expected"]["item_count"] and
                (intent["budget_limit"] is not None) == test["expected"].get("has_budget", False) and
                (intent["department"] is not None) == test["expected"].get("has_department", False)
            )
            
            self._record_result(
                "Intent Parsing",
                f"'{test['input'][:40]}...'",
                passed
            )
    
    def test_task_decomposition(self):
        """Test: Tasks are decomposed into correct sub-tasks with proper DAG ordering."""
        print("[TEST] Task Decomposition")
        
        agent = OrchestratorAgent()
        intent = {
            "items": [
                {"name": "Monitor", "quantity": 5},
                {"name": "Keyboard", "quantity": 10}
            ],
            "budget_limit": 3000,
            "department": "IT",
            "urgency": "high"
        }
        
        tasks = agent.decompose_into_tasks(intent)
        
        # Verify task structure
        fulfillment_tasks = [t for t in tasks if t["type"] == "catalog_search"]
        compliance_tasks = [t for t in tasks if t["type"] == "policy_audit"]
        
        passed = (
            len(fulfillment_tasks) == 2 and  # 2 items
            len(compliance_tasks) == 1 and
            all("depends_on" in t for t in compliance_tasks)  # DAG ordering
        )
        
        self._record_result(
            "Task Decomposition",
            f"{len(tasks)} tasks created with proper DAG",
            passed
        )
    
    def test_policy_enforcement(self):
        """Test: Policy server enforces transaction limits and role-based access."""
        print("[TEST] Policy Enforcement")
        
        server = PolicyServer()
        
        # Test 1: Manager role with high-value transaction
        transaction = {
            "amount": 7500.00,
            "department": "IT",
            "budget_available": 10000.00,
            "items": [],
            "urgency": "normal"
        }
        
        check = server.check_transaction_policy(transaction, user_role="manager")
        passed_1 = (
            check["approved"] == True and
            check["requires_mfa"] == False  # Below $10K threshold
        )
        
        # Test 2: Employee role exceeding transaction limit
        check = server.check_transaction_policy(transaction, user_role="employee")
        passed_2 = (
            check["approved"] == False and
            len(check["violations"]) > 0
        )
        
        # Test 3: MFA requirement for high-value transactions
        high_value_transaction = transaction.copy()
        high_value_transaction["amount"] = 15000.00
        check = server.check_transaction_policy(high_value_transaction, user_role="admin")
        passed_3 = check["requires_mfa"] == True
        
        self._record_result(
            "Policy Enforcement",
            "Transaction approval and MFA gating",
            passed_1 and passed_2 and passed_3
        )
    
    def test_context_sanitization(self):
        """Test: Context resolver properly scrubs PII and detects injection attempts."""
        print("[TEST] Context Sanitization")
        
        resolver = ContextResolver()
        
        # Test 1: PII scrubbing
        text_with_pii = "Email john.doe@example.com, SSN 123-45-6789"
        scrubbed, findings = resolver.scrub_pii(text_with_pii)
        passed_1 = (
            len(findings) >= 2 and
            "@" not in scrubbed
        )
        
        # Test 2: Injection detection
        is_valid, error = resolver.validate_input("<script>alert('xss')</script>")
        passed_2 = is_valid == False
        
        # Test 3: Safe variable substitution
        template = "Buy [[QUANTITY]] [[PRODUCT]] for [[DEPARTMENT]]"
        variables = {"QUANTITY": "5", "PRODUCT": "Monitors", "DEPARTMENT": "IT"}
        result = resolver.safe_substitute(template, variables)
        passed_3 = "5 Monitors for IT" in result
        
        self._record_result(
            "Context Sanitization",
            "PII scrubbing, injection detection, safe substitution",
            passed_1 and passed_2 and passed_3
        )
    
    def test_mcp_server(self):
        """Test: MCP server handles queries correctly and prevents injection."""
        print("[TEST] MCP Server")
        
        # Initialize database
        db_path = "./data/test_knowledge.db"
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        try:
            # Test 1: Tool listing
            server = MCPServer(db_path)
            response = server.handle_request({"method": "list_tools", "id": 1})
            passed_1 = "result" in response and "tools" in response["result"]
            
            # Test 2: Successful query (once DB is initialized)
            initialize_database(db_path)
            response = server.handle_request({
                "method": "query_catalog",
                "params": {"product_name": "Monitor"},
                "id": 2
            })
            passed_2 = response["result"]["status"] == "success"
            
            # Test 3: SQL injection attempt (should be prevented)
            response = server.handle_request({
                "method": "query_catalog",
                "params": {"product_name": "'; DROP TABLE catalog; --"},
                "id": 3
            })
            # If parameterized queries work, this should return empty results, not error
            passed_3 = response["result"]["status"] == "success"
            
            self._record_result(
                "MCP Server",
                "Tool listing, query execution, injection prevention",
                passed_1 and passed_2 and passed_3
            )
            
            # Cleanup
            if os.path.exists(db_path):
                os.remove(db_path)
        
        except Exception as e:
            self._record_result(
                "MCP Server",
                "Tool listing, query execution, injection prevention",
                False
            )
    
    def test_trajectory_validation(self):
        """Test: Multi-turn trajectory is recorded and validated."""
        print("[TEST] Trajectory Validation (EDD)")
        
        agent = OrchestratorAgent()
        
        # Generate trajectory
        intent = agent.parse_intent("Buy 5 monitors for IT under $2000")
        tasks = agent.decompose_into_tasks(intent)
        
        # Validate trajectory log
        log = agent.trajectory_log
        passed = (
            len(log) >= 2 and
            any(entry["step"] == "parse_intent" for entry in log) and
            any(entry["step"] == "decompose_tasks" for entry in log) and
            all(entry["status"] == "success" for entry in log)
        )
        
        self._record_result(
            "Trajectory Validation",
            f"Multi-turn trajectory with {len(log)} steps",
            passed
        )
    
    def _record_result(self, test_name: str, description: str, passed: bool):
        """Record test result."""
        if passed:
            self.tests_passed += 1
            status = "[PASS]"
        else:
            self.tests_failed += 1
            status = "[FAIL]"
        
        self.results.append({
            "name": test_name,
            "description": description,
            "passed": passed
        })
        
        print(f"  {status}: {description}\n")
    
    def _print_summary(self):
        """Print test summary."""
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print("\n" + "="*60)
        print(f"Test Results: {self.tests_passed}/{total} PASSED ({pass_rate:.1f}%)")
        print("="*60)
        
        if self.tests_failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  ✗ {result['name']}: {result['description']}")


def test_intent_parsing():
    agent = OrchestratorAgent()
    intent = agent.parse_intent("Buy 5 monitors for IT")
    assert intent["items"], "Items should be parsed"
    assert intent["department"] == "IT", "Department should be parsed"


def test_intent_parsing_with_budget():
    agent = OrchestratorAgent()
    intent = agent.parse_intent("Buy 5 4K monitors for IT under $2000")
    assert len(intent["items"]) == 1
    assert intent["budget_limit"] == 2000.0
    assert intent["department"] == "IT"


def test_task_decomposition_dag_ordering():
    agent = OrchestratorAgent()
    intent = {
        "items": [{"name": "Monitor", "quantity": 5}, {"name": "Keyboard", "quantity": 10}],
        "budget_limit": 3000,
        "department": "IT",
        "urgency": "normal"
    }
    tasks = agent.decompose_into_tasks(intent)
    compliance_tasks = [t for t in tasks if t["type"] == "policy_audit"]
    assert len(compliance_tasks) == 1
    assert "depends_on" in compliance_tasks[0]


def test_policy_limits():
    server = PolicyServer()
    transaction = {"amount": 6000, "department": "IT", "budget_available": 10000}
    check = server.check_transaction_policy(transaction, user_role="employee")
    assert not check["approved"], "Employee should not exceed limit"


def test_policy_mfa_threshold():
    server = PolicyServer()
    transaction = {"amount": 15000, "department": "IT", "budget_available": 50000}
    check = server.check_transaction_policy(transaction, user_role="admin")
    assert check["requires_mfa"] is True


def test_pii_scrubbing():
    resolver = ContextResolver()
    text = "Email: john@example.com"
    scrubbed, findings = resolver.scrub_pii(text)
    assert len(findings) > 0, "PII should be detected"
    assert "@" not in scrubbed


def test_injection_detection():
    resolver = ContextResolver()
    is_valid, _ = resolver.validate_input("<script>alert('xss')</script>")
    assert not is_valid


def test_mcp_list_tools():
    server = MCPServer(":memory:")
    response = server.handle_request({"method": "list_tools", "id": 1})
    assert "result" in response
    assert "tools" in response["result"]


def test_mcp_sql_injection_prevention():
    db_path = "./data/test_knowledge.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    initialize_database(db_path)
    server = MCPServer(db_path)
    response = server.handle_request({
        "method": "query_catalog",
        "params": {"product_name": "'; DROP TABLE catalog; --"},
        "id": 1
    })
    assert response["result"]["status"] == "success"
    if os.path.exists(db_path):
        os.remove(db_path)


def test_trajectory_logging():
    agent = OrchestratorAgent()
    agent.parse_intent("Buy 5 monitors for IT under $2000")
    agent.decompose_into_tasks({
        "items": [{"name": "Monitor", "quantity": 5}],
        "budget_limit": 2000,
        "department": "IT",
        "urgency": "normal"
    })
    log = agent.trajectory_log
    assert any(e["step"] == "parse_intent" for e in log)
    assert any(e["step"] == "decompose_tasks" for e in log)
    assert all(e["status"] == "success" for e in log)


if __name__ == "__main__":
    # Run test suite
    suite = ProcurementTestSuite()
    suite.run_all_tests()
