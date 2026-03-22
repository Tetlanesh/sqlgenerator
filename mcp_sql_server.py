"""
MCP SQL Server — gives Copilot the ability to query a SQLite database.

HOW THIS WORKS:
===============
This script is an MCP (Model Context Protocol) server. It runs as a subprocess
launched by VS Code (configured in .vscode/mcp.json). Copilot communicates with
it over stdin/stdout using JSON messages.

The server exposes 3 "tools" — functions that Copilot can call:
  1. query()          — run a SELECT and get rows back
  2. execute()        — run INSERT/UPDATE/DELETE and get affected row count
  3. describe_table() — get column info for a table

LIFECYCLE:
==========
  VS Code starts → reads .vscode/mcp.json → launches this script
  → script tells Copilot "I have these tools"
  → Copilot calls them when needed
  → script stays alive until VS Code closes
"""

import sqlite3
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load .env file if it exists (for DB_PATH setting)
load_dotenv()

# Where is the SQLite database file?
# Reads from .env or defaults to data/sample.db relative to this script
DB_PATH = os.getenv("DB_PATH", "data/sample.db")

# Resolve relative paths from the project root (where this script lives)
PROJECT_ROOT = Path(__file__).parent
DB_FULL_PATH = (PROJECT_ROOT / DB_PATH).resolve()

# ---------------------------------------------------------------------------
# Create the MCP server
# ---------------------------------------------------------------------------
# FastMCP handles all the protocol details — JSON parsing, message routing,
# tool registration. You just write normal Python functions.

mcp = FastMCP(
    name="sql-server",                          # Name shown in VS Code
    instructions=(
        "SQL database server. Use the 'query' tool to run SELECT statements. "
        "Use 'execute' for INSERT/UPDATE/DELETE. Use 'list_tables' to see "
        "available tables and 'describe_table' to see column details."
    ),
)

# ---------------------------------------------------------------------------
# Helper: get a database connection
# ---------------------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the SQLite database.
    
    sqlite3.connect() opens the file (or creates it if missing).
    row_factory = sqlite3.Row makes rows act like dicts — so we can
    access columns by name (row["title"]) instead of index (row[0]).
    """
    if not DB_FULL_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_FULL_PATH}. "
            f"Set DB_PATH in .env or place a .db file at {DB_PATH}"
        )
    conn = sqlite3.connect(str(DB_FULL_PATH))
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


# ---------------------------------------------------------------------------
# Tool 1: query — run a SELECT statement
# ---------------------------------------------------------------------------
@mcp.tool()
def query(sql: str) -> str:
    """
    Execute a read-only SQL query (SELECT) and return the results as JSON.

    Args:
        sql: A SQL SELECT statement to execute.

    Returns:
        JSON string with "columns" (list of column names) and "rows" (list of
        row objects). Limited to 500 rows to avoid overwhelming the context.

    Example call from Copilot:
        query(sql="SELECT title, release_year FROM film LIMIT 10")
    """
    conn = get_connection()
    try:
        cursor = conn.execute(sql)

        # Get column names from the cursor description
        # cursor.description is a list of tuples: [(name, type, ...), ...]
        columns = [desc[0] for desc in cursor.description]

        # Fetch rows — limit to 500 to keep response size reasonable
        rows = cursor.fetchmany(500)

        # Convert sqlite3.Row objects to plain dicts for JSON serialization
        result = {
            "columns": columns,
            "rows": [dict(row) for row in rows],
            "row_count": len(rows),
            "truncated": len(rows) == 500,  # True if we hit the limit
        }
        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool 2: execute — run INSERT/UPDATE/DELETE
# ---------------------------------------------------------------------------
@mcp.tool()
def execute(sql: str) -> str:
    """
    Execute a write SQL statement (INSERT, UPDATE, DELETE) and return
    the number of affected rows.

    Args:
        sql: A SQL INSERT, UPDATE, or DELETE statement.

    Returns:
        JSON string with "affected_rows" count and "status".

    Example call from Copilot:
        execute(sql="UPDATE customer SET active = 0 WHERE customer_id = 42")
    """
    conn = get_connection()
    try:
        cursor = conn.execute(sql)
        conn.commit()  # SQLite requires explicit commit for writes

        result = {
            "status": "success",
            "affected_rows": cursor.rowcount,
        }
        return json.dumps(result)

    except Exception as e:
        conn.rollback()
        return json.dumps({"status": "error", "error": str(e)})
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool 3: list_tables — show all tables in the database
# ---------------------------------------------------------------------------
@mcp.tool()
def list_tables() -> str:
    """
    List all tables in the database.

    Returns:
        JSON array of table names.

    Example call from Copilot:
        list_tables()
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row["name"] for row in cursor.fetchall()]
        return json.dumps({"tables": tables})

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool 4: describe_table — show columns and types for a table
# ---------------------------------------------------------------------------
@mcp.tool()
def describe_table(table_name: str) -> str:
    """
    Get the schema (columns, types, nullable, primary key) for a table.

    Args:
        table_name: The name of the table to describe.

    Returns:
        JSON with column definitions.

    Example call from Copilot:
        describe_table(table_name="film")
    """
    conn = get_connection()
    try:
        # PRAGMA table_info returns one row per column:
        # (cid, name, type, notnull, dflt_value, pk)
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "name": row["name"],
                "type": row["type"],
                "nullable": not row["notnull"],   # notnull=1 means NOT NULL
                "default": row["dflt_value"],
                "primary_key": bool(row["pk"]),
            })

        if not columns:
            return json.dumps({"error": f"Table '{table_name}' not found"})

        return json.dumps({
            "table": table_name,
            "columns": columns,
            "column_count": len(columns),
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Entry point — start the MCP server
# ---------------------------------------------------------------------------
# This is what runs when VS Code launches the script.
# mcp.run() starts listening on stdin/stdout for JSON-RPC messages from Copilot.
# It blocks forever (until the process is killed when VS Code closes).

if __name__ == "__main__":
    mcp.run()
