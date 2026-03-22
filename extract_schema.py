"""Extract full schema info from the Chinook SQLite database for documentation."""
import sqlite3
import json

conn = sqlite3.connect("data/chinook.db")
conn.row_factory = sqlite3.Row

# Get all tables
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()

for t in tables:
    tname = t["name"]
    print(f"\n### {tname}")
    
    # Columns
    cols = conn.execute(f"PRAGMA table_info([{tname}])").fetchall()
    print("| # | Key | Column | Data Type | Nullable | Default |")
    print("|---|-----|--------|-----------|----------|---------|")
    for c in cols:
        pk = "PK" if c["pk"] else ""
        nullable = "YES" if not c["notnull"] else "NO"
        default = c["dflt_value"] if c["dflt_value"] else "—"
        print(f"| {c['cid']+1} | {pk} | {c['name']} | {c['type']} | {nullable} | {default} |")
    
    # Foreign keys
    fks = conn.execute(f"PRAGMA foreign_key_list([{tname}])").fetchall()
    if fks:
        print(f"\n**Foreign Keys:**")
        for fk in fks:
            print(f"- {tname}.{fk['from']} → {fk['table']}.{fk['to']}")
    
    # Indexes
    indexes = conn.execute(f"PRAGMA index_list([{tname}])").fetchall()
    if indexes:
        print(f"\n**Indexes:**")
        for idx in indexes:
            idx_cols = conn.execute(f"PRAGMA index_info([{idx['name']}])").fetchall()
            col_names = ", ".join([ic["name"] for ic in idx_cols])
            unique = "UNIQUE" if idx["unique"] else ""
            print(f"- {idx['name']} ({col_names}) {unique}")
    
    # Row count
    count = conn.execute(f"SELECT COUNT(*) FROM [{tname}]").fetchone()[0]
    print(f"\n**Row count:** {count}")

conn.close()
