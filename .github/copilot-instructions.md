# Copilot Instructions — SQL Generator (Chinook / SQLite)

## Project Overview

This project generates SQL queries against the **Chinook** digital music store database (SQLite).  
The single source of truth for all table/column definitions is [schema.md](../schema.md). **Always read it before generating SQL** — never guess names, types, or relationships.


## Core Rules

1. **Always reference `schema.md`** before generating any SQL. Never guess table or column names — verify them against the schema file.
2. **Use exact column names, data types, and relationships** as documented. Do not invent columns or tables that are not in the schema.
3. **Respect foreign key relationships.** When joining tables, use the documented FK → PK paths. Do not use implicit joins on columns that are not related by a foreign key.
4. **Target SQLite syntax.** All generated SQL must be valid SQLite. Use double quotes or square brackets for identifier quoting when needed.


## Schema Architecture (11 tables, 3 modules)

- **Music Catalog:** `Artist`, `Album`, `Track`, `Genre`, `MediaType`, `Playlist`, `PlaylistTrack` (M:N)
- **Customer Data:** `Customer`, `Employee` (self-referencing hierarchy via ReportsTo)
- **Sales:** `Invoice`, `InvoiceLine`

Key structural patterns:
- M:N relationship between playlists and tracks uses `PlaylistTrack` junction table with **composite PK**
- `Employee.ReportsTo` is a **self-referencing FK** for the management hierarchy
- Address fields are **denormalized** directly on `Customer`, `Employee`, and `Invoice` (no separate address table)
- `InvoiceLine` connects sales to the music catalog — it's the bridge between Sales and Music Catalog modules

## Common Multi-Hop Join Paths

| From → To | Path |
|-----------|------|
| Customer → Track | `Customer → Invoice → InvoiceLine → Track` |
| Customer → Artist | `Customer → Invoice → InvoiceLine → Track → Album → Artist` |
| Customer → Genre | `Customer → Invoice → InvoiceLine → Track → Genre` |
| Invoice → Track | `Invoice → InvoiceLine → Track` |
| Invoice → Artist | `Invoice → InvoiceLine → Track → Album → Artist` |
| Track → Artist | `Track → Album → Artist` |
| Track → Playlist | `Track → PlaylistTrack → Playlist` |
| Employee → Customer | `Employee → Customer` (via SupportRepId) |
| Employee → Employee | `Employee → Employee` (via ReportsTo, self-join) |

## SQL Conventions

- **SQLite syntax only.** Use double quotes or square brackets for identifier quoting when needed.
- Use exact column names, data types, and relationships as documented — do not invent columns or tables absent from the schema.
- Join only on documented FK → PK paths; do not use implicit joins on unrelated columns.
- Use explicit `JOIN … ON` (never comma joins). Qualify ambiguous columns with short aliases (`t` for `Track`, `c` for `Customer`, `i` for `Invoice`).
- Include only columns that exist in the schema. Respect `NOT NULL` constraints — never omit required columns in `INSERT`.
- Omit `Auto Increment` PKs and columns with suitable `Default` values in `INSERT` unless the user specifies values.
- Always add `WHERE` to `UPDATE`/`DELETE` unless a bulk operation is explicitly requested.
- Use `GROUP BY` with every non-aggregated `SELECT` column. Prefer `HAVING` for simple aggregate filters; use window functions for ranking/running totals.
- Add `ORDER BY` / `LIMIT` when the prompt implies sorting or subsetting ("top 10", "most recent").

## Response Rules

- **Answer exactly what was asked.** Do not run additional queries or add unsolicited analysis. If the user asks "which years", return the years — not a revenue breakdown. Let the user ask follow-up questions for more detail.
- **One query per question.** Execute a single SQL query that answers the user's question. Only run a second query if the first result is insufficient to answer what was asked.
- **Never guess or fabricate explanations for query results.** Only state what the returned data actually shows. Do not infer causes, assume data patterns, or use general knowledge about the database to explain why results look a certain way. If results are unexpected or sparse, note the observation and ask the user whether they'd like you to investigate further — do not run follow-up queries or speculate without explicit instructions.
- **Avoid Markdown pitfalls.** Do not use `~` as an approximation symbol — write "approximately" or "approx." instead. The `~` character triggers strikethrough formatting in Markdown.
- Present SQL in a ` ```sql ` fenced block. Add a brief explanation for complex queries.
- If the request is ambiguous, state your interpretation before generating SQL.
- If multiple approaches exist, generate the most straightforward one first; mention alternatives only if meaningfully different.
- If a requested column/table doesn't exist, say so and suggest the closest schema alternative.
- Warn before providing destructive statements (`DROP`, `TRUNCATE`, mass `DELETE`/`UPDATE` without `WHERE`).

## Schema Maintenance

When the user adds or modifies tables, update `schema.md` in the same format as existing entries (columns table, keys, indexes, references, module tag, status). Keep the status column (`✅`) current for every table.
