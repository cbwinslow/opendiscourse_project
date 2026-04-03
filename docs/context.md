# Context.md - OpenDiscourse Project State

## Current Status
**Date**: 2026-04-03
**Phase**: Phase 3 - GovInfo Ingestion (IN PROGRESS)
**Status**: GovInfo pipeline built (govinfo.py). Bill status and bill text parsing verified. Sitemap URLs fixed. Bill text extraction from `<legis-body>` works. CREC and FR sitemaps working.

---

## Recent Decisions

### 2026-04-03 - GovInfo Ingestion Pipeline Built
- **GovInfo API is unreliable**: REST API returns 500 errors on collections, date format errors on summaries. Using sitemap/bulk data downloads instead.
- **Sitemap URLs**: 
  - BILLSTATUS: `https://www.govinfo.gov/sitemap/bulkdata/BILLSTATUS/sitemapindex.xml` (96 sitemaps, organized by congress+type like `118hr`)
  - BILLS: `https://www.govinfo.gov/sitemap/BILLS_sitemap_index.xml` (34 sitemaps by year)
  - CREC: `https://www.govinfo.gov/sitemap/CREC_sitemap_index.xml` (33 sitemaps by year)
  - FR: `https://www.govinfo.gov/sitemap/FR_sitemap_index.xml` (91 sitemaps by year)
- **BILLSTATUS format**: Plain XML (not ZIP), no namespace. Structure: `<billStatus><bill><congress>118</congress><type>HR</type><number>1</number><title>...</title></bill></billStatus>`
- **Bill text format**: XML in ZIP files from GovInfo content URLs. Structure: `<bill><metadata>...<legis-body>...</legis-body></bill>`. Text extracted via `etree.tostring(method="text")`.
- **Bill text URL pattern**: `https://www.govinfo.gov/content/pkg/BILLS-{congress}{type}{number}{version}/xml/BILLS-{congress}{type}{number}{version}.xml`
- **Bill text parsing**: Regex `BILLS-(\d+)([a-z]+)(\d+)([a-z]+)` extracts congress, type, number, version from filename
- **Bill status ingestion**: Updates existing Bill records with titles, sponsors, latest actions from BILLSTATUS XML
- **Bill text ingestion**: Creates BillText records with full text content from `<legis-body>` element
- **CREC/FR ingestion**: Downloads ZIP packages, extracts XML content, stores in CongressionalRecord/FederalRegister tables
- **Bugs fixed in govinfo.py**:
  1. BILLSTATUS sitemap URL was wrong (used lowercase path, should be `bulkdata/BILLSTATUS/sitemapindex.xml`)
  2. Bill type filter was case-sensitive (URLs use lowercase `/hr/` not `/HR/`)
  3. Bill text parser looked for wrong XML element (`bill-text` → `legis-body`)
  4. Bill text filename extraction used `[-2]` (directory) instead of `[-1]` (filename)
  5. Bill status parser used namespace prefixes but XML has no namespace

### 2026-04-03 - GovInfo Ingestion Pipeline Built
- **GovInfo API is unreliable**: REST API returns 500 errors on collections, date format errors on summaries. Using sitemap/bulk data downloads instead.
- **Sitemap URLs**: 
  - BILLSTATUS: `https://www.govinfo.gov/sitemap/bulkdata/BILLSTATUS/sitemapindex.xml` (96 sitemaps, organized by congress+type like `118hr`)
  - BILLS: `https://www.govinfo.gov/sitemap/BILLS_sitemap_index.xml` (34 sitemaps by year)
  - CREC: `https://www.govinfo.gov/sitemap/CREC_sitemap_index.xml` (33 sitemaps by year)
  - FR: `https://www.govinfo.gov/sitemap/FR_sitemap_index.xml` (91 sitemaps by year)
- **BILLSTATUS format**: Plain XML (not ZIP), no namespace. Structure: `<billStatus><bill><congress>118</congress><type>HR</type><number>1</number><title>...</title></bill></billStatus>`
- **Bill text format**: XML in ZIP files from GovInfo content URLs. Structure: `<bill><metadata>...<legis-body>...</legis-body></bill>`. Text extracted via `etree.tostring(method="text")`.
- **Bill text URL pattern**: `https://www.govinfo.gov/content/pkg/BILLS-{congress}{type}{number}{version}/xml/BILLS-{congress}{type}{number}{version}.xml`
- **Bill text parsing**: Regex `BILLS-(\d+)([a-z]+)(\d+)([a-z]+)` extracts congress, type, number, version from filename
- **Bill status ingestion**: Updates existing Bill records with titles, sponsors, latest actions from BILLSTATUS XML
- **Bill text ingestion**: Creates BillText records with full text content from `<legis-body>` element
- **CREC/FR ingestion**: Downloads ZIP packages, extracts XML content, stores in CongressionalRecord/FederalRegister tables
- **Bugs fixed in govinfo.py**:
  1. BILLSTATUS sitemap URL was wrong (used lowercase path, should be `bulkdata/BILLSTATUS/sitemapindex.xml`)
  2. Bill type filter was case-sensitive (URLs use lowercase `/hr/` not `/HR/`)
  3. Bill text parser looked for wrong XML element (`bill-text` → `legis-body`)
  4. Bill text filename extraction used `[-2]` (directory) instead of `[-1]` (filename)
  5. Bill status parser used namespace prefixes but XML has no namespace

### 2026-04-03 - Real Ingestion Completed
- **Congress 118**: 20 congresses, 1,250 members, 818 committees, 19,242 bills = 21,330 total records
- **Congress 119**: 20 congresses, 1,250 members, 818 committees, 14,590 bills = 16,678 total records (5 bills failed due to null latestAction)
- **Bugs fixed during ingestion**:
  1. Congress API uses `startYear`/`endYear` not `startDate`/`endDate`
  2. Congress number derived from name ("118th Congress") not a numeric field: formula `(year - 1789) // 2 + 1`
  3. Members endpoint `/congress/{n}/member` returns 404 - use `/member` only
  4. Member `name` field is "Last, First" format, not separate firstName/lastName
  5. Member `chamber` is "House of Representatives" (25 chars) - normalized to "house"/"senate"/"joint"
  6. Committees use `systemCode` not URL for ID; no `congress` field in response
  7. `log_ingestion` had session binding bug with cached DataSource - fixed to query in same session
  8. Bills had duplicate `congress_gov_id` in batches - added dedup set
  9. Bills FK referenced `congresses.id` not `congress_number` - altered constraint
  10. Votes endpoint not available in v3 API - skipped
- **API keys added**: Congress.gov, GovInfo, FEC to `.env`

### 2026-04-03 - Project Initialization
- **Decision**: Created project structure at `/home/cbwinslow/workspace/opendiscourse/`
- **Rationale**: Workspace partition has 2.1TB available space, sufficient for 200-300GB estimated data
- **Alternatives considered**: Home directory (insufficient space), /workspace (doesn't exist)

### 2026-04-03 - Agent Guidelines Established
- **Decision**: Created strict agent rules in AGENTS.md
- **Key rules**:
  1. Always read context.md and AGENTS.md before acting
  2. Reuse existing code over creating new files
  3. Solve real problems, no cheap workarounds
  4. No task drift or scope expansion
  5. No hallucinations - verify before coding
  6. Use Letta memory before/after every task
  7. Follow file structure discipline
- **Rationale**: Prevent AI agent degradation over time (task drift, hallucinations, duplicate files)

### 2026-04-03 - Data Sources Researched
- **Congress.gov API**: Confirmed active, 920-star GitHub repo, 1000 req/hr rate limit
- **GovInfo API**: Confirmed active, official MCP server available
- **FEC API**: Confirmed active, free API key
- **OpenSecrets API**: Confirmed active, limited free tier
- **MCP Servers**: Found 4+ community MCP servers for Congress.gov data
- **Python packages**: `unitedstates/congress` (1k stars) is primary ingestion tool
- **Note**: ProPublica Congress API is **DEPRECATED** - do not use

### 2026-04-03 - Pagination Offset Fix
- **Issue**: The original `paginate()` method in `base.py` set `params[offset_key] = 0` once before the loop, but the offset was incremented AFTER yielding results. This meant the first request had offset=0, then offset was updated, but the NEXT request used the updated offset correctly. However, if the caller passed an initial offset in `params`, it was overwritten to 0.
- **Fix**: 
  1. Changed to `params = dict(params) if params else {}` to avoid mutating caller's dict
  2. Only set `params[offset_key] = 0` if the key is not already present (respects caller's initial offset)
  3. Added detailed debug logging for each page fetch showing offset/limit values
  4. Added `max_pages` safety valve parameter to prevent infinite loops
  5. Added logging for each pagination termination reason (no results, total reached, partial page, max pages)
- **Files changed**: `src/opendiscourse/ingestion/base.py`

### 2026-04-03 - Reserved Column Name Fix
- **Issue**: `IngestionLog.metadata` column name conflicts with SQLAlchemy's reserved `Base.metadata` attribute
- **Fix**: Renamed to `extra_metadata = Column("metadata", JSONB)` - Python attribute is `extra_metadata` but DB column stays `metadata`
- **Files changed**: `src/opendiscourse/models/metadata.py`, `src/opendiscourse/ingestion/base.py`

### 2026-04-03 - Missing Import Fix
- **Issue**: `campaign_finance.py` used `Text` column type but didn't import it from SQLAlchemy
- **Fix**: Added `Text` to the import line
- **Files changed**: `src/opendiscourse/models/campaign_finance.py`

### 2026-04-03 - Build Backend Fix
- **Issue**: `pyproject.toml` had `build-backend = "setuptools.backends._legacy:_Backend"` which doesn't exist
- **Fix**: Changed to `build-backend = "setuptools.build_meta"`
- **Files changed**: `pyproject.toml`

### 2026-04-03 - Database Setup
- **Database**: `opendiscourse` already existed on server
- **Extensions**: `pg_trgm` installed; `pgvector` not available on this PostgreSQL instance (needs separate install)
- **Migration**: `alembic upgrade head` created 54 tables (47 models + 7 additional)
- **Alembic revision**: `ecc1fda708e0`

### 2026-04-03 - Congress.gov Ingestion Pipeline
- **Decision**: Created `congress_gov.py` (502 lines) with full ingestion pipeline
- **Methods implemented**:
  - `ingest_congresses()` - All congress sessions
  - `ingest_members(congress_number)` - Members with pagination (250/page)
  - `ingest_member_details(bioguide_id)` - Single member detail fetch
  - `ingest_committees(congress_number)` - Committees with pagination (100/page)
  - `ingest_bills(congress_number, bill_type)` - Bills with pagination (250/page)
  - `ingest_bill_details(congress, type, number)` - Full bill: actions, cosponsors, subjects, summaries
  - `ingest_votes(congress_number)` - Roll call votes for Senate + House
  - `ingest_vote_details(congress, chamber, roll_number)` - Individual vote positions
  - `ingest(congress_number)` - Master method running full pipeline
- **Bulk load script**: `scripts/initial_bulk_load.py` with --congress, --source, --dry-run, --bill-types flags
- **Dry run test**: Passed for congress 118, verified all 6 endpoint paths
- **Pagination**: All endpoints use the fixed `paginate()` method with proper offset tracking
- **Upsert logic**: All methods use PostgreSQL ON CONFLICT DO UPDATE for idempotent ingestion

### 2026-04-03 - Congress.gov Ingestion Pipeline
- **Decision**: Created `congress_gov.py` (502 lines) with full ingestion pipeline
- **Methods implemented**:
  - `ingest_congresses()` - All congress sessions
  - `ingest_members(congress_number)` - Members with pagination (250/page)
  - `ingest_member_details(bioguide_id)` - Single member detail fetch
  - `ingest_committees(congress_number)` - Committees with pagination (100/page)
  - `ingest_bills(congress_number, bill_type)` - Bills with pagination (250/page)
  - `ingest_bill_details(congress, type, number)` - Full bill: actions, cosponsors, subjects, summaries
  - `ingest_votes(congress_number)` - Roll call votes for Senate + House
  - `ingest_vote_details(congress, chamber, roll_number)` - Individual vote positions
  - `ingest(congress_number)` - Master method running full pipeline
- **Bulk load script**: `scripts/initial_bulk_load.py` with --congress, --source, --dry-run, --bill-types flags
- **Dry run test**: Passed for congress 118, verified all 6 endpoint paths
- **Pagination**: All endpoints use the fixed `paginate()` method with proper offset tracking
- **Upsert logic**: All methods use PostgreSQL ON CONFLICT DO UPDATE for idempotent ingestion

---

## Open Issues

### Congress.gov API Stability
- **Issue**: API went dark in August 2025 per GovTech report
- **Impact**: High - primary data source
- **Mitigation**: Use GovInfo bulk data as fallback, verify API availability before Phase 2
- **Status**: Needs verification

### Large Data Volumes
- **Issue**: Estimated 200-300GB total storage needed
- **Impact**: Medium - workspace has 2.1TB available
- **Mitigation**: Sufficient space, but monitor growth
- **Status**: Acceptable for now

---

## Technical Debt
*(None yet - foundation just completed)*

---

## Phase 1 Completion Summary (2026-04-03)

### Files Created (29 total)
**Config/Infra**: pyproject.toml, docker-compose.yml, Dockerfile, .env.example, .env, alembic.ini
**Core**: __init__.py, __main__.py, config.py, database.py, celery_app.py
**Models** (5 files): congress.py (400 lines), campaign_finance.py (146 lines), lobbying.py, stock_disclosures.py, metadata.py
**Ingestion**: base.py (rate limiting, pagination, upsert, retry logic)
**Parsers** (4 files): xml_parser.py, json_parser.py, pdf_parser.py, csv_parser.py
**Utils** (3 files): rate_limiter.py, logging_config.py, helpers.py
**API**: api/main.py (FastAPI skeleton with lifespan)
**Alembic**: env.py, script.py.mako
**Docs**: AGENTS.md, project_summary.md, context.md, schema.md, PROJECT_PLAN.md

### Models Implemented
- Congress domain: 20 models (Congress, Chamber, Member, MemberTerm, Committee, CommitteeMembership, Bill, BillAction, BillCosponsor, BillCommittee, BillSubject, BillSummary, BillText, RelatedBill, Amendment, Vote, VotePosition, Nomination, NominationAction, Treaty, CommitteeReport, CongressionalRecord, FederalRegister, CFREntry)
- Campaign Finance: 7 models (FECCandidate, FECCommittee, FECCommitteeCandidate, FECContribution, FECDisbursement, FECIndependentExpenditure, FECFiling, FECTotal)
- Lobbying: 9 models (OpenSecretsLegislator, OpenSecretsCandidateSummary, OpenSecretsContributor, OpenSecretsIndustryContribution, OpenSecretsSectorContribution, LobbyingDisclosure, LobbyingIssue, LobbyingLobbyist, LobbyingContact)
- Stock Disclosures: 7 models (StockDisclosure, StockTransaction, FinancialDisclosure, FinancialPosition, FinancialAgreement, FinancialGift, FinancialTravel, FinancialAsset)
- Metadata: 4 models (DataSource, IngestionLog, APIRateLimit, DataQualityCheck)

---

## API Notes

### Congress.gov API
- Base URL: `https://api.congress.gov/v3/`
- Requires api.data.gov key
- Pagination: Uses `offset` and `limit` parameters
- Response format: JSON with nested `bills`, `members`, etc. arrays
- Coverage: 1973-present (varies by endpoint)

### GovInfo API
- Base URL: `https://api.govinfo.gov/`
- Same api.data.gov key as Congress.gov
- Bulk data available at `https://www.govinfo.gov/bulkdata/`
- XML and JSON endpoints available by adding `/xml` or `/json` to bulkdata URLs
- Official MCP server in public preview

### FEC API
- Base URL: `https://api.open.fec.gov/v1/`
- Free API key required
- No strict rate limit documented
- Bulk data available as CSV/ZIP files

### OpenSecrets API
- Base URL: `https://www.opensecrets.org/api/`
- Free API key, limited endpoints
- Method-based query parameters

---

## Key Dependencies to Install
- SQLAlchemy 2.0
- Alembic
- Celery + Redis
- FastAPI + uvicorn
- httpx
- lxml + xmltodict
- Polars
- Playwright
- LangChain MCP SDK
- pdfplumber (for financial disclosure PDFs)

---

## Database Configuration
- **Host**: localhost (existing PostgreSQL 16 instance)
- **Database**: `opendiscourse` (CREATED, 54 tables)
- **User**: `cbwinslow` (existing)
- **Extensions**: pg_trgm installed, pgvector NOT available
- **Alembic**: revision ecc1fda708e0
- **Virtual env**: `/home/cbwinslow/workspace/opendiscourse/.venv`

---

## Next Steps
1. ~~Create `pyproject.toml` with dependencies~~ DONE
2. ~~Set up `docker-compose.yml` for Redis (PostgreSQL already exists)~~ DONE
3. ~~Create SQLAlchemy models in `src/opendiscourse/models/`~~ DONE
4. ~~Set up Alembic migrations~~ DONE
5. ~~Create base ingestion framework~~ DONE
6. ~~Write initial bulk load scripts~~ DONE (base class + parsers)
7. ~~Install dependencies~~ DONE (venv with all deps)
8. ~~Create PostgreSQL database~~ DONE (opendiscourse with pg_trgm)
9. ~~Run initial migration~~ DONE (54 tables created)
10. ~~Fix pagination offset bug~~ DONE (offset properly tracked per loop iteration)
11. ~~Create Congress.gov ingestion pipeline~~ DONE (congress_gov.py - 327 lines)
12. ~~Create initial bulk load script~~ DONE (scripts/initial_bulk_load.py)
13. ~~Test dry run~~ DONE (congress 118 endpoints verified)
14. ~~Add API keys to `.env`~~ DONE
15. ~~Run real ingestion~~ DONE (Congress 118: 21,330 records, Congress 119: 16,678 records)
16. ~~Build GovInfo ingestion pipeline~~ DONE (govinfo.py - 778 lines, sitemap-based)
17. Run full GovInfo ingestion: bill status updates + bill text for Congress 118
18. Build Congressional Record ingestion (CREC) - sitemaps working, needs testing
19. Build Federal Register ingestion (FR) - sitemaps working, needs testing
20. Begin Phase 4: Campaign Finance (FEC API + OpenSecrets)
