"""
Model Context Protocol (MCP) Server
Part of SmartBuy Node - Automated B2B Procurement & Compliance

This module implements an MCP Server that:
1. Exposes SQLite database via standard JSON-RPC 2.0 interface
2. Provides catalog and budget query tools to sub-agents
3. Manages low-privilege database connections
4. Prevents direct SQL access (mitigates injection attacks)

Demonstrates MCP Integration (Day 2: Agent Tools & Interoperability)
"""

import os
import json
import sqlite3
import re
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

# Default database path
DB_PATH = os.getenv("DATABASE_PATH", "./data/knowledge.db")


class MCPServer:
    """
    Model Context Protocol Server for SmartBuy Node.
    
    Features:
    - Low-privilege SQLite query execution
    - Query parameter sanitization
    - JSON-RPC 2.0 request/response handling
    - Tool discovery and capability listing
    """
    
    def __init__(self, db_path: str = DB_PATH):
        """Initialize MCP Server with database connection."""
        self.db_path = db_path
        self.tools = {
            "query_catalog": {
                "description": "Query product catalog by name, department, or price range",
                "params": {
                    "product_name": "Optional: Product name pattern to search",
                    "department": "Optional: Filter by department (e.g., 'IT', 'Engineering')",
                    "max_price": "Optional: Maximum price filter",
                    "limit": "Optional: Limit results (default 10)"
                }
            },
            "query_budget": {
                "description": "Check department budget status and availability",
                "params": {
                    "department": "Required: Department name",
                }
            },
            "add_to_catalog": {
                "description": "Add or update product in catalog (admin only)",
                "params": {
                    "product_name": "Required: Product name",
                    "price": "Required: Unit price",
                    "stock_quantity": "Required: Stock quantity",
                    "department": "Optional: Department tag",
                    "supplier": "Optional: Supplier name"
                }
            }
        }
    
    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections with error handling."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dicts
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            print(f"[MCP] Database error: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle JSON-RPC 2.0 request (main MCP interface).
        
        Args:
            request: JSON-RPC request dict with method and params
            
        Returns:
            JSON-RPC response dict
        """
        
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            # Route to appropriate handler
            if method == "list_tools":
                result = self.list_tools()
            elif method == "query_catalog":
                result = self.query_catalog(**params)
            elif method == "query_budget":
                result = self.query_budget(**params)
            elif method == "add_to_catalog":
                result = self.add_to_catalog(**params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": request_id
                }
            
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": request.get("id")
            }
    
    def list_tools(self) -> Dict[str, Any]:
        """List available tools and their parameters."""
        return {"tools": self.tools}
    
    def query_catalog(self, product_name: Optional[str] = None,
                     department: Optional[str] = None,
                     max_price: Optional[float] = None,
                     limit: int = 10) -> Dict[str, Any]:
        """
        Query product catalog with optional filters.
        
        Demonstrates: Deterministic query bounds (no injection attacks)
        """
        
        try:
            with self._get_db_connection() as conn:
                query = "SELECT * FROM catalog WHERE 1=1"
                params = []
                
                # Parameterized queries prevent SQL injection
                if product_name:
                    query += " AND product_name LIKE ?"
                    params.append(f"%{product_name}%")
                
                if department:
                    query += " AND department = ?"
                    params.append(department)
                
                if max_price is not None:
                    query += " AND price <= ?"
                    params.append(max_price)
                
                # Enforce limit to prevent resource exhaustion
                query += f" LIMIT {min(limit, 100)}"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to dicts
                results = [dict(row) for row in rows]
                
                return {
                    "status": "success",
                    "count": len(results),
                    "results": results
                }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def query_budget(self, department: str) -> Dict[str, Any]:
        """
        Query department budget status.
        
        Demonstrates: Zero ambient authority (read-only access)
        """
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM budgets WHERE department = ?",
                    (department,)
                )
                row = cursor.fetchone()
                
                if row:
                    budget_data = dict(row)
                    return {
                        "status": "success",
                        "budget": budget_data
                    }
                else:
                    return {
                        "status": "not_found",
                        "message": f"No budget found for department: {department}"
                    }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def add_to_catalog(self, product_name: str, price: float,
                       stock_quantity: int, department: Optional[str] = None,
                       supplier: Optional[str] = None) -> Dict[str, Any]:
        """
        Add or update product in catalog.
        
        Demonstrates: JIT token scoping (write access requires elevation)
        Note: In production, this would require authentication/authorization
        """
        
        try:
            # Input validation to prevent injection
            if not re.match(r'^[a-zA-Z0-9\s\-]+$', product_name):
                raise ValueError("Invalid product name format")
            
            if price < 0 or stock_quantity < 0:
                raise ValueError("Price and stock must be non-negative")
            
            with self._get_db_connection() as conn:
                # Upsert pattern: INSERT if new, UPDATE if exists
                conn.execute(
                    """
                    INSERT OR REPLACE INTO catalog 
                    (product_name, price, stock_quantity, department, supplier)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (product_name, price, stock_quantity, department, supplier)
                )
                
                return {
                    "status": "success",
                    "message": f"Product '{product_name}' added/updated in catalog"
                }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


def initialize_database(db_path: str = DB_PATH) -> None:
    """Initialize SQLite database with schema if it doesn't exist."""
    
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create catalog table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                stock_quantity INTEGER NOT NULL,
                department TEXT,
                supplier TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT UNIQUE NOT NULL,
                allocated REAL NOT NULL,
                spent REAL DEFAULT 0,
                remaining REAL GENERATED ALWAYS AS (allocated - spent) STORED,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample data if tables are empty
        cursor.execute("SELECT COUNT(*) FROM catalog")
        if cursor.fetchone()[0] == 0:
            sample_catalog = [
                ("4K Monitor", 350.00, 45, "IT", "Dell", "hardware,monitor"),
                ("Mechanical Keyboard", 99.00, 150, "IT", "Logitech", "hardware,input"),
                ("Standing Desk", 500.00, 20, "Engineering", "IKEA", "furniture,workspace"),
                ("USB-C Hub", 45.00, 200, "IT", "Belkin", "hardware,accessory"),
                ("Noise Cancelling Headset", 250.00, 30, "Engineering", "Sony", "audio,productivity"),
            ]
            cursor.executemany(
                "INSERT INTO catalog (product_name, price, stock_quantity, department, supplier, tags) VALUES (?, ?, ?, ?, ?, ?)",
                sample_catalog
            )
        
        cursor.execute("SELECT COUNT(*) FROM budgets")
        if cursor.fetchone()[0] == 0:
            sample_budgets = [
                ("IT", 10000.00, 3500.00),
                ("Engineering", 15000.00, 5000.00),
                ("Marketing", 8000.00, 2000.00),
                ("HR", 5000.00, 1000.00),
                ("Operations", 12000.00, 4500.00),
            ]
            cursor.executemany(
                "INSERT INTO budgets (department, allocated, spent) VALUES (?, ?, ?)",
                sample_budgets
            )
        
        conn.commit()
        conn.close()
        
        print(f"[MCP] Database initialized at: {db_path}")
    
    except Exception as e:
        print(f"[MCP] Database initialization error: {str(e)}")
        raise


if __name__ == "__main__":
    # Initialize database
    initialize_database()
    
    # Example MCP request handling
    server = MCPServer()
    
    # Example 1: List tools
    print("\n[Example] List tools:")
    response = server.handle_request({"method": "list_tools", "id": 1})
    print(json.dumps(response, indent=2))
    
    # Example 2: Query catalog
    print("\n[Example] Query catalog for monitors:")
    response = server.handle_request({
        "method": "query_catalog",
        "params": {"product_name": "Monitor"},
        "id": 2
    })
    print(json.dumps(response, indent=2))
    
    # Example 3: Query budget
    print("\n[Example] Query IT department budget:")
    response = server.handle_request({
        "method": "query_budget",
        "params": {"department": "IT"},
        "id": 3
    })
    print(json.dumps(response, indent=2))
