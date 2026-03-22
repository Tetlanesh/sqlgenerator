# SQL Generator — Proof of Concept Project Plan

## Goal

Build a system where a user asks natural-language questions about data, and an AI agent:
1. Clarifies the question with follow-ups to avoid wasted tokens
2. Generates SQL against the loaded database
3. **Passes SQL through a sentry review gate** before execution
4. Executes the SQL via an MCP tool (only after sentry approval)
5. Optionally runs Python/pandas for deeper analysis
7. **Generates charts/visualizations** on request (bar, line, pie, scatter, etc.)
8. Returns the answer + exports results to a file (CSV / Markdown / Excel / PNG / PDF)

**Database:** SQLite (runs inside Python via built-in `sqlite3` — no external DB server needed).  
**Sample data:** TBD — will choose a suitable example dataset when we get to that step.  
**Design:** DB-agnostic — swapping the dataset = pointing at a different `.db` file.

---

## Architecture

```
User Question
    ↓
Copilot Agent (clarifies → generates SQL)
    ↓
MCP review_sql()  ← Sentry Gate (Layer 1: programmatic checks + Layer 2: LLM reviewer)
    ↓                         ↓
  APPROVED                 REJECTED → issues[] returned to Copilot
    ↓                         ↓
MCP query() / execute()    Copilot corrects SQL or asks user missing questions
    ↓                         ↓
Result                     Loop back to review_sql()
    ↓
┌─────────────────────────────────┐
│ What does the user want?        │
├──────────┬──────────┬───────────┤
│ Answer   │ Analysis │ Chart     │
│ (text)   │ (pandas) │ (visual)  │
├──────────┼──────────┼───────────┤
│ Format & │ Pivot /  │ MCP       │
│ respond  │ stats    │ generate_ │
│          │          │ chart()   │
└──────────┴──────────┴───────────┘
    ↓
Result → CSV / Markdown / Excel / PNG / PDF
```

### Sentry Review — Two Layers

| Layer | What | How | Catches |
|-------|------|-----|--------|
| **Layer 1 — Programmatic** | Deterministic checks inside `review_sql()` | SQL parsing (sqlglot), `EXPLAIN`, DB metadata queries | Wrong table/column names, bad joins, syntax errors, missing WHERE on writes, GROUP BY violations, ranking without clarification |
| **Layer 2 — LLM Reviewer** | A second AI agent reviewing the SQL semantically | OpenAI API call with sentry_prompt.md as system context | SQL that is valid but doesn't answer the question, instruction rules not followed, missing user clarifications |

---

## Components to Install / Build

### 1. Python Environment (uv)

**File:** `pyproject.toml`

| Package | Purpose |
|---------|--------|
| `python >=3.11` | Runtime |
| `pandas` | DataFrames, aggregation, pivots |
| `sqlite3` (stdlib) | Python ↔ SQLite connectivity (no install needed) |
| `openpyxl` | Excel (.xlsx) export |
| `tabulate` | Pretty Markdown table rendering |
| `numpy` | Numerical operations |
| `mcp[cli]` | MCP SDK for building the server |
| `python-dotenv` | Load `.env` for DB credentials |
| `sqlglot` | SQL parser — extracts tables, columns, join paths from SQL for programmatic validation (Layer 1) |
| `openai` | OpenAI API SDK — powers the LLM-based sentry reviewer (Layer 2) |
| `matplotlib` | Chart rendering engine — bar, line, pie, scatter, horizontal bar |
| `seaborn` | Statistical visualization — builds on matplotlib with better defaults and styles |

**Setup:**
```bash
# Install uv (if not already installed)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create venv and install all deps in one step
uv sync
```

### 2. MCP Server for SQLite (Python)

**File:** `mcp_sql_server.py`

A Python-based MCP server using the `mcp` SDK that exposes tools to Copilot.  
Uses built-in `sqlite3` — DB-agnostic design so swapping the `.db` file is trivial:

| Tool | Input | Output | Purpose |
|------|-------|--------|---------|
| `query` | SQL string | JSON rows + column names | Execute SELECT queries |
| `execute` | SQL string | Affected row count | Run INSERT/UPDATE/DELETE |
| `list_tables` | — | JSON array of table names | Show all tables in DB |
| `describe_table` | Table name | Column definitions | Quick schema lookup |
| `review_sql` | SQL + full conversation context (see below) | Approval or rejection with issues | **Sentry gate** — must be called before `query()`/`execute()` |
| `generate_chart` | SQL + chart type + labels + output format | File path to saved chart image | Generate a visualization from query results (see below) |

**`review_sql` input parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | yes | The SQL query to review |
| `user_question` | string | yes | The **original** question the user asked |
| `conversation_history` | string | yes | The relevant conversation leading up to the SQL — includes: the agent's clarifying questions, the user's answers, any follow-up questions the user added, and the agent's stated interpretation. This is what the sentry uses to verify the agent asked the right questions and incorporated the answers correctly. |
| `clarifications_given` | string | no | Optional structured summary of key decisions made (e.g., "Ranking: RANK(), include ties, no cutoff"). Helps Layer 2 do a quick check without parsing the full conversation. |

**`generate_chart` input parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | yes | The SQL query to run. Results become the chart's data source. |
| `chart_type` | string | yes | One of: `bar`, `barh`, `line`, `pie`, `scatter`. |
| `x_column` | string | yes | Column name from the SQL results to use as the X axis (or pie labels). |
| `y_column` | string | yes | Column name from the SQL results to use as the Y axis (or pie values). |
| `title` | string | no | Chart title. Defaults to empty. |
| `x_label` | string | no | Custom X-axis label. Defaults to the column name. |
| `y_label` | string | no | Custom Y-axis label. Defaults to the column name. |
| `output_format` | string | no | `png` (default) or `pdf`. |
| `style` | string | no | Seaborn style theme: `whitegrid` (default), `darkgrid`, `white`, `dark`, `ticks`. |
| `color_palette` | string | no | Seaborn palette name: `deep` (default), `muted`, `pastel`, `bright`, `dark`, `colorblind`. |
| `figsize_width` | number | no | Figure width in inches. Default: 10. |
| `figsize_height` | number | no | Figure height in inches. Default: 6. |
| `limit` | number | no | Max rows to plot (to keep charts readable). Default: no limit. |
| `sort_by_value` | boolean | no | Sort data by Y values before plotting. Default: false. |

**`generate_chart` return value:** JSON string with:
- `file_path` — absolute path to the saved chart image
- `row_count` — number of data points plotted
- `chart_type` — the chart type used
- `message` — human-readable summary

**Chart generation workflow:**
1. Runs the SQL via the existing `query()` pipeline (sentry review should happen before calling `generate_chart`)
2. Loads results into a pandas DataFrame
3. Applies optional sorting/limiting
4. Renders chart with matplotlib + seaborn styling
5. Saves to `output/charts/` with a timestamped filename
6. Returns the file path for the agent to display or reference

### 3. VS Code MCP Registration

**File:** `.vscode/mcp.json`

Registers the MCP SQL server so Copilot can call it. Will point to the uv-managed venv running `mcp_sql_server.py`.

### 4. Sample Database (deferred)

SQLite `.db` file — will pick a suitable example dataset later.  
The MCP server reads the DB path from `.env`:
```env
DB_PATH=data/sample.db
```
Swapping datasets = drop a new `.db` file and update the path.

### 5. Export / Analysis Scripts

| File | Purpose |
|------|---------|
| `scripts/export_results.py` | Convert query results → CSV, Markdown table, or Excel (.xlsx) |
| `scripts/analyze.py` | Pandas helper — pivots, stats, groupings beyond what SQL does easily |
| `output/` | Directory for generated result files |

### 6. Sentry Review Agent

**Files:**
- `mcp_sql_server.py` — the `review_sql()` tool lives alongside the other MCP tools
- `sentry_prompt.md` — system prompt for the LLM reviewer (loaded at runtime)

#### Layer 1 — Programmatic Checks (inside `review_sql()`)

Automated, deterministic validation using `sqlglot` + SQLite metadata:

| Check | Implementation | Catches |
|-------|---------------|--------|
| Schema validation | Parse SQL with sqlglot → extract table/column names → verify against `PRAGMA table_info()` | Hallucinated columns, typos |
| Syntax validation | Run `EXPLAIN {sql}` via SQLite (no execution) | Malformed SQL |
| FK join validation | Extract JOIN pairs from AST → compare against `PRAGMA foreign_key_list()` | Undocumented / implicit joins |
| Write safety | Detect `UPDATE`/`DELETE` without `WHERE`, `DROP`, `TRUNCATE` | Destructive mistakes |
| GROUP BY audit | Compare non-aggregated SELECT columns against GROUP BY list | Missing grouping columns |
| Ranking detection | Scan for `ROW_NUMBER`/`RANK`/`DENSE_RANK`/`ORDER BY…LIMIT` patterns | Ranking rules skipped without clarification |

#### Layer 2 — LLM Semantic Review (OpenAI API call)

A second AI agent that reviews the SQL **in its full conversational context**. The sentry receives:
- The SQL query
- The user's original question
- The full conversation history (agent questions → user answers → follow-ups)
- An optional structured summary of key decisions

The system prompt (`sentry_prompt.md`) also loads:
- All rules from `copilot-instructions.md`
- The full schema from `schema.md`

The LLM reviewer evaluates **five** dimensions:
1. **Did the agent ask all required clarification questions?** (e.g., ranking/ties questions when the query involves top-N, ambiguity resolution)
2. **Did the agent correctly incorporate the user's answers into the SQL?** (e.g., user said DENSE_RANK but agent used ROW_NUMBER)
3. **Does the SQL correctly answer the user's question?** (semantic correctness — the SQL may be valid but answer the wrong thing)
4. **Were all instruction rules followed?** (SQL conventions, response rules, schema usage)
5. **Are there missing follow-up questions the user asked that the agent ignored or misunderstood?**

Returns a structured JSON verdict:
```json
{
  "approved": false,
  "issues": [
    {"severity": "error", "rule": "missing_clarification", "message": "Query uses ORDER BY … LIMIT 10 but the conversation shows no ranking/tie-handling questions were asked."},
    {"severity": "error", "rule": "answer_ignored", "message": "User said 'include all ties' but query uses ROW_NUMBER() which forces unique positions."},
    {"severity": "warning", "rule": "semantic", "message": "User asked about 'region' but query filters by BillingCountry — confirm this is what the user meant."}
  ],
  "missing_questions": [
    "Ask user: Did you mean country when you said 'region'?",
    "Ask user: The query involves a top-10 ranking — how should ties be handled?"
  ],
  "explanation": "The agent skipped the mandatory ranking clarification questions. Additionally, the user's follow-up about 'region' was interpreted as country without confirmation."
}
```

**Issue severity levels:**
- `error` — **blocking** — the SQL must not be executed until this is resolved
- `warning` — **non-blocking** — the SQL can run, but the agent should mention the caveat to the user

#### Environment Variables (`.env`)

```env
DB_PATH=data/chinook.db
OPENAI_API_KEY=sk-...           # Required for Layer 2 LLM review
SENTRY_MODEL=gpt-4o-mini        # Model for the reviewer (cost-efficient default)
SENTRY_ENABLED=true             # Set to false to skip LLM review (Layer 1 still runs)
```

### 7. Updated Copilot Instructions

**File:** `.github/copilot-instructions.md` (extend existing)

Add sections for:
- **Sentry Review — MANDATORY** — `review_sql()` must be called before every `query()`/`execute()`. The agent must pass (1) the SQL, (2) the user's original question, (3) the full relevant conversation history including all clarifying Q&A and user follow-ups, and (4) an optional decision summary. If rejected, Copilot must fix issues or ask the user the missing questions before retrying. Never bypass.
- **Clarification workflow** — agent must ask 1–2 follow-up questions before generating SQL (time range, filters, grouping preferences)
- **Tool usage** — when to use the MCP `query` tool vs. Python analysis
- **Export rules** — always save results to `output/` and tell the user the file path
- **Chart generation** — when the user asks for a visualization, chart, or graph, the agent should use `generate_chart()` with appropriate parameters

### 8. Analytics — Chart Generation

**File:** `mcp_sql_server.py` (new tool: `generate_chart`)

Generate visual charts from SQL query results using matplotlib + seaborn.

#### Supported Chart Types

| Type | Best For | Example Use Case |
|------|----------|-----------------|
| `bar` | Comparing categories | Revenue by country, tracks per genre |
| `barh` | Categories with long labels | Top artists by track count |
| `line` | Trends over time | Monthly invoice totals |
| `pie` | Part-of-whole composition | Genre distribution, market share |
| `scatter` | Correlation between two numeric values | Track duration vs. price |

#### Design Decisions

- **SQL runs inside the tool** — `generate_chart()` executes the SQL itself (via the existing `query()` path) and builds the chart from the results. The agent doesn't need to run the query separately and pass raw data.
- **Sentry review first** — the agent should call `review_sql()` before `generate_chart()`, since the chart tool runs the SQL internally.
- **Output directory** — charts save to `output/charts/` with timestamped filenames (e.g., `chart_20260322_153045.png`).
- **Sensible defaults** — seaborn `whitegrid` style, `deep` palette, 10x6 figure size. All overridable.
- **Readability guardrails** — if the query returns many rows, the agent can use `limit` and `sort_by_value` to keep charts clean. Label rotation is applied automatically for long category names.
- **Two output formats** — PNG (default, for quick viewing) and PDF (for print/export).

#### Dependencies

| Package | Purpose |
|---------|---------|
| `matplotlib` | Core chart rendering engine |
| `seaborn` | Statistical visualization layer — cleaner defaults, richer color palettes |
| `pandas` | Already in project — loads SQL results into DataFrame for chart data |

---

## Project File Structure (target)

```
sqlgenerator/
├── .env                          # DB path + API keys (gitignored)
├── .gitignore                    # .env, output/, data/, __pycache__, .venv/
├── pyproject.toml                # Project metadata + dependencies (uv)
├── uv.lock                       # Lockfile (auto-generated by uv sync)
├── schema.md                     # DB schema reference (existing)
├── mcp_sql_server.py             # MCP server: query/execute/describe/review_sql/generate_chart
├── sentry_prompt.md              # System prompt for the LLM sentry reviewer
├── README.md                     # Project documentation
├── data/
│   └── chinook.db                # SQLite database file (gitignored — see README for download)
├── .vscode/
│   └── mcp.json                  # MCP server registration for Copilot
├── .github/
│   └── copilot-instructions.md   # Agent behavior rules (existing, to extend)
├── tests/
│   ├── test_db.py                # Database connectivity tests
│   ├── test_sentry.py            # Layer 1 + Layer 2 sentry tests
│   ├── test_sentry_full.py       # Combined review_sql() test
│   └── test_cte.py               # CTE false-positive regression test
├── scripts/
│   ├── export_results.py         # Result → CSV / Markdown / Excel
│   └── analyze.py                # Pandas analysis helpers
└── output/                       # Generated files (gitignored)
    └── charts/                   # Chart images (PNG/PDF)
```

---

## Agent Workflow (runtime)

1. **User asks a question** about the data
2. **Agent asks 1–2 clarifying questions** (time range? specific store? grouping?) to ensure precision
3. **Agent generates SQL** using `schema.md` as the source of truth
4. **Agent calls MCP `review_sql` tool** — passes SQL + original user question + full conversation history (clarifying Q&A, follow-ups, stated interpretations) + optional decision summary
5. **Sentry Layer 1 (programmatic)** runs deterministic checks (schema, syntax, joins, write safety, ranking)
6. **Sentry Layer 2 (LLM reviewer)** evaluates: Were the right questions asked? Were answers incorporated? Does the SQL match the question? Were rules followed? Were follow-ups addressed?
7. **Review result:**
   - ✅ `approved: true` → Agent proceeds to step 8
   - ❌ `approved: false` → Agent reads `issues[]` and either:
     - a. Fixes the SQL and re-submits to `review_sql()` (for correction requests)
     - b. Asks the user the missing clarification questions (for missing-question flags)
     - c. Loops back to step 4 after fixing/clarifying
8. **Agent calls MCP `query` / `execute` tool** to run the approved SQL
9. **Simple answer?** → Format directly, export to CSV/Markdown/Excel in `output/`
10. **Chart requested?** → Agent calls MCP `generate_chart()` with SQL + chart config → returns file path
11. **Complex analysis needed?** → Run Python/pandas on the result set (pivots, statistics, trends)
12. **Agent responds** with the answer + chart image + path to exported files

### Sentry Loop — Retry Limits

- Max **3 review attempts** per user question. If the SQL still fails review after 3 tries, the agent must present the remaining issues to the user and ask for guidance rather than looping forever.
- Each retry should address the specific `issues[]` from the previous rejection — not regenerate from scratch (unless the issues are fundamental).

---

## VS Code Extensions (optional, helpful)

| Extension | ID | Purpose |
|-----------|----|---------|
| SQLite Viewer | `alexcvzz.vscode-sqlite` | Browse the SQLite DB visually |
| Python | `ms-python.python` | Linting, debugging, env |
| Jupyter | `ms-toolsai.jupyter` | Interactive pandas analysis |

---

## Build Order

| # | Task | Depends On | Status |
|---|------|------------|--------|
| 1 | Create `pyproject.toml` + `uv sync` | — | ✅ |
| 2 | Build `mcp_sql_server.py` (query, execute, list_tables, describe_table) | 1 | ✅ |
| 3 | Create `.vscode/mcp.json` | 2 | ✅ |
| 4 | Pick sample dataset (Chinook) + place `.db` file | — | ✅ |
| 5 | Create `schema.md` | 4 | ✅ |
| 6 | Create `.github/copilot-instructions.md` | 5 | ✅ |
| 7 | Create `.env` + `.gitignore` | — | ✅ |
| 8 | **Add `sqlglot` + `openai` to `pyproject.toml`** + `uv sync` | 1 | ✅ |
| 9 | **Create `sentry_prompt.md`** — LLM reviewer system prompt | 6 | ✅ |
| 10 | **Build `review_sql()` tool** — Layer 1 programmatic checks + Layer 2 LLM review | 2, 8, 9 | ✅ |
| 11 | **Update `.github/copilot-instructions.md`** — add mandatory sentry review section | 6, 10 | ✅ |
| 12 | **Update `.env`** — add `OPENAI_API_KEY`, `SENTRY_MODEL`, `SENTRY_ENABLED` | 7 | ✅ |
| 13 | **Test `review_sql()` tool** — end-to-end sentry validation | 8–12 | ✅ |
| 14 | **Add `matplotlib` + `seaborn` to `pyproject.toml`** + `uv sync` | 1 | ⬜ |
| 15 | **Build `generate_chart()` tool** in `mcp_sql_server.py` | 2, 14 | ⬜ |
| 16 | **Update `.github/copilot-instructions.md`** — add chart generation section | 11, 15 | ⬜ |
| 17 | **Update `README.md`** — document chart feature | 15 | ⬜ |
| 18 | **Test `generate_chart()` tool** — end-to-end chart generation | 14–16 | ⬜ |
| 19 | Create `scripts/export_results.py` | 1 | ⬜ (deferred) |
| 20 | Create `scripts/analyze.py` | 1 | ⬜ (deferred) |
