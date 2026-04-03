# OpenDiscourse - Project Summary

## Overview

OpenDiscourse is a unified PostgreSQL database that ingests, normalizes, and correlates US government data from multiple sources: legislation, voting records, member information, campaign finance, congressional trading disclosures, and lobbying data. Built with Python ingestion pipelines, MCP servers for AI integration, and a normalized schema enabling cross-domain analysis.

---

## Data Sources & APIs

### 1. Congress.gov API (Official - Library of Congress)
- **URL**: `https://api.congress.gov/v3/`
- **GitHub**: `LibraryOfCongress/api.congress.gov` (920 stars)
- **Auth**: API key required (free via api.data.gov)
- **Rate Limits**: 1000 requests/hour with key
- **Endpoints**: bills, members, committees, amendments, nominations, treaties, committee reports, congressional record, house communications
- **Coverage**: 1973-present (varies by endpoint)
- **Note**: API had outage in Aug 2025, verify availability

### 2. GovInfo API (Official - GPO)
- **URL**: `https://api.govinfo.gov/`
- **GitHub**: `usgpo/api`, `usgpo/bulk-data` (356 stars)
- **Auth**: API key via api.data.gov (same as Congress.gov)
- **Bulk Data Repository**: `https://www.govinfo.gov/bulkdata/`
  - Congressional Bill Text (113th Congress+), Bill Status (108th+), Bill Summaries (113th+)
  - Code of Federal Regulations (1996+), Federal Register (2000+)
  - Congressional Record, US Code, Public/Private Laws, Statutes at Large
  - Congressional Hearings, Committee Prints, Committee Reports
- **Formats**: XML, JSON, PDF
- **MCP Server**: Official GovInfo MCP available at `usgpo/api` repo

### 3. FEC Campaign Finance API
- **URL**: `https://api.open.fec.gov/developers/`
- **Auth**: API key required (free)
- **Endpoints**: candidates, committees, Schedule A (contributions), Schedule B (disbursements), Schedule C (loans), Schedule E (independent expenditures), filings, totals, elections
- **Bulk Data**: `https://www.fec.gov/data/browse-data/` - All filings in CSV/ZIP, historical data back to 1980

### 4. OpenSecrets API (NIMSP/CRP)
- **URL**: `https://www.opensecrets.org/api/`
- **Auth**: API key required (free, limited)
- **Endpoints**: candidate contributors, industry/sector contributions, lobbying data, outside spending, legislator info
- **Bulk Data**: `https://www.opensecrets.org/open-data/bulk-data`

### 5. Congressional Trading/Stock Disclosures
- **Primary Sources**:
  - Senate: `https://www.senate.gov/senators/financial-disclosures/`
  - House: `https://disclosures-clerk.house.gov/`
- **Third-Party APIs**:
  - **Apify**: `ryanclinton/congress-stock-tracker` - STOCK Act scraper
  - **Apify**: `johnvc/us-congress-financial-dis` - Financial disclosures
  - **Finnhub**: `/api/v1/insider/congressional-trading` - Congressional trading API
  - **Financial Modeling Prep**: Congressional ownership APIs
  - **FinBrain**: House/Senate trades datasets

### 6. Additional Data Sources
- Ballotpedia, Vote Smart, GovTrack.us, MapLight, Sunlight Foundation Archives, CQ Roll Call (paid)

---

## MCP Servers Available

| Repository | Language | Stars | Description |
|------------|----------|-------|-------------|
| `cyanheads/congressgov-mcp-server` | TypeScript | New | Bills, votes, members, committees. STDIO & Streamable HTTP |
| `amurshak/congressMCP` | Python | 27 | 91 operations consolidated into 6 tools |
| `bsmi021/mcp-congress_gov_server` | TypeScript | 7 | Hybrid approach to Congress.gov API v3 |
| `nawagner/congress-mcp` | Python | 2 | Access to official Congress.gov API v3 |
| `usgpo/api` (official) | - | - | GovInfo MCP server (public preview) |

---

## Python Packages & Tools

| Package | Description | Stars | Status |
|---------|-------------|-------|--------|
| `unitedstates/congress` | Bills, amendments, votes, nominations, committee meetings | 1042 | Active |
| `BICAM` (bicam-data/bicam) | Bulk Ingestion of Congressional Actions & Materials | 2 | Active |
| `python-congress` | ProPublica Congress API client | - | Deprecated (ProPublica API shut down) |

---

## Database Schema (40+ tables)

### Core Tables
- `congresses`, `chambers`, `members`, `member_terms`
- `committees`, `committee_memberships`
- `bills`, `bill_actions`, `bill_cosponsors`, `bill_committees`, `bill_subjects`, `bill_summaries`, `bill_texts`, `related_bills`
- `amendments`
- `votes`, `vote_positions`
- `nominations`, `nomination_actions`
- `treaties`, `committee_reports`
- `congressional_records`, `federal_register`, `cfr_entries`

### Campaign Finance Tables
- `fec_candidates`, `fec_committees`, `fec_committee_candidates`
- `fec_contributions` (Schedule A), `fec_disbursements` (Schedule B)
- `fec_independent_expenditures` (Schedule E)
- `fec_filings`, `fec_totals`

### Lobbying & OpenSecrets Tables
- `opensecrets_legislators`, `opensecrets_candidate_summaries`
- `opensecrets_contributors`, `opensecrets_industry_contributions`, `opensecrets_sector_contributions`
- `lobbying_disclosures`, `lobbying_issues`, `lobbying_lobbyists`, `lobbying_contacts`

### Stock/Trading Disclosure Tables
- `stock_disclosures`, `stock_transactions`
- `financial_disclosures`, `financial_positions`, `financial_agreements`, `financial_gifts`, `financial_travel`, `financial_assets`

### Metadata Tables
- `data_sources`, `ingestion_logs`, `api_rate_limits`, `data_quality_checks`

---

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Database | PostgreSQL 16 + pgvector | Already running on server, supports vector search |
| ORM | SQLAlchemy 2.0 | Industry standard, async support |
| Migrations | Alembic | SQLAlchemy companion |
| Task Queue | Celery + Redis | Mature, reliable, distributed |
| Scheduling | Celery Beat | Built-in periodic task support |
| API | FastAPI | Fast, async, auto-docs |
| MCP Server | LangChain MCP SDK | Standard MCP implementation |
| HTTP Client | httpx | Async, modern |
| XML Parsing | lxml + xmltodict | Fast, reliable |
| Data Processing | Polars | Faster than pandas for ETL |
| Web Scraping | Playwright | Modern, handles JS |
| Containerization | Docker Compose | Easy deployment |

---

## Implementation Phases (16 weeks)

1. **Phase 1: Foundation** (Weeks 1-2) - Repo, DB schema, models, Docker, base ingestion framework
2. **Phase 2: Congress.gov** (Weeks 3-4) - Members, bills, votes, committees, amendments
3. **Phase 3: GovInfo** (Weeks 5-6) - Bill text, Congressional Record, Federal Register, CFR
4. **Phase 4: Campaign Finance** (Weeks 7-8) - FEC API, OpenSecrets, lobbying
5. **Phase 5: Trading Disclosures** (Weeks 9-10) - STOCK Act, financial disclosures, PDF parsing
6. **Phase 6: API & MCP Server** (Weeks 11-12) - FastAPI REST API, MCP server
7. **Phase 7: Analysis & Visualization** (Weeks 13-14) - Notebooks, dashboards, export utilities
8. **Phase 8: Production Hardening** (Weeks 15-16) - Error handling, monitoring, docs, load testing

---

## Estimated Data Volumes

| Data Type | Records | Size |
|-----------|---------|------|
| Members | ~20,000 | ~10MB |
| Bills | ~300,000 | ~2GB |
| Bill Actions | ~5,000,000 | ~10GB |
| Votes | ~50,000 | ~500MB |
| FEC Contributions | ~100M+ | ~50GB |
| FEC Disbursements | ~50M+ | ~25GB |
| Stock Disclosures | ~100,000 | ~1GB |
| Lobbying | ~500,000 | ~2GB |
| Bill Texts | ~500,000 | ~100GB |

**Total estimated storage**: ~200-300GB

---

## Key Cross-Domain Queries

1. Money-Vote Correlation: Contributors lobbying for/against bills vs. member votes
2. Trading Anomalies: Stock trades within 30 days of committee actions on relevant bills
3. Voting Loyalty: Member voting patterns vs. party line, correlated with donor industries
4. Legislative Effectiveness: Bills sponsored/cosponsored, passage rate, by donor profile
5. Influence Networks: Committee membership + donor overlap + voting alignment
6. Temporal Analysis: How patterns change over congresses
7. Geographic Analysis: State/district donation patterns vs. representative behavior
8. Lobbying Impact: Lobbying spend vs. bill outcomes for specific industries
