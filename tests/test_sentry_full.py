"""Quick test of the full review_sql() tool — both layers combined."""
import json
from mcp_sql_server import review_sql

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
        "Agent asked: Should the next position skip ahead (two #1s -> next "
        "is #3) or continue (two #1s -> next is #2)?\n"
        "User: Skip ahead.\n"
        "Agent asked: Should I include all tied items even if that gives "
        "more than 10 rows?\n"
        "User: Yes, include all ties.\n"
        "Agent: Got it - I will use RANK() with all ties included."
    ),
    clarifications_given=(
        "Ranking: RANK(), include all ties, no strict cutoff. "
        "User confirmed skip-ahead numbering."
    ),
)
result = json.loads(result_json)
print(f"Approved: {result['approved']}")
print(f"Issues: {len(result['issues'])}")
for i in result["issues"]:
    print(f"  [{i['severity'].upper()}] {i['rule']}: {i['message']}")
if result["missing_questions"]:
    print("Missing questions:")
    for q in result["missing_questions"]:
        print(f"  - {q}")
print(f"Explanation: {result['explanation']}")
