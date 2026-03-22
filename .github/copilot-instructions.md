# Copilot Instructions — SQL Generator (Sakila / MySQL)

## Project Overview

This project generates SQL queries against the **Sakila** sample database (MySQL).  
The single source of truth for all table/column definitions is [sqlgenerator/schema.md](../schema.md). **Always read it before generating SQL** — never guess names, types, or relationships.


## Core Rules

1. **Always reference `schema.md`** before generating any SQL. Never guess table or column names — verify them against the schema file.
2. **Use exact column names, data types, and relationships** as documented. Do not invent columns or tables that are not in the schema.
3. **Respect foreign key relationships.** When joining tables, use the documented FK → PK paths. Do not use implicit joins on columns that are not related by a foreign key.
4. **Target MySQL syntax.** All generated SQL must be valid MySQL. Use backticks for identifier quoting when needed.


## Schema Architecture (16 tables, 3 modules)

- **Film module:** `actor`, `category`, `language`, `film`, `film_actor` (M:N), `film_category` (M:N), `film_text` (fulltext mirror)
- **Customer Data module:** `country` → `city` → `address` → `customer`/`staff`/`store`
- **Business module:** `store`, `inventory`, `rental`, `payment`, `staff`

Key structural patterns:
- Many-to-many relationships use junction tables with **composite PKs** (`film_actor`, `film_category`)
- `film_text` is a trigger-synced copy of `film` for `FULLTEXT` search — never write to it directly
- Geographic hierarchy is always `country → city → address`; there is no direct `customer → city` FK

## Common Multi-Hop Join Paths

| From → To | Path |
|-----------|------|
| customer → city | `customer → address → city` |
| customer → country | `customer → address → city → country` |
| customer → film | `customer → rental → inventory → film` |
| payment → film | `payment → rental → inventory → film` |
| film → actor | `film → film_actor → actor` |
| film → category | `film → film_category → category` |
| film → store | `film → inventory → store` |
| staff → city | `staff → address → city` |
| store → city | `store → address → city` |

## SQL Conventions

- **MySQL syntax only.** Use backticks for identifier quoting when needed.
- Use exact column names, data types, and relationships as documented — do not invent columns or tables absent from the schema.
- Join only on documented FK → PK paths; do not use implicit joins on unrelated columns.
- Use explicit `JOIN … ON` (never comma joins). Qualify ambiguous columns with short aliases (`f` for `film`, `c` for `customer`).
- Include only columns that exist in the schema. Respect `NOT NULL` constraints — never omit required columns in `INSERT`.
- Omit `Auto Increment` PKs and columns with suitable `Default` values in `INSERT` unless the user specifies values.
- Always add `WHERE` to `UPDATE`/`DELETE` unless a bulk operation is explicitly requested.
- Use `GROUP BY` with every non-aggregated `SELECT` column. Prefer `HAVING` for simple aggregate filters; use window functions for ranking/running totals.
- Add `ORDER BY` / `LIMIT` when the prompt implies sorting or subsetting ("top 10", "most recent").

## Response Rules

- Present SQL in a ` ```sql ` fenced block. Add a brief explanation for complex queries.
- If the request is ambiguous, state your interpretation before generating SQL.
- If multiple approaches exist, generate the most straightforward one first; mention alternatives only if meaningfully different.
- If a requested column/table doesn't exist, say so and suggest the closest schema alternative.
- Warn before providing destructive statements (`DROP`, `TRUNCATE`, mass `DELETE`/`UPDATE` without `WHERE`).

## Schema Maintenance

When the user adds or modifies tables, update `schema.md` in the same format as existing entries (columns table, keys, indexes, references, module tag, status). Keep the status column (`✅`) current for every table.
