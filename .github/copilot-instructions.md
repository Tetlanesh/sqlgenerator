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

## Ranking & Ties Clarification

### ⛔ MANDATORY — DO NOT SKIP

**This section is a hard gate.** You **MUST complete ALL applicable clarification questions below and receive the user's answers BEFORE writing, generating, or executing ANY SQL** that involves ranking, ordering, or picking "top N" / "bottom N" items. This applies to every ranking dimension in the query (e.g., if a query ranks both cities and customers, each dimension must be clarified separately).

**Violation check:** If you find yourself writing a `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `ORDER BY … LIMIT`, or any ranking/filtering logic **before** the user has answered all required questions below — **STOP immediately**, discard the draft, and ask the missing questions first.

Ask the user the following (skip only questions the user has **explicitly already answered** in the current conversation):

1. **"If several items share the same value, should they all count as the same position (e.g., two items tied for 1st place are both #1), or should each item get its own unique position number?"**
   - Same position → use `RANK()` (or `DENSE_RANK()` — see next question).
   - Unique position → use `ROW_NUMBER()`, and warn the user that the pick among tied items is arbitrary / may change between runs.

2. **(Only if the user chose "same position") "When there's a tie, should the next position skip ahead (e.g., two #1s → next is #3) or continue with the next number (e.g., two #1s → next is #2)?"**
   - Skip ahead → `RANK()`
   - Continue → `DENSE_RANK()`

3. **"If there's a tie and you only want a fixed number of results, should I include all tied items (even if that gives more rows than the number you asked for) or cut off strictly at that number?"**
   - Include all tied → filter on the rank value (e.g., `WHERE rnk <= 5`); row count may exceed 5.
   - Strict cutoff → apply a secondary sort or `LIMIT` to cap the count.

4. **(REQUIRED if the user chose strict cutoff OR unique position / `ROW_NUMBER()`) "When items are tied, is there a tiebreaker you'd like me to use to decide their order — for example alphabetical name, most recent date, etc.?"**
   - If yes → add the tiebreaker to the `ORDER BY` inside the window function.
   - If none → warn the user that the order among tied items will be arbitrary.
   - **You MUST ask this question whenever Q1 = unique position or Q3 = strict cutoff. Do NOT proceed to SQL generation without the user's answer.**

### Sequencing rule

Ask **all** applicable questions in a **single prompt** (batch them). Wait for user answers. Only then proceed to SQL generation. Do **not** interleave question-asking with SQL writing — the full Q&A must complete first.

**Default when the user wants a quick answer and doesn't want to decide:** use `RANK()` with all ties included (no cutoff), and note the choice in the explanation.

## Response Rules

- **Answer exactly what was asked.** Do not run additional queries or add unsolicited analysis. If the user asks "which years", return the years — not a revenue breakdown. Let the user ask follow-up questions for more detail.
- **One query per question.** Execute a single SQL query that answers the user's question. Only run a second query if the first result is insufficient to answer what was asked.
- **Never run verification or follow-up queries.** After executing a query and receiving results, present them immediately. Do not run additional queries to "verify", "double-check", "sanity-check", or "explore" the data — even if the result set is small, empty, or unexpected. If the results seem surprising, state the observation and let the user decide whether to investigate further.
- **Never guess or fabricate explanations for query results.** Only state what the returned data actually shows. Do not infer causes, assume data patterns, or use general knowledge about the database to explain why results look a certain way. If results are unexpected or sparse, note the observation and ask the user whether they'd like you to investigate further — do not run follow-up queries or speculate without explicit instructions.
- **Avoid Markdown pitfalls.** Do not use `~` as an approximation symbol — write "approximately" or "approx." instead. The `~` character triggers strikethrough formatting in Markdown.
- Present SQL in a ` ```sql ` fenced block. Add a brief explanation for complex queries.
- If the request is ambiguous, state your interpretation before generating SQL.
- If multiple approaches exist, generate the most straightforward one first; mention alternatives only if meaningfully different.
- If a requested column/table doesn't exist, say so and suggest the closest schema alternative.
- Warn before providing destructive statements (`DROP`, `TRUNCATE`, mass `DELETE`/`UPDATE` without `WHERE`).

## Chart Generation (`generate_chart` tool)

When the user asks for a chart, graph, plot, or visualization:

1. **Write a SELECT query** that returns the data needed for the chart — typically two columns (one for labels/X-axis, one for values/Y-axis).
2. **Run `review_sql()` first** to validate the query, then call `generate_chart()` with the reviewed SQL.
3. **Choose the right chart type** based on what the user asked or what fits the data:
   - `bar` — comparing categories (e.g., revenue by country, tracks by genre)
   - `barh` — horizontal bars, good when category labels are long
   - `line` — trends over time or ordered sequences
   - `pie` — proportional breakdowns (best with ≤ 8 slices)
   - `scatter` — correlation between two numeric columns
4. **Set `x_column` and `y_column`** to match the exact column names/aliases in the SELECT query.
5. **Use `sort_by_value: true`** when the user wants items ranked (e.g., "top genres by sales").
6. **Use `limit`** to cap the number of data points when plotting "top N" or when there are too many categories for a readable chart.
7. **Provide a descriptive `title`** that summarizes the chart (e.g., "Top 10 Genres by Track Count").
8. **Output format:** Default is PNG. Only use PDF if the user explicitly requests it.
9. **After the chart is generated**, tell the user where the file was saved (the path is in the tool's return value).

### Parameter defaults (override only when needed)

| Parameter | Default | Notes |
|-----------|---------|-------|
| `style` | `whitegrid` | Options: whitegrid, darkgrid, white, dark, ticks |
| `color_palette` | `deep` | Options: deep, muted, pastel, bright, dark, colorblind |
| `figsize_width` | `10.0` | Increase for charts with many categories |
| `figsize_height` | `6.0` | Increase for horizontal bar charts with many items |

### Important

- The SQL in `generate_chart` runs internally — do **not** execute it separately via `query()`.
- If the query involves ranking, the Ranking & Ties clarification rules still apply to the SQL you write for the chart.
- Keep chart SQL simple — only select the columns needed for plotting, with appropriate GROUP BY and ORDER BY.

## Schema Maintenance

When the user adds or modifies tables, update `schema.md` in the same format as existing entries (columns table, keys, indexes, references, module tag, status). Keep the status column (`✅`) current for every table.
