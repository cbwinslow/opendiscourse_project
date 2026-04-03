# AGENTS.md - OpenDiscourse Agent Guidelines

## Project Overview

OpenDiscourse is a unified PostgreSQL database that ingests, normalizes, and correlates US government data from multiple sources: legislation, voting records, member information, campaign finance, congressional trading disclosures, and lobbying data.

**Location**: `/home/cbwinslow/workspace/opendiscourse/`

---

## CRITICAL RULES - READ FIRST

### 1. Read Context Before Acting
Before making ANY changes or creating ANY files:
1. Read this file (`AGENTS.md`) completely
2. Read `docs/context.md` for current project state
3. Read `docs/project_summary.md` for the master plan
4. Check existing files in the directory you plan to work in
5. Search the codebase for existing implementations

### 2. Reuse Over Create
- **ALWAYS** search for existing code before writing new code
- **ALWAYS** modify/edit/add to existing files rather than creating new ones
- **NEVER** create a new file if the functionality fits in an existing file
- **NEVER** duplicate functionality that already exists
- Use `grep` and `glob` to find existing implementations before writing anything

### 3. Solve The Real Problem
- **NEVER** create cheap workarounds or hacky solutions
- When you hit a problem, work hard to solve it the RIGHT way first
- Only consider workarounds after exhausting proper solutions
- If stuck, document the problem in `docs/context.md` under "Open Issues" and explain what was tried
- Do NOT silently switch approaches without documenting why

### 4. No Task Drift
- Stay focused on the specific task you were given
- Do NOT expand scope or add features not requested
- Do NOT refactor unrelated code "while you're at it"
- If you notice something that needs fixing outside your task, document it in `docs/context.md` under "Technical Debt" - do NOT fix it unless asked

### 5. No Hallucinations
- If you don't know something, say so - do NOT make up API endpoints, function signatures, or data structures
- Verify API endpoints exist before writing code against them
- Test imports before assuming packages are available
- When in doubt, read the actual source code or documentation

### 6. Memory Management (Letta)
- **BEFORE starting any task**: Search Letta memory for relevant context
- **AFTER completing any task**: Store results, decisions, and learnings in Letta memory
- Use the `letta_memory` skill for all memory operations
- Record: architectural decisions, API quirks discovered, bugs found, solutions implemented
- Use appropriate memory blocks: `project_state`, `technical_decisions`, `api_notes`, `known_issues`

### 7. File Structure Discipline
- Know where everything lives before creating anything
- Follow the existing directory structure exactly
- Follow naming conventions: `snake_case` for files, `PascalCase` for classes, `snake_case` for functions/variables
- One class per file for models; group related functions in module files

---

## Project Structure

```
opendiscourse/
├── AGENTS.md                    # This file - agent guidelines
├── docs/
│   ├── project_summary.md       # Master project plan and overview
│   ├── context.md               # Current project state, decisions, open issues
│   ├── schema.md                # Database schema documentation
│   └── api.md                   # API documentation
├── src/opendiscourse/
│   ├── __init__.py
│   ├── config.py                # Configuration management
│   ├── database.py              # Database connection/session
│   ├── models/                  # SQLAlchemy models
│   │   ├── congress.py          # Members, bills, votes, committees
│   │   ├── campaign_finance.py  # FEC data models
│   │   ├── lobbying.py          # OpenSecrets/lobbying models
│   │   ├── stock_disclosures.py # STOCK Act/financial disclosure models
│   │   └── metadata.py          # Ingestion logs, data sources
│   ├── ingestion/               # Data ingestion pipelines
│   │   ├── base.py              # Base ingestion class
│   │   ├── congress_gov.py      # Congress.gov API ingestion
│   │   ├── govinfo.py           # GovInfo API/bulk ingestion
│   │   ├── fec.py               # FEC API ingestion
│   │   ├── opensecrets.py       # OpenSecrets API ingestion
│   │   ├── stock_disclosures.py # Stock disclosure scraping
│   │   └── huggingface.py       # HuggingFace dataset ingestion
│   ├── parsers/                 # Data format parsers
│   │   ├── xml_parser.py
│   │   ├── json_parser.py
│   │   ├── pdf_parser.py
│   │   └── csv_parser.py
│   ├── validators/              # Data validation
│   ├── transformers/            # Data normalization
│   ├── api/                     # FastAPI REST API
│   │   ├── main.py
│   │   ├── routes/
│   │   └── schemas/
│   ├── mcp_server/              # MCP server for AI integration
│   │   └── server.py
│   └── utils/                   # Shared utilities
│       ├── rate_limiter.py
│       ├── logging_config.py
│       └── helpers.py
├── alembic/                     # Database migrations
├── scripts/                     # Standalone scripts
├── tests/                       # Test suite
├── notebooks/                   # Jupyter analysis notebooks
├── config/                      # Configuration files
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env
```

---

## Data Sources Reference

### Primary APIs
| Source | URL | Auth | Rate Limit |
|--------|-----|------|------------|
| Congress.gov | `https://api.congress.gov/v3/` | api.data.gov key | 1000/hr |
| GovInfo | `https://api.govinfo.gov/` | api.data.gov key | Varies |
| FEC | `https://api.open.fec.gov/` | API key (free) | Varies |
| OpenSecrets | `https://www.opensecrets.org/api/` | API key (free) | Limited |

### Bulk Data
| Source | URL | Format |
|--------|-----|--------|
| GovInfo Bulk | `https://www.govinfo.gov/bulkdata/` | XML, JSON |
| FEC Bulk | `https://www.fec.gov/data/browse-data/` | CSV, ZIP |
| OpenSecrets Bulk | `https://www.opensecrets.org/open-data/bulk-data` | CSV |

### Third-Party APIs
| Source | Description |
|--------|-------------|
| Finnhub | Congressional trading API |
| FMP | Congressional ownership APIs |
| Apify | STOCK Act scrapers |

### Key GitHub Repos
| Repo | Purpose |
|------|---------|
| `usgpo/bulk-data` | GovInfo bulk data guides |
| `usgpo/bill-status` | Bill status XML format |
| `usgpo/api` | GovInfo API + MCP server |
| `unitedstates/congress` | Python data collectors (1k stars) |
| `LibraryOfCongress/api.congress.gov` | Congress.gov API source |

### MCP Servers
| Repo | Language | Notes |
|------|----------|-------|
| `cyanheads/congressgov-mcp-server` | TypeScript | STDIO & Streamable HTTP |
| `amurshak/congressMCP` | Python | 91 ops in 6 tools |
| `bsmi021/mcp-congress_gov_server` | TypeScript | Hybrid approach |
| `nawagner/congress-mcp` | Python | Congress.gov API v3 |

---

## Technology Stack

- **Database**: PostgreSQL 16 + pgvector (existing server instance)
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Task Queue**: Celery + Redis
- **API**: FastAPI
- **MCP**: LangChain MCP SDK
- **HTTP**: httpx (async)
- **XML**: lxml + xmltodict
- **Data Processing**: Polars
- **Scraping**: Playwright
- **Deployment**: Docker Compose

---

## Development Workflow

1. **Check memory** - Search Letta for relevant context
2. **Read context** - Read `docs/context.md` for current state
3. **Search existing** - Use grep/glob to find existing code
4. **Implement** - Make minimal, focused changes
5. **Test** - Run relevant tests
6. **Document** - Update `docs/context.md` with decisions/changes
7. **Store memory** - Record results in Letta

---

## Database Schema Summary

See `docs/schema.md` for full schema. Core domains:
- **Congress**: members, bills, votes, committees, amendments, nominations
- **Campaign Finance**: FEC candidates, committees, contributions, disbursements
- **Lobbying**: OpenSecrets data, lobbying disclosures
- **Trading**: STOCK Act disclosures, financial disclosures
- **Metadata**: Ingestion logs, data sources, quality checks

---

## Implementation Phases

1. Foundation (Weeks 1-2)
2. Congress.gov Ingestion (Weeks 3-4)
3. GovInfo Ingestion (Weeks 5-6)
4. Campaign Finance (Weeks 7-8)
5. Trading Disclosures (Weeks 9-10)
6. API & MCP Server (Weeks 11-12)
7. Analysis & Visualization (Weeks 13-14)
8. Production Hardening (Weeks 15-16)

---

## Anti-Patterns to Avoid

- Creating new files when existing ones can be extended
- Adding dependencies without checking if existing ones suffice
- Hardcoding API keys or configuration
- Silent failures without logging
- Creating duplicate models or functions
- Skipping tests because "it's simple"
- Making assumptions about API responses without checking
- Ignoring rate limits
- Not handling pagination in API responses
- Creating workarounds without documenting the actual problem
