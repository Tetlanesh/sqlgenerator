"""
MCP SQL Server — gives Copilot the ability to query a SQLite database.

HOW THIS WORKS:
===============
This script is an MCP (Model Context Protocol) server. It runs as a subprocess
launched by VS Code (configured in .vscode/mcp.json). Copilot communicates with
it over stdin/stdout using JSON messages.

The server exposes tools — functions that Copilot can call:
  1. query()          — run a SELECT and get rows back
  2. execute()        — run INSERT/UPDATE/DELETE and get affected row count
  3. list_tables()    — show all tables in the database
  4. describe_table() — get column info for a table
  5. review_sql()     — sentry gate: validate SQL before execution

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
import re
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import sqlglot
from openai import OpenAI

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
# Sentry configuration
# ---------------------------------------------------------------------------

# OpenAI API key — required for Layer 2 (LLM review)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Which model to use for the sentry reviewer (cost-efficient default)
SENTRY_MODEL = os.getenv("SENTRY_MODEL", "gpt-4o-mini")

# Set to "false" to skip Layer 2 (LLM review) — Layer 1 still runs
SENTRY_ENABLED = os.getenv("SENTRY_ENABLED", "true").lower() == "true"

# Load the sentry system prompt and schema once at startup
SENTRY_PROMPT_PATH = PROJECT_ROOT / "sentry_prompt.md"
SCHEMA_PATH = PROJECT_ROOT / "schema.md"

def _load_text_file(path: Path) -> str:
    """Read a text file and return its contents, or empty string if missing."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

SENTRY_PROMPT_TEMPLATE = _load_text_file(SENTRY_PROMPT_PATH)
SCHEMA_TEXT = _load_text_file(SCHEMA_PATH)

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
# Sentry — Layer 1 helper functions (programmatic checks)
# ---------------------------------------------------------------------------

def _get_db_tables_and_columns() -> dict[str, list[str]]:
    """
    Query the live database to get all table names and their column names.
    Returns a dict: {"Album": ["AlbumId", "Title", "ArtistId"], ...}
    """
    conn = get_connection()
    try:
        tables_cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        result = {}
        for row in tables_cursor.fetchall():
            table_name = row["name"]
            col_cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
            result[table_name] = [col["name"] for col in col_cursor.fetchall()]
        return result
    finally:
        conn.close()


def _get_db_foreign_keys() -> list[dict]:
    """
    Get all foreign key relationships from the live database.
    Returns a list of dicts:
      [{"from_table": "Album", "from_col": "ArtistId",
        "to_table": "Artist", "to_col": "ArtistId"}, ...]
    """
    conn = get_connection()
    try:
        tables_cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        fks = []
        for row in tables_cursor.fetchall():
            table_name = row["name"]
            fk_cursor = conn.execute(f"PRAGMA foreign_key_list([{table_name}])")
            for fk in fk_cursor.fetchall():
                fks.append({
                    "from_table": table_name,
                    "from_col": fk["from"],
                    "to_table": fk["table"],
                    "to_col": fk["to"],
                })
        return fks
    finally:
        conn.close()


def _check_syntax(sql: str) -> list[dict]:
    """
    Layer 1 check: Verify SQL syntax by running EXPLAIN on it.
    Returns a list of issues (empty if syntax is valid).
    """
    issues = []
    conn = get_connection()
    try:
        conn.execute(f"EXPLAIN {sql}")
    except Exception as e:
        issues.append({
            "severity": "error",
            "rule": "sql_convention",
            "message": f"SQL syntax error: {e}",
        })
    finally:
        conn.close()
    return issues


def _check_schema(sql: str) -> list[dict]:
    """
    Layer 1 check: Parse SQL with sqlglot and verify all table/column
    names exist in the actual database schema.
    """
    issues = []
    db_schema = _get_db_tables_and_columns()

    # Normalize for case-insensitive lookup
    schema_lower = {t.lower(): {c.lower() for c in cols} for t, cols in db_schema.items()}
    table_name_map = {t.lower(): t for t in db_schema}  # lowercase → actual name

    try:
        parsed = sqlglot.parse(sql, dialect="sqlite")
    except sqlglot.errors.ErrorLevel:
        # If sqlglot can't parse it, syntax check already caught it
        return issues

    for statement in parsed:
        if statement is None:
            continue

        # Collect CTE names so we don't flag them as missing tables
        cte_names: set[str] = set()
        for cte_node in statement.find_all(sqlglot.exp.CTE):
            cte_names.add(cte_node.alias.lower())

        # Collect output aliases (SELECT ... AS alias) so we don't flag them
        output_aliases: set[str] = set()
        for alias_node in statement.find_all(sqlglot.exp.Alias):
            output_aliases.add(alias_node.alias.lower())

        # Extract table names referenced in the SQL
        for table in statement.find_all(sqlglot.exp.Table):
            table_name = table.name
            if table_name.lower() in cte_names:
                continue
            if table_name.lower() not in schema_lower:
                issues.append({
                    "severity": "error",
                    "rule": "schema",
                    "message": f"Table '{table_name}' does not exist in the database. "
                               f"Available tables: {', '.join(sorted(db_schema.keys()))}",
                })

        # Extract column references and check against known tables
        for column in statement.find_all(sqlglot.exp.Column):
            col_name = column.name
            col_table = column.table  # alias or table name, may be empty

            # Skip columns that match an output alias (e.g., ORDER BY TrackCount)
            if col_name.lower() in output_aliases:
                continue

            # If column is qualified with a table/alias, we can't easily
            # resolve aliases here, so only check unqualified columns
            # against ALL known columns across all tables.
            if not col_table:
                all_columns = set()
                for cols in schema_lower.values():
                    all_columns.update(cols)
                if col_name.lower() not in all_columns:
                    issues.append({
                        "severity": "error",
                        "rule": "schema",
                        "message": f"Column '{col_name}' not found in any table.",
                    })

    return issues


def _check_write_safety(sql: str) -> list[dict]:
    """
    Layer 1 check: Flag destructive operations without WHERE,
    and dangerous statements like DROP/TRUNCATE.
    """
    issues = []
    sql_upper = sql.upper().strip()

    # DROP / TRUNCATE are always flagged
    if sql_upper.startswith("DROP "):
        issues.append({
            "severity": "error",
            "rule": "write_safety",
            "message": "DROP statement detected. This is destructive and irreversible.",
        })
    if "TRUNCATE" in sql_upper:
        issues.append({
            "severity": "error",
            "rule": "write_safety",
            "message": "TRUNCATE detected. This deletes all rows and is irreversible.",
        })

    # UPDATE/DELETE without WHERE
    if sql_upper.startswith("UPDATE ") and " WHERE " not in sql_upper:
        issues.append({
            "severity": "error",
            "rule": "write_safety",
            "message": "UPDATE without WHERE clause — this would affect ALL rows.",
        })
    if sql_upper.startswith("DELETE ") and " WHERE " not in sql_upper:
        issues.append({
            "severity": "error",
            "rule": "write_safety",
            "message": "DELETE without WHERE clause — this would delete ALL rows.",
        })

    return issues


def _detect_ranking(sql: str, conversation_history: str) -> list[dict]:
    """
    Layer 1 check: Detect ranking patterns (ROW_NUMBER, RANK, DENSE_RANK,
    ORDER BY … LIMIT) and flag if conversation history doesn't show
    the mandatory clarification questions were asked.
    """
    issues = []
    sql_upper = sql.upper()

    has_ranking = any(fn in sql_upper for fn in [
        "ROW_NUMBER(", "RANK(", "DENSE_RANK(",
    ])
    has_order_limit = "ORDER BY" in sql_upper and "LIMIT" in sql_upper

    if not has_ranking and not has_order_limit:
        return issues  # No ranking pattern — nothing to check

    # Look for evidence of ranking clarification in conversation history
    # These are the key phrases from the mandatory questions
    clarification_signals = [
        "same position",
        "unique position",
        "tied",
        "ties",
        "tiebreaker",
        "skip ahead",
        "continue with the next number",
        "include all tied",
        "strict cutoff",
        "rank()",
        "dense_rank()",
        "row_number()",
        "quick answer",
        "don't want to decide",
    ]

    history_lower = conversation_history.lower()
    found_signal = any(signal in history_lower for signal in clarification_signals)

    if not found_signal:
        issues.append({
            "severity": "error",
            "rule": "missing_clarification",
            "message": (
                "The SQL uses a ranking/ordering pattern "
                f"({'window function' if has_ranking else 'ORDER BY … LIMIT'}) "
                "but the conversation history shows no evidence that the mandatory "
                "ranking/tie-handling clarification questions were asked. "
                "These questions MUST be asked before generating ranking SQL."
            ),
        })

    return issues


def _run_layer1_checks(sql: str, conversation_history: str) -> list[dict]:
    """Run all Layer 1 (programmatic) checks and return combined issues."""
    issues = []
    issues.extend(_check_syntax(sql))
    # Only run further checks if syntax is valid
    if not any(i["rule"] == "sql_convention" and "syntax error" in i["message"].lower()
               for i in issues):
        issues.extend(_check_schema(sql))
        issues.extend(_check_write_safety(sql))
        issues.extend(_detect_ranking(sql, conversation_history))
    return issues


# ---------------------------------------------------------------------------
# Sentry — Layer 2 (LLM semantic review)
# ---------------------------------------------------------------------------

def _run_layer2_review(
    sql: str,
    user_question: str,
    conversation_history: str,
    clarifications_given: str,
) -> dict:
    """
    Call the OpenAI API with the sentry prompt to get a semantic review.
    Returns the parsed JSON verdict, or an error dict if the call fails.
    """
    if not OPENAI_API_KEY:
        return {
            "skipped": True,
            "reason": "OPENAI_API_KEY not set — Layer 2 (LLM review) skipped.",
        }

    # Build the system prompt by injecting the schema into the template
    system_prompt = SENTRY_PROMPT_TEMPLATE.replace("{schema}", SCHEMA_TEXT)

    # Build the user message with all context the reviewer needs
    user_message = (
        f"## SQL to Review\n```sql\n{sql}\n```\n\n"
        f"## User's Original Question\n{user_question}\n\n"
        f"## Conversation History\n{conversation_history}\n\n"
    )
    if clarifications_given:
        user_message += f"## Clarifications Summary\n{clarifications_given}\n\n"

    user_message += (
        "Review the SQL against all 5 evaluation dimensions and return "
        "your JSON verdict. Remember: respond with ONLY a JSON object."
    )

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=SENTRY_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,  # Deterministic — we want consistent reviews
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "approved": False,
            "issues": [{"severity": "error", "rule": "semantic",
                        "message": "LLM reviewer returned invalid JSON."}],
            "missing_questions": [],
            "explanation": f"Raw LLM response could not be parsed: {raw[:500]}",
        }
    except Exception as e:
        return {
            "skipped": True,
            "reason": f"LLM review failed: {e}",
        }


# ---------------------------------------------------------------------------
# Tool 5: review_sql — sentry gate (must be called before query/execute)
# ---------------------------------------------------------------------------
@mcp.tool()
def review_sql(
    sql: str,
    user_question: str,
    conversation_history: str,
    clarifications_given: str = "",
) -> str:
    """
    Sentry review gate — validates SQL before execution. MUST be called
    before query() or execute(). Returns approval or rejection with issues.

    Args:
        sql: The SQL query to review.
        user_question: The original question the user asked.
        conversation_history: The relevant conversation leading up to the SQL —
            includes the agent's clarifying questions, user's answers, any
            follow-up questions the user added, and the agent's interpretation.
        clarifications_given: Optional structured summary of key decisions
            (e.g., "Ranking: RANK(), include ties, no cutoff").

    Returns:
        JSON with "approved" (bool), "issues" (list), "missing_questions" (list),
        and "explanation" (string).
    """
    # --- Layer 1: Programmatic checks ---
    layer1_issues = _run_layer1_checks(sql, conversation_history)

    # --- Layer 2: LLM semantic review (if enabled and API key is set) ---
    layer2_result = {}
    if SENTRY_ENABLED:
        layer2_result = _run_layer2_review(
            sql, user_question, conversation_history, clarifications_given
        )

    # --- Merge results ---
    # Start with Layer 1 issues
    all_issues = list(layer1_issues)
    missing_questions = []
    explanation_parts = []

    if layer2_result.get("skipped"):
        explanation_parts.append(f"Layer 2: {layer2_result['reason']}")
    else:
        # Merge Layer 2 issues (avoid exact duplicates by message)
        layer1_messages = {i["message"] for i in layer1_issues}
        for issue in layer2_result.get("issues", []):
            if issue.get("message") not in layer1_messages:
                all_issues.append(issue)

        missing_questions = layer2_result.get("missing_questions", [])

        if layer2_result.get("explanation"):
            explanation_parts.append(layer2_result["explanation"])

    # Determine approval: no error-severity issues = approved
    has_errors = any(i["severity"] == "error" for i in all_issues)

    if not explanation_parts:
        if has_errors:
            explanation_parts.append(
                f"Review found {sum(1 for i in all_issues if i['severity'] == 'error')} "
                f"blocking issue(s). Fix them before executing."
            )
        else:
            explanation_parts.append("All checks passed.")

    result = {
        "approved": not has_errors,
        "issues": all_issues,
        "missing_questions": missing_questions,
        "explanation": " ".join(explanation_parts),
    }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Entry point — start the MCP server
# ---------------------------------------------------------------------------
# This is what runs when VS Code launches the script.
# mcp.run() starts listening on stdin/stdout for JSON-RPC messages from Copilot.
# It blocks forever (until the process is killed when VS Code closes).

if __name__ == "__main__":
    mcp.run()
