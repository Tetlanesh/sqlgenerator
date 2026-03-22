# SQL Generator

AI-powered SQL query generator for the **Chinook** digital music store database (SQLite). Built as an MCP (Model Context Protocol) server that integrates with VS Code Copilot to generate, review, and execute SQL queries through natural language conversation.

## Features

- **Natural language to SQL** — Ask questions in plain English, get correct SQLite queries
- **MCP tools** — `query`, `execute`, `list_tables`, `describe_table`, `review_sql` exposed to Copilot
- **Two-layer sentry review** — Every SQL query is validated before execution:
  - **Layer 1 (Programmatic):** Syntax checking via `EXPLAIN`, schema validation via sqlglot AST parsing, write-safety guards (DROP/DELETE without WHERE), and ranking clarification enforcement
  - **Layer 2 (LLM Semantic):** OpenAI API call that reviews SQL against the full conversation context, checking whether clarification questions were asked, user answers were incorporated, and instruction rules were followed
- **Ranking & ties workflow** — Mandatory clarification questions for any top-N / bottom-N query, with decision-table enforcement in the sentry prompt
- **Schema-driven** — All SQL generation references `schema.md` as the single source of truth

## Project Structure

```
sqlgenerator/
├── mcp_sql_server.py      # MCP server — all tools + sentry logic
├── schema.md              # Database schema (11 tables, single source of truth)
├── sentry_prompt.md       # LLM reviewer system prompt (Layer 2)
├── extract_schema.py      # Utility to extract schema from the DB
├── pyproject.toml         # Python project config + dependencies
├── .env                   # API keys + config (gitignored)
├── data/
│   └── chinook.db         # SQLite database
├── tests/
│   ├── test_db.py         # Database connectivity tests
│   ├── test_sentry.py     # Layer 1 + Layer 2 sentry tests
│   ├── test_sentry_full.py# Combined review_sql() test
│   └── test_cte.py        # CTE false-positive regression test
├── .github/
│   └── copilot-instructions.md  # Rules for Copilot agent behavior
└── .vscode/
    └── mcp.json           # MCP server registration for VS Code
```

## Database

The **Chinook** database models a digital music store with 11 tables across 3 modules:

| Module | Tables |
|--------|--------|
| Music Catalog | Artist, Album, Track, Genre, MediaType, Playlist, PlaylistTrack |
| Customer Data | Customer, Employee |
| Sales | Invoice, InvoiceLine |

## Prerequisites

- **Python** >= 3.11
- **uv** — Python package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- **VS Code** with GitHub Copilot extension
- **OpenAI API key** (for Layer 2 sentry review — optional, Layer 1 works without it)

## Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/Tetlanesh/sqlgenerator.git
   cd sqlgenerator
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Configure environment:**

   Create a `.env` file in the project root:
   ```
   DB_PATH=data/chinook.db
   OPENAI_API_KEY=sk-your-key-here
   SENTRY_MODEL=gpt-4o-mini
   SENTRY_ENABLED=true
   ```

4. **Configure MCP server in VS Code:**

   The `.vscode/mcp.json` file registers the MCP server. Update the `command` path to point to your `uv` executable:
   ```json
   {
     "servers": {
       "sql-server": {
         "command": "/path/to/uv",
         "args": ["run", "python", "mcp_sql_server.py"],
         "cwd": "${workspaceFolder}"
       }
     }
   }
   ```

5. **Open in VS Code** — Copilot will automatically start the MCP server and expose the SQL tools.

## Usage

Open Copilot Chat in VS Code and ask questions about the Chinook database:

- *"How many customers are in each country?"*
- *"Which artists have the most tracks?"*
- *"Show me the top 5 customers by total spending"* — triggers the ranking clarification workflow

Copilot will generate SQL, pass it through the sentry review, and execute it only after approval.

## Running Tests

```bash
uv run python tests/test_sentry.py
uv run python tests/test_cte.py
uv run python tests/test_sentry_full.py
```

## Branches

- **master** — Base project (MCP server + schema + instructions)
- **sentry** — Adds the two-layer sentry review system

## Tech Stack

- **SQLite** — Database engine
- **FastMCP** (`mcp[cli]`) — MCP server framework
- **sqlglot** — SQL parser for AST-based schema validation
- **OpenAI API** (`gpt-4o-mini`) — LLM semantic review
- **python-dotenv** — Environment configuration
