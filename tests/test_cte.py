"""Quick test: CTE names should NOT be flagged as missing tables."""
from mcp_sql_server import _check_schema

# Test 1: CTE query — "ranked" is a CTE, not a real table
sql = """
WITH ranked AS (
    SELECT c.FirstName, c.LastName, SUM(i.Total) AS TotalSpent,
           RANK() OVER (ORDER BY SUM(i.Total) DESC) AS rnk
    FROM Customer c
    JOIN Invoice i ON c.CustomerId = i.CustomerId
    GROUP BY c.FirstName, c.LastName
)
SELECT * FROM ranked WHERE rnk <= 5
"""
issues = _check_schema(sql)
print(f"Test 1 (CTE single): {len(issues)} issue(s)")
for i in issues:
    print(f"  [{i['severity']}] {i['rule']}: {i['message']}")

# Test 2: Multiple CTEs
sql2 = """
WITH customer_totals AS (
    SELECT CustomerId, SUM(Total) AS TotalSpent
    FROM Invoice
    GROUP BY CustomerId
),
ranked AS (
    SELECT c.FirstName, c.LastName, ct.TotalSpent,
           RANK() OVER (ORDER BY ct.TotalSpent DESC) AS rnk
    FROM Customer c
    JOIN customer_totals ct ON c.CustomerId = ct.CustomerId
)
SELECT * FROM ranked WHERE rnk <= 10
"""
issues2 = _check_schema(sql2)
print(f"Test 2 (CTE multiple): {len(issues2)} issue(s)")
for i in issues2:
    print(f"  [{i['severity']}] {i['rule']}: {i['message']}")

# Test 3: Real bad table should still be caught
sql3 = "SELECT * FROM NonExistentTable"
issues3 = _check_schema(sql3)
print(f"Test 3 (Bad table still caught): {len(issues3)} issue(s)")
for i in issues3:
    print(f"  [{i['severity']}] {i['rule']}: {i['message']}")
