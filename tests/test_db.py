import sqlite3

conn = sqlite3.connect("data/chinook.db")
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cur.fetchall()
print(f"{len(tables)} tables:")
for t in tables:
    print(f"  {t[0]}")

# Quick row counts
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
    print(f"  {t[0]}: {count} rows")

conn.close()
