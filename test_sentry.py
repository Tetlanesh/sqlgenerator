"""
Test script for the sentry review_sql tool.
Tests both Layer 1 (programmatic checks) and Layer 2 (LLM review).

Run with:  uv run python test_sentry.py
"""

import json
import sys

# Import the helpers and tool directly from our MCP server module
from mcp_sql_server import (
    _check_syntax,
    _check_schema,
    _check_write_safety,
    _detect_ranking,
    _run_layer1_checks,
    _run_layer2_review,
    review_sql,
    SENTRY_ENABLED,
    OPENAI_API_KEY,
)


def header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def show_result(label: str, issues: list[dict]):
    if issues:
        print(f"  {label}: {len(issues)} issue(s)")
        for i in issues:
            print(f"    [{i['severity'].upper()}] {i['rule']}: {i['message']}")
    else:
        print(f"  {label}: ✅ No issues")


# ── Layer 1 Tests ──────────────────────────────────────────

header("LAYER 1 — Test 1: Valid SQL (should pass)")
issues = _run_layer1_checks(
    sql="SELECT c.FirstName, c.LastName, COUNT(i.InvoiceId) AS InvoiceCount "
        "FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId "
        "GROUP BY c.FirstName, c.LastName",
    conversation_history="User asked: how many invoices does each customer have?"
)
show_result("Layer 1", issues)

header("LAYER 1 — Test 2: Bad table name (should catch schema error)")
issues = _check_schema(
    "SELECT * FROM Customers"  # wrong — it's "Customer" not "Customers"
)
show_result("Schema check", issues)

header("LAYER 1 — Test 3: Bad column name (should catch schema error)")
issues = _check_schema(
    "SELECT FullName FROM Customer"  # "FullName" doesn't exist
)
show_result("Schema check", issues)

header("LAYER 1 — Test 4: DELETE without WHERE (should catch write safety)")
issues = _check_write_safety("DELETE FROM Invoice")
show_result("Write safety", issues)

header("LAYER 1 — Test 5: DROP TABLE (should catch write safety)")
issues = _check_write_safety("DROP TABLE Customer")
show_result("Write safety", issues)

header("LAYER 1 — Test 6: Syntax error (should catch)")
issues = _check_syntax("SELEC * FORM Customer")
show_result("Syntax check", issues)

header("LAYER 1 — Test 7: Ranking without clarification (should catch)")
issues = _detect_ranking(
    sql="SELECT Name, Total FROM Customer ORDER BY Total DESC LIMIT 10",
    conversation_history="User asked: who are the top 10 customers?"
)
show_result("Ranking check", issues)

header("LAYER 1 — Test 8: Ranking WITH clarification (should pass)")
issues = _detect_ranking(
    sql="SELECT Name, Total FROM Customer ORDER BY Total DESC LIMIT 10",
    conversation_history=(
        "User asked: who are the top 10 customers?\n"
        "Agent asked: If several customers share the same total, should they "
        "all count as the same position or unique position?\n"
        "User: same position, include all ties\n"
        "Agent: I'll use RANK() with all tied items included."
    )
)
show_result("Ranking check", issues)


# ── Layer 2 Test ───────────────────────────────────────────

header("LAYER 2 — LLM Semantic Review")
print(f"  SENTRY_ENABLED: {SENTRY_ENABLED}")
print(f"  OPENAI_API_KEY set: {'yes' if OPENAI_API_KEY else 'no'}")

if SENTRY_ENABLED and OPENAI_API_KEY:
    print("\n  Calling OpenAI API for semantic review...")
    result = _run_layer2_review(
        sql=(
            "SELECT c.FirstName, c.LastName, SUM(i.Total) AS TotalSpent "
            "FROM Customer c "
            "JOIN Invoice i ON c.CustomerId = i.CustomerId "
            "GROUP BY c.FirstName, c.LastName "
            "ORDER BY TotalSpent DESC "
            "LIMIT 5"
        ),
        user_question="Who are the top 5 customers by total spending?",
        conversation_history=(
            "User: Who are the top 5 customers by total spending?\n"
            "Agent: I need to clarify a few things about the ranking before "
            "generating SQL.\n"
            "Agent asked: If several customers share the same total, should "
            "they all count as the same position, or each get a unique number?\n"
            "User: Just give me a quick answer, I don't want to decide.\n"
            "Agent: OK, I'll use RANK() with all ties included and note "
            "that choice."
        ),
        clarifications_given=(
            "Ranking: user chose quick-answer default. Agent will use RANK() "
            "with all ties included (no cutoff)."
        ),
    )
    print(f"\n  LLM Response:")
    print(json.dumps(result, indent=4))
else:
    print("  ⚠ Skipping Layer 2 — API key not set or sentry disabled.")


# ── Full review_sql() Test ────────────────────────────────

header("FULL REVIEW — review_sql() (both layers combined)")
if SENTRY_ENABLED and OPENAI_API_KEY:
    print("  Calling review_sql() with both layers...")
    result_json = review_sql(
        sql=(
            "SELECT a.Name AS ArtistName, COUNT(t.TrackId) AS TrackCount "
            "FROM Artist a "
            "JOIN Album al ON a.ArtistId = al.ArtistId "
            "JOIN Track t ON al.AlbumId = t.AlbumId "
            "GROUP BY a.Name "
            "ORDER BY TrackCount DESC "
            "LIMIT 10"
        ),
        user_question="Which artists have the most tracks?",
        conversation_history=(
            "User: Which artists have the most tracks?\n"
            "Agent: Before I generate the query, I need to clarify the ranking.\n"
            "Agent asked: If several artists share the same track count, should "
            "they all count as the same position, or each get a unique number?\n"
            "User: Same position.\n"
            "Agent asked: Should the next position skip ahead (two #1s → next "
            "is #3) or continue (two #1s → next is #2)?\n"
            "User: Skip ahead.\n"
            "Agent asked: Should I include all tied items even if that gives "
            "more than 10 rows?\n"
            "User: Yes, include all ties.\n"
            "Agent: Got it — I'll use RANK() with all ties included."
        ),
        clarifications_given=(
            "Ranking: RANK(), include all ties, no strict cutoff. "
            "User confirmed skip-ahead numbering."
        ),
    )
    result = json.loads(result_json)
    print(f"\n  Approved: {result['approved']}")
    print(f"  Issues: {len(result['issues'])}")
    for i in result["issues"]:
        print(f"    [{i['severity'].upper()}] {i['rule']}: {i['message']}")
    if result["missing_questions"]:
        print(f"  Missing questions:")
        for q in result["missing_questions"]:
            print(f"    - {q}")
    print(f"  Explanation: {result['explanation']}")
else:
    print("  ⚠ Skipping full review — running Layer 1 only.")
    result_json = review_sql(
        sql="SELECT * FROM Customer WHERE Country = 'Canada'",
        user_question="Show me all Canadian customers",
        conversation_history="User: Show me all Canadian customers",
    )
    result = json.loads(result_json)
    print(f"\n  Approved: {result['approved']}")
    print(f"  Explanation: {result['explanation']}")

print(f"\n{'='*60}")
print("  All tests complete!")
print(f"{'='*60}\n")
