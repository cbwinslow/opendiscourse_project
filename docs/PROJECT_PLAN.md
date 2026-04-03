# Government Data Aggregation Database - Comprehensive Project Plan

## Executive Summary

A unified PostgreSQL database that ingests, normalizes, and correlates US government data from multiple sources: legislation, voting records, member information, campaign finance, congressional trading disclosures, and lobbying data. Built with Python ingestion pipelines, MCP servers for AI integration, and a normalized schema enabling cross-domain analysis.

---

## 1. Data Sources & APIs

### 1.1 Congress.gov API (Official - Library of Congress)
- **URL**: `https://api.congress.gov/v3/`
- **GitHub**: `LibraryOfCongress/api.congress.gov` (920 stars)
- **Auth**: API key required (free via api.data.gov)
- **Rate Limits**: 1000 requests/hour with key
- **Endpoints**:
  - `/bill` - All bills (HR, S, HJ, SJ, HR, SR, HCONRES, SCONRES, HRES, SRES)
  - `/bill/{congress}/{type}/{number}` - Bill details, actions, amendments, committees, cosponsors, related bills, subjects, summaries, text, titles
  - `/member` - All congressional members
  - `/member/{bioguideId}` - Member details, sponsored legislation, cosponsored legislation
  - `/committee` - All committees
  - `/committee/{committeeId}` - Committee details, associated bills, reports, nominations
  - `/amendment` - All amendments
  - `/nomination` - Presidential nominations
  - `/treaty` - Treaties
  - `/committeeReport` - Committee reports
  - `/congressional-record` - Congressional Record
  - `/house-communication` - House communications
  - `/congress` - Congress sessions
- **Coverage**: 1973-present (varies by endpoint)
- **Note**: API had outage in Aug 2025, verify availability

### 1.2 GovInfo API (Official - GPO)
- **URL**: `https://api.govinfo.gov/`
- **GitHub**: `usgpo/api`, `usgpo/bulk-data` (356 stars)
- **Auth**: API key via api.data.gov
- **Endpoints**:
  - Content packages, metadata, search service
  - Related documents service
- **Bulk Data Repository**: `https://www.govinfo.gov/bulkdata/`
  - Congressional Bill Text (113th Congress+)
  - Congressional Bill Status (108th Congress+)
  - Congressional Bill Summaries (113th Congress+)
  - Code of Federal Regulations (1996+)
  - Federal Register (2000+)
  - Congressional Record
  - US Code
  - Public/Private Laws
  - Statutes at Large
  - Congressional Hearings
  - Committee Prints
  - Committee Reports
- **Formats**: XML, JSON, PDF
- **MCP Server**: Official GovInfo MCP available at `usgpo/api` repo

### 1.3 FEC Campaign Finance API
- **URL**: `https://api.open.fec.gov/developers/`
- **Auth**: API key required (free)
- **Endpoints**:
  - `/candidates/` - Candidate data
  - `/committees/` - Committee data
  - `/schedules/schedule_a/` - Individual contributions (donations)
  - `/schedules/schedule_b/` - Disbursements
  - `/schedules/schedule_c/` - Loans
  - `/schedules/schedule_d/` - Receipts
  - `/schedules/schedule_e/` - Independent expenditures
  - `/schedules/schedule_f/` - Debts
  - `/schedules/schedule_h4/` - Allocation
  - `/totals/` - Committee totals
  - `/filings/` - FEC filings
  - `/elections/` - Election data
  - `/rad-analysis/` - Reports analysis
- **Bulk Data**: `https://www.fec.gov/data/browse-data/`
  - All filings in CSV/ZIP format
  - Historical data back to 1980

### 1.4 OpenSecrets API (NIMSP/CRP)
- **URL**: `https://www.opensecrets.org/api/`
- **Auth**: API key required (free, limited)
- **Endpoints**:
  - `candContrib` - Candidate contributors
  - `candIndustry` - Candidate by industry
  - `candSector` - Candidate by sector
  - `candSummary` - Candidate summary
  - `memPACprofile` - Member PAC profile
  - `orgSummary` - Organization summary
  - `indusProfile` - Industry profile
  - `lobbying` - Lobbying data
  - `outsideSpending` - Outside spending
  - `legislators` - Legislator info
- **Bulk Data**: `https://www.opensecrets.org/open-data/bulk-data`

### 1.5 Congressional Trading/Stock Disclosures
- **Primary Sources**:
  - Senate: `https://www.senate.gov/senators/financial-disclosures/`
  - House: `https://disclosures-clerk.house.gov/`
- **Third-Party APIs**:
  - **Apify**: `ryanclinton/congress-stock-tracker` - STOCK Act scraper
  - **Apify**: `johnvc/us-congress-financial-dis` - Financial disclosures
  - **Finnhub**: `/api/v1/insider/congressional-trading` - Congressional trading API
  - **Financial Modeling Prep**: Congressional ownership APIs
  - **FinBrain**: House/Senate trades datasets
- **STOCK Act**: Requires disclosures within 45 days of transaction

### 1.6 Additional Data Sources
- **Ballotpedia**: Election results, candidate info
- **Vote Smart**: Voting records, issue positions, ratings
- **GovTrack.us**: Historical congressional data, bill tracking
- **MapLight**: Money in politics, bill-vote correlations
- **Sunlight Foundation Archives**: Historical legislative data
- **CQ Roll Call**: Congressional news, vote analysis (paid)
- **Congressional Data Coalition**: `congressionaldata.org`

---

## 2. MCP Servers

### 2.1 Congress.gov MCP Servers
| Repository | Language | Stars | Description |
|------------|----------|-------|-------------|
| `cyanheads/congressgov-mcp-server` | TypeScript | New | Bills, votes, members, committees. STDIO & Streamable HTTP |
| `amurshak/congressMCP` | Python | 27 | 91 operations consolidated into 6 tools |
| `bsmi021/mcp-congress_gov_server` | TypeScript | 7 | Hybrid approach to Congress.gov API v3 |
| `nawagner/congress-mcp` | Python | 2 | Access to official Congress.gov API v3 |

### 2.2 GovInfo MCP Server
- **Official**: `usgpo/api` repo - `docs/mcp.md`
- Provides access to latest GovInfo content
- Public preview status

### 2.3 Data.gov MCP Server
- **Repository**: Community-built
- Access to datasets across federal agencies

---

## 3. Python Packages & Tools

### 3.1 Primary Ingestion Tools
| Package | Description | Stars | Status |
|---------|-------------|-------|--------|
| `unitedstates/congress` | Bills, amendments, votes, nominations, committee meetings | 1042 | Active |
| `BICAM` (bicam-data/bicam) | Bulk Ingestion of Congressional Actions & Materials | 2 | Active |
| `python-congress` | ProPublica Congress API client (defunct) | - | Deprecated |

### 3.2 Recommended Stack
- **HTTP Client**: `httpx` (async) or `requests`
- **XML Parsing**: `lxml`, `xmltodict`
- **JSON Processing**: Built-in `json`, `orjson` (fast)
- **Data Processing**: `pandas`, `polars` (faster)
- **Database ORM**: `SQLAlchemy 2.0`
- **Database Migrations**: `Alembic`
- **Task Queue**: `Celery` or `Dramatiq`
- **Scheduling**: `APScheduler` or cron
- **Web Scraping**: `playwright`, `scrapy`, `beautifulsoup4`
- **PDF Processing**: `pdfplumber`, `pypdf2`

---

## 4. HuggingFace Datasets

### 4.1 Relevant Datasets
| Dataset | Description | URL Pattern |
|---------|-------------|-------------|
| Congressional Record | Congressional proceedings | `huggingface.co/datasets/congressional-record` |
| Bill Summaries | NLP-ready bill summaries | Various |
| Congressional Votes | Roll call vote data | Various |
| Political Text | Political documents for NLP | Various |
| US Legislation | Historical legislation corpus | Various |
| Congressional Data (BICAM) | Bulk congressional actions | `bicam-data/bicam` |

### 4.2 Dataset Ingestion Strategy
- Use `datasets` library from HuggingFace
- Download and normalize into PostgreSQL tables
- Cross-reference with primary sources for updates

---

## 5. Database Schema Design

### 5.1 Core Tables

```sql
-- CONGRESS & SESSIONS
CREATE TABLE congresses (
    id SERIAL PRIMARY KEY,
    congress_number INTEGER UNIQUE NOT NULL,  -- 108, 109, 110, etc.
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- CHAMBERS
CREATE TABLE chambers (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,  -- 'house', 'senate', 'joint'
    name VARCHAR(50) NOT NULL
);

-- MEMBERS OF CONGRESS
CREATE TABLE members (
    id SERIAL PRIMARY KEY,
    bioguide_id VARCHAR(20) UNIQUE,           -- Congress.gov ID
    govtrack_id INTEGER UNIQUE,               -- GovTrack ID
    thomas_id VARCHAR(20),                    -- Legacy THOMAS ID
    lis_id VARCHAR(20),                       -- Senate LIS ID
    fec_id VARCHAR(20),                       -- FEC candidate ID
    opensecrets_id VARCHAR(20),               -- OpenSecrets ID
    vote_smart_id INTEGER,                    -- Vote Smart ID
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    suffix VARCHAR(20),
    nickname VARCHAR(100),
    full_name VARCHAR(200),
    date_of_birth DATE,
    gender VARCHAR(20),
    party VARCHAR(50),                        -- Current party
    state VARCHAR(50) NOT NULL,
    district INTEGER,                         -- NULL for Senators
    chamber VARCHAR(20),                      -- 'house' or 'senate'
    title VARCHAR(50),                        -- Rep, Sen, Delegate, etc.
    website_url TEXT,
    contact_form_url TEXT,
    phone VARCHAR(30),
    office_address TEXT,
    rss_url TEXT,
    twitter_id VARCHAR(100),
    youtube_id VARCHAR(100),
    facebook_id VARCHAR(100),
    image_url TEXT,
    is_current BOOLEAN DEFAULT TRUE,
    first_congress INTEGER,
    last_congress INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- MEMBER TERMS (tracks changes over time)
CREATE TABLE member_terms (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    congress_id INTEGER REFERENCES congresses(id),
    chamber VARCHAR(20) NOT NULL,
    state VARCHAR(50) NOT NULL,
    district INTEGER,
    party VARCHAR(50) NOT NULL,
    class INTEGER,                            -- Senate class (1, 2, 3)
    state_rank VARCHAR(10),                   -- 'junior' or 'senior'
    start_date DATE NOT NULL,
    end_date DATE,
    how_ended VARCHAR(50),                    -- 'term_expired', 'resigned', 'died', etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- COMMITTEES
CREATE TABLE committees (
    id SERIAL PRIMARY KEY,
    congress_gov_id VARCHAR(50) UNIQUE,
    house_committee_id VARCHAR(20),           -- Legacy House ID
    senate_committee_id VARCHAR(20),          -- Legacy Senate ID
    name VARCHAR(200) NOT NULL,
    chamber VARCHAR(20),                      -- 'house', 'senate', 'joint'
    committee_type VARCHAR(50),              -- 'standing', 'select', 'joint', 'subcommittee'
    parent_committee_id INTEGER REFERENCES committees(id),
    congress_id INTEGER REFERENCES congresses(id),
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- COMMITTEE MEMBERSHIP
CREATE TABLE committee_memberships (
    id SERIAL PRIMARY KEY,
    committee_id INTEGER REFERENCES committees(id),
    member_id INTEGER REFERENCES members(id),
    congress_id INTEGER REFERENCES congresses(id),
    role VARCHAR(50),                        -- 'chair', 'ranking_member', 'member'
    created_at TIMESTAMP DEFAULT NOW()
);

-- BILLS & RESOLUTIONS
CREATE TABLE bills (
    id SERIAL PRIMARY KEY,
    congress_gov_id VARCHAR(50) UNIQUE NOT NULL,
    congress_id INTEGER REFERENCES congresses(id),
    bill_type VARCHAR(20) NOT NULL,          -- 'hr', 's', 'hjres', 'sjres', 'hconres', 'sconres', 'hres', 'sres'
    number INTEGER NOT NULL,
    display_number VARCHAR(50),              -- 'HR 1', 'S 234', etc.
    title TEXT,
    popular_title TEXT,
    short_title TEXT,
    official_title TEXT,
    sponsor_id INTEGER REFERENCES members(id),
    origin_chamber VARCHAR(20),              -- 'house' or 'senate'
    status VARCHAR(50),                      -- 'introduced', 'reported', 'passed', 'enacted', 'vetoed', etc.
    status_date DATE,
    introduced_date DATE,
    latest_action_date DATE,
    latest_action TEXT,
    enacted_as VARCHAR(50),                  -- 'law', 'treaty', etc.
    law_number VARCHAR(50),                  -- Public law number
    session_law VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(congress_id, bill_type, number)
);

-- BILL ACTIONS
CREATE TABLE bill_actions (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    action_date TIMESTAMP NOT NULL,
    action_time TIMESTAMP,
    chamber VARCHAR(20),
    action_type VARCHAR(50),
    text TEXT,
    record_id VARCHAR(50),
    source_system VARCHAR(50),
    committee_id INTEGER REFERENCES committees(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- BILL COSPONSORS
CREATE TABLE bill_cosponsors (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    member_id INTEGER REFERENCES members(id),
    is_original_cosponsor BOOLEAN DEFAULT FALSE,
    sponsorship_date DATE,
    withdrawal_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- BILL COMMITTEES
CREATE TABLE bill_committees (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    committee_id INTEGER REFERENCES committees(id),
    activity VARCHAR(100),                   -- 'referred to', 'reported by', 'discharged from', etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- BILL SUBJECTS
CREATE TABLE bill_subjects (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    subject_type VARCHAR(50),                -- 'legislative', 'policy_area'
    name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- BILL SUMMARIES
CREATE TABLE bill_summaries (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    action_date DATE,
    action_description VARCHAR(200),
    text TEXT NOT NULL,
    source VARCHAR(50),                      -- 'CRS', 'LCS', etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- BILL TEXT VERSIONS
CREATE TABLE bill_texts (
    id PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    version_code VARCHAR(20),                -- 'ih', 'eh', 'enr', etc.
    version_description VARCHAR(200),
    url TEXT,
    format VARCHAR(20),                      -- 'xml', 'html', 'pdf', 'txt'
    date DATE,
    full_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- RELATED BILLS
CREATE TABLE related_bills (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    related_bill_id INTEGER REFERENCES bills(id),
    relationship_type VARCHAR(50),           -- 'identical', 'related', 'includes', etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- AMENDMENTS
CREATE TABLE amendments (
    id SERIAL PRIMARY KEY,
    congress_gov_id VARCHAR(50) UNIQUE,
    bill_id INTEGER REFERENCES bills(id),
    amendment_type VARCHAR(20),              -- 'hamdt', 'samdt'
    number INTEGER,
    description TEXT,
    purpose TEXT,
    sponsor_id INTEGER REFERENCES members(id),
    proposed_date DATE,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- VOTES (Roll Call)
CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    congress_gov_id VARCHAR(50) UNIQUE,
    congress_id INTEGER REFERENCES congresses(id),
    chamber VARCHAR(20) NOT NULL,
    session VARCHAR(10),
    roll_number INTEGER NOT NULL,
    vote_date DATE NOT NULL,
    vote_time TIME,
    question VARCHAR(200),                   -- 'On Passage', 'On Motion to Recommit', etc.
    vote_type VARCHAR(50),                   -- 'YEA-AND-NAY', 'RECORDED VOTE', etc.
    vote_result VARCHAR(50),                 -- 'Agreed to', 'Failed', etc.
    vote_description TEXT,
    bill_id INTEGER REFERENCES bills(id),
    amendment_id INTEGER REFERENCES amendments(id),
    nomination_id INTEGER REFERENCES nominations(id),
    majority_position VARCHAR(20),           -- 'YEA', 'NAY'
    total_yes INTEGER,
    total_no INTEGER,
    total_present INTEGER,
    total_not_voting INTEGER,
    required_majority VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(congress_id, chamber, roll_number)
);

-- INDIVIDUAL VOTE RECORDS
CREATE TABLE vote_positions (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER REFERENCES votes(id),
    member_id INTEGER REFERENCES members(id),
    position VARCHAR(20),                    -- 'Yea', 'Nay', 'Present', 'Not Voting'
    created_at TIMESTAMP DEFAULT NOW()
);

-- NOMINATIONS
CREATE TABLE nominations (
    id SERIAL PRIMARY KEY,
    congress_gov_id VARCHAR(50) UNIQUE,
    congress_id INTEGER REFERENCES congresses(id),
    number VARCHAR(50),
    name VARCHAR(200),
    position_title TEXT,
    organization TEXT,
    nominee_name VARCHAR(200),
    nominee_state VARCHAR(50),
    received_date DATE,
    status VARCHAR(50),
    committee_id INTEGER REFERENCES committees(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- NOMINATION ACTIONS
CREATE TABLE nomination_actions (
    id SERIAL PRIMARY KEY,
    nomination_id INTEGER REFERENCES nominations(id),
    action_date DATE,
    action TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- TREATIES
CREATE TABLE treaties (
    id SERIAL PRIMARY KEY,
    congress_gov_id VARCHAR(50) UNIQUE,
    congress_id INTEGER REFERENCES congresses(id),
    treaty_number INTEGER,
    resolution_number INTEGER,
    title TEXT,
    received_date DATE,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- COMMITTEE REPORTS
CREATE TABLE committee_reports (
    id SERIAL PRIMARY KEY,
    congress_gov_id VARCHAR(50) UNIQUE,
    congress_id INTEGER REFERENCES congresses(id),
    report_type VARCHAR(20),                 -- 'h rpt', 's rpt', 'e rpt'
    number INTEGER,
    title TEXT,
    committee_id INTEGER REFERENCES committees(id),
    bill_id INTEGER REFERENCES bills(id),
    date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- CONGRESSIONAL RECORD
CREATE TABLE congressional_records (
    id SERIAL PRIMARY KEY,
    congress_gov_id VARCHAR(50) UNIQUE,
    date DATE NOT NULL,
    volume VARCHAR(20),
    issue VARCHAR(20),
    section VARCHAR(20),                     -- 'Daily Digest', 'Senate', 'House', etc.
    url TEXT,
    pdf_url TEXT,
    full_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- FEDERAL REGISTER
CREATE TABLE federal_register (
    id SERIAL PRIMARY KEY,
    document_number VARCHAR(50) UNIQUE,
    date DATE NOT NULL,
    type VARCHAR(50),                        -- 'rule', 'proposed_rule', 'notice', 'presidential_document'
    title TEXT,
    agency VARCHAR(200),
    docket_number VARCHAR(100),
    pdf_url TEXT,
    html_url TEXT,
    full_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- CODE OF FEDERAL REGULATIONS
CREATE TABLE cfr_entries (
    id SERIAL PRIMARY KEY,
    title INTEGER NOT NULL,
    part INTEGER NOT NULL,
    section INTEGER,
    heading TEXT,
    text TEXT,
    last_updated DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.2 Campaign Finance Tables

```sql
-- FEC CANDIDATES
CREATE TABLE fec_candidates (
    id SERIAL PRIMARY KEY,
    fec_candidate_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    party VARCHAR(50),
    office_sought VARCHAR(50),               -- 'P', 'S', 'H'
    state VARCHAR(50),
    district INTEGER,
    incumbent_active CHAR(1),                -- 'C', 'I', 'O', 'N'
    principal_committee_id VARCHAR(20),
    election_year INTEGER,
    election_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- FEC COMMITTEES
CREATE TABLE fec_committees (
    id SERIAL PRIMARY KEY,
    fec_committee_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(300) NOT NULL,
    committee_type VARCHAR(50),              -- 'H', 'S', 'P', 'X', 'Y', 'Z', etc.
    committee_designation VARCHAR(50),       -- 'A', 'P', 'T', etc.
    party VARCHAR(50),
    treasurer_name VARCHAR(200),
    street1 VARCHAR(100),
    street2 VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- FEC COMMITTEE CANDIDATE LINKS
CREATE TABLE fec_committee_candidates (
    id SERIAL PRIMARY KEY,
    fec_committee_id VARCHAR(20),
    fec_candidate_id VARCHAR(20),
    election_year INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- INDIVIDUAL CONTRIBUTIONS (Schedule A)
CREATE TABLE fec_contributions (
    id SERIAL PRIMARY KEY,
    filing_id INTEGER,
    report_year INTEGER,
    report_type VARCHAR(50),
    committee_id VARCHAR(20) REFERENCES fec_committees(fec_committee_id),
    contributor_name VARCHAR(200),
    contributor_city VARCHAR(100),
    contributor_state VARCHAR(50),
    contributor_zip VARCHAR(20),
    employer VARCHAR(200),
    occupation VARCHAR(200),
    contribution_date DATE NOT NULL,
    contribution_amount NUMERIC(12,2) NOT NULL,
    contribution_type VARCHAR(50),           -- '15', '15E', '15J', etc.
    memo_code CHAR(1),
    memo_text TEXT,
    election_type VARCHAR(20),               -- 'P', 'G', 'R', 'O', etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- DISBURSEMENTS (Schedule B)
CREATE TABLE fec_disbursements (
    id SERIAL PRIMARY KEY,
    filing_id INTEGER,
    report_year INTEGER,
    committee_id VARCHAR(20) REFERENCES fec_committees(fec_committee_id),
    payee_name VARCHAR(200),
    payee_city VARCHAR(100),
    payee_state VARCHAR(50),
    payee_zip VARCHAR(20),
    disbursement_date DATE NOT NULL,
    disbursement_amount NUMERIC(12,2) NOT NULL,
    disbursement_type VARCHAR(50),
    purpose VARCHAR(200),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- INDEPENDENT EXPENDITURES (Schedule E)
CREATE TABLE fec_independent_expenditures (
    id SERIAL PRIMARY KEY,
    filing_id INTEGER,
    committee_id VARCHAR(20) REFERENCES fec_committees(fec_committee_id),
    candidate_id VARCHAR(20) REFERENCES fec_candidates(fec_candidate_id),
    support_oppose VARCHAR(10),              -- 'S' or 'O'
    expenditure_date DATE NOT NULL,
    expenditure_amount NUMERIC(12,2) NOT NULL,
    expenditure_type VARCHAR(50),
    memo_code CHAR(1),
    memo_text TEXT,
    candidate_office VARCHAR(20),
    candidate_state VARCHAR(50),
    candidate_district INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- FEC FILINGS
CREATE TABLE fec_filings (
    id SERIAL PRIMARY KEY,
    filing_number INTEGER UNIQUE NOT NULL,
    committee_id VARCHAR(20) REFERENCES fec_committees(fec_committee_id),
    report_type VARCHAR(50),
    report_year INTEGER,
    coverage_start DATE,
    coverage_end DATE,
    receipt_date DATE,
    filing_status VARCHAR(50),
    pdf_url TEXT,
    xml_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- FEC TOTALS
CREATE TABLE fec_totals (
    id SERIAL PRIMARY KEY,
    committee_id VARCHAR(20) REFERENCES fec_committees(fec_committee_id),
    report_year INTEGER,
    report_type VARCHAR(50),
    receipts NUMERIC(14,2),
    disbursements NUMERIC(14,2),
    cash_on_hand NUMERIC(14,2),
    debt_owed NUMERIC(14,2),
    individual_contributions NUMERIC(14,2),
    pac_contributions NUMERIC(14,2),
    candidate_contributions NUMERIC(14,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.3 OpenSecrets/Lobbying Tables

```sql
-- OPENSECRETS LEGISLATORS
CREATE TABLE opensecrets_legislators (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    opensecrets_id VARCHAR(20) UNIQUE,
    firstlast VARCHAR(200),
    party VARCHAR(50),
    office VARCHAR(50),
    gender VARCHAR(10),
    first_elected INTEGER,
    exit_code VARCHAR(10),
    comments TEXT,
    phone VARCHAR(30),
    fax VARCHAR(30),
    website TEXT,
    webform TEXT,
    congress_office TEXT,
    bioguide_id VARCHAR(20),
    votesmart_id INTEGER,
    fec_id VARCHAR(20),
    govtrack_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- OPENSECRETS CANDIDATE SUMMARY
CREATE TABLE opensecrets_candidate_summaries (
    id SERIAL PRIMARY KEY,
    legislator_id INTEGER REFERENCES opensecrets_legislators(id),
    cycle INTEGER NOT NULL,
    firstlast VARCHAR(200),
    chamber VARCHAR(20),
    party VARCHAR(50),
    state VARCHAR(50),
    total NUMERIC(14,2),
    spent NUMERIC(14,2),
    cash_on_hand NUMERIC(14,2),
    debt NUMERIC(14,2),
    origin VARCHAR(50),
    source TEXT,
    last_updated DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- OPENSECRETS CANDIDATE CONTRIBUTORS
CREATE TABLE opensecrets_contributors (
    id SERIAL PRIMARY KEY,
    legislator_id INTEGER REFERENCES opensecrets_legislators(id),
    cycle INTEGER NOT NULL,
    org_name VARCHAR(300) NOT NULL,
    total NUMERIC(14,2) NOT NULL,
    pacs NUMERIC(14,2),
    indivs NUMERIC(14,2),
    rank INTEGER,
    source TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- OPENSECRETS CANDIDATE BY INDUSTRY
CREATE TABLE opensecrets_industry_contributions (
    id SERIAL PRIMARY KEY,
    legislator_id INTEGER REFERENCES opensecrets_legislators(id),
    cycle INTEGER NOT NULL,
    industry_code VARCHAR(10),
    industry_name VARCHAR(200),
    total NUMERIC(14,2),
    pacs NUMERIC(14,2),
    indivs NUMERIC(14,2),
    rank INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- OPENSECRETS CANDIDATE BY SECTOR
CREATE TABLE opensecrets_sector_contributions (
    id SERIAL PRIMARY KEY,
    legislator_id INTEGER REFERENCES opensecrets_legislators(id),
    cycle INTEGER NOT NULL,
    sector_name VARCHAR(100),
    sector_id VARCHAR(10),
    total NUMERIC(14,2),
    pacs NUMERIC(14,2),
    indivs NUMERIC(14,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- LOBBYING DATA
CREATE TABLE lobbying_disclosures (
    id SERIAL PRIMARY KEY,
    filing_id VARCHAR(50) UNIQUE,
    registrant_name VARCHAR(300),
    client_name VARCHAR(300),
    lobby_year INTEGER,
    income NUMERIC(14,2),
    expenses NUMERIC(14,2),
    filing_date DATE,
    filing_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- LOBBYING ISSUES
CREATE TABLE lobbying_issues (
    id SERIAL PRIMARY KEY,
    disclosure_id INTEGER REFERENCES lobbying_disclosures(id),
    issue_code VARCHAR(10),
    issue_description TEXT,
    specific_issues TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- LOBBYING LOBBYISTS
CREATE TABLE lobbying_lobbyists (
    id SERIAL PRIMARY KEY,
    disclosure_id INTEGER REFERENCES lobbying_disclosures(id),
    lobbyist_name VARCHAR(200),
    covered_official_position VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

-- LOBBYING CONGRESSIONAL CONTACTS
CREATE TABLE lobbying_contacts (
    id SERIAL PRIMARY KEY,
    disclosure_id INTEGER REFERENCES lobbying_disclosures(id),
    senator_bioguide_id VARCHAR(20),
    rep_bioguide_id VARCHAR(20),
    house_member_id VARCHAR(20),
    senate_member_id VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.4 Congressional Trading/Stock Disclosure Tables

```sql
-- STOCK ACT DISCLOSURES
CREATE TABLE stock_disclosures (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    filing_date DATE NOT NULL,
    report_type VARCHAR(50),                 -- 'periodic', 'late', 'amended'
    report_url TEXT,
    pdf_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- STOCK TRANSACTIONS
CREATE TABLE stock_transactions (
    id SERIAL PRIMARY KEY,
    disclosure_id INTEGER REFERENCES stock_disclosures(id),
    member_id INTEGER REFERENCES members(id),
    filer_name VARCHAR(200),                 -- Member, spouse, dependent
    filer_relation VARCHAR(50),              -- 'self', 'spouse', 'dependent_child'
    asset_name VARCHAR(300) NOT NULL,
    asset_type VARCHAR(50),                  -- 'stock', 'bond', 'mutual_fund', 'etf', 'option', 'commodity', etc.
    ticker VARCHAR(20),
    cusip VARCHAR(20),
    transaction_type VARCHAR(50),            -- 'purchase', 'sale', 'exchange', 'gift', etc.
    transaction_date DATE,
    transaction_amount_low NUMERIC(12,2),    -- Range minimum
    transaction_amount_high NUMERIC(12,2),   -- Range maximum
    transaction_amount NUMERIC(14,2),        -- Estimated midpoint
    ownership_type VARCHAR(50),              -- 'joint', 'individual'
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- FINANCIAL DISCLOSURES (Annual)
CREATE TABLE financial_disclosures (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    year INTEGER NOT NULL,
    filing_type VARCHAR(50),                 -- 'senate', 'house'
    pdf_url TEXT,
    filing_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- FINANCIAL DISCLOSURE POSITIONS
CREATE TABLE financial_positions (
    id SERIAL PRIMARY KEY,
    disclosure_id INTEGER REFERENCES financial_disclosures(id),
    organization_name VARCHAR(300),
    position_title VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

-- FINANCIAL DISCLOSURE AGREEMENTS
CREATE TABLE financial_agreements (
    id SERIAL PRIMARY KEY,
    disclosure_id INTEGER REFERENCES financial_disclosures(id),
    party_name VARCHAR(300),
    terms_or_date TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- FINANCIAL DISCLOSURE GIFTS
CREATE TABLE financial_gifts (
    id SERIAL PRIMARY KEY,
    disclosure_id INTEGER REFERENCES financial_disclosures(id),
    source_name VARCHAR(300),
    description TEXT,
    value NUMERIC(12,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- FINANCIAL DISCLOSURE TRAVEL
CREATE TABLE financial_travel (
    id SERIAL PRIMARY KEY,
    disclosure_id INTEGER REFERENCES financial_disclosures(id),
    source_name VARCHAR(300),
    destination VARCHAR(200),
    dates VARCHAR(100),
    purpose VARCHAR(200),
    amount NUMERIC(12,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- FINANCIAL DISCLOSURE ASSETS
CREATE TABLE financial_assets (
    id SERIAL PRIMARY KEY,
    disclosure_id INTEGER REFERENCES financial_disclosures(id),
    asset_name VARCHAR(300),
    asset_type VARCHAR(100),
    value_low NUMERIC(14,2),
    value_high NUMERIC(14,2),
    income_type VARCHAR(50),
    income_low NUMERIC(14,2),
    income_high NUMERIC(14,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.5 Metadata & Ingestion Tables

```sql
-- DATA SOURCES
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    url TEXT,
    description TEXT,
    api_type VARCHAR(50),                    -- 'rest', 'bulk', 'scrape', 'mcp'
    auth_type VARCHAR(50),
    rate_limit INTEGER,
    last_sync TIMESTAMP,
    status VARCHAR(50),                      -- 'active', 'inactive', 'error'
    created_at TIMESTAMP DEFAULT NOW()
);

-- INGESTION LOGS
CREATE TABLE ingestion_logs (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES data_sources(id),
    table_name VARCHAR(100),
    records_processed INTEGER,
    records_inserted INTEGER,
    records_updated INTEGER,
    records_failed INTEGER,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    status VARCHAR(50),
    error_message TEXT,
    metadata JSONB
);

-- API RATE LIMIT TRACKING
CREATE TABLE api_rate_limits (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES data_sources(id),
    endpoint VARCHAR(200),
    requests_made INTEGER DEFAULT 0,
    limit_total INTEGER,
    limit_reset TIMESTAMP,
    last_request TIMESTAMP DEFAULT NOW()
);

-- DATA QUALITY CHECKS
CREATE TABLE data_quality_checks (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    check_name VARCHAR(100),
    check_type VARCHAR(50),                  -- 'completeness', 'uniqueness', 'validity', 'consistency'
    records_checked INTEGER,
    records_failed INTEGER,
    passed BOOLEAN,
    details JSONB,
    checked_at TIMESTAMP DEFAULT NOW()
);
```

### 5.6 Indexes (Performance)

```sql
-- Core indexes
CREATE INDEX idx_bills_congress_type ON bills(congress_id, bill_type);
CREATE INDEX idx_bills_sponsor ON bills(sponsor_id);
CREATE INDEX idx_bills_status ON bills(status);
CREATE INDEX idx_bills_introduced_date ON bills(introduced_date);
CREATE INDEX idx_bill_actions_bill ON bill_actions(bill_id);
CREATE INDEX idx_bill_actions_date ON bill_actions(action_date);
CREATE INDEX idx_bill_cosponsors_bill ON bill_cosponsors(bill_id);
CREATE INDEX idx_bill_cosponsors_member ON bill_cosponsors(member_id);
CREATE INDEX idx_votes_congress_chamber ON votes(congress_id, chamber);
CREATE INDEX idx_votes_date ON votes(vote_date);
CREATE INDEX idx_votes_bill ON votes(bill_id);
CREATE INDEX idx_vote_positions_vote ON vote_positions(vote_id);
CREATE INDEX idx_vote_positions_member ON vote_positions(member_id);
CREATE INDEX idx_member_terms_member ON member_terms(member_id);
CREATE INDEX idx_member_terms_congress ON member_terms(congress_id);
CREATE INDEX idx_committee_memberships_committee ON committee_memberships(committee_id);
CREATE INDEX idx_committee_memberships_member ON committee_memberships(member_id);
CREATE INDEX idx_fec_contributions_committee ON fec_contributions(committee_id);
CREATE INDEX idx_fec_contributions_date ON fec_contributions(contribution_date);
CREATE INDEX idx_fec_contributions_amount ON fec_contributions(contribution_amount);
CREATE INDEX idx_stock_transactions_member ON stock_transactions(member_id);
CREATE INDEX idx_stock_transactions_date ON stock_transactions(transaction_date);
CREATE INDEX idx_stock_transactions_ticker ON stock_transactions(ticker);
CREATE INDEX idx_opensecrets_contributors_legislator ON opensecrets_contributors(legislator_id);
CREATE INDEX idx_opensecrets_contributors_cycle ON opensecrets_contributors(cycle);

-- Full-text search indexes
CREATE INDEX idx_bills_title_search ON bills USING gin(to_tsvector('english', title));
CREATE INDEX idx_bill_actions_text_search ON bill_actions USING gin(to_tsvector('english', text));
CREATE INDEX idx_bill_summaries_text_search ON bill_summaries USING gin(to_tsvector('english', text));
CREATE INDEX idx_contributor_name_search ON fec_contributions USING gin(to_tsvector('english', contributor_name));
CREATE INDEX idx_member_name_search ON members USING gin(to_tsvector('english', first_name || ' ' || last_name));
```

---

## 6. Infrastructure Architecture

### 6.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION LAYER                            │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│ Congress.gov│  GovInfo    │    FEC      │ OpenSecrets │  Scrapers       │
│   API       │  API/Bulk   │   API/Bulk  │   API       │  (STOCK Act)    │
├─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┤
│                         INGESTION PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Fetcher  │→ │ Parser   │→ │Validator │→ │Normalizer│→ │  Loader  │  │
│  │          │  │          │  │          │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                         MESSAGE QUEUE (Redis/RabbitMQ)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                         WORKER PROCESSES (Celery)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                         POSTGRESQL 16 + pgvector                        │
├─────────────────────────────────────────────────────────────────────────┤
│                         QUERY/ANALYSIS LAYER                            │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│   REST API  │  MCP Server │  BI Tools   │  Jupyter    │  CLI Tools      │
│  (FastAPI)  │  (LangChain)│  (Metabase) │  Notebooks  │                 │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┘
```

### 6.2 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Database | PostgreSQL 16 + pgvector | Already running on server, supports vector search |
| ORM | SQLAlchemy 2.0 | Industry standard, async support |
| Migrations | Alembic | SQLAlchemy companion |
| Task Queue | Celery + Redis | Mature, reliable, distributed |
| Scheduling | APScheduler / Celery Beat | Built-in periodic task support |
| API | FastAPI | Fast, async, auto-docs |
| MCP Server | LangChain MCP SDK | Standard MCP implementation |
| HTTP Client | httpx | Async, modern |
| XML Parsing | lxml + xmltodict | Fast, reliable |
| Data Processing | Polars | Faster than pandas for ETL |
| Web Scraping | Playwright | Modern, handles JS |
| Monitoring | Sentry + Prometheus | Error tracking + metrics |
| Containerization | Docker Compose | Easy deployment |
| CI/CD | GitHub Actions | Standard |

### 6.3 Directory Structure

```
government-data-db/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
├── .env.example
├── alembic.ini
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── src/
│   └── govdata/
│       ├── __init__.py
│       ├── config.py
│       ├── database.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── congress.py
│       │   ├── campaign_finance.py
│       │   ├── lobbying.py
│       │   ├── stock_disclosures.py
│       │   └── metadata.py
│       │
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── congress_gov.py
│       │   ├── govinfo.py
│       │   ├── fec.py
│       │   ├── opensecrets.py
│       │   ├── stock_disclosures.py
│       │   ├── ballotpedia.py
│       │   └── huggingface.py
│       │
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── xml_parser.py
│       │   ├── json_parser.py
│       │   ├── pdf_parser.py
│       │   └── csv_parser.py
│       │
│       ├── validators/
│       │   ├── __init__.py
│       │   └── validators.py
│       │
│       ├── transformers/
│       │   ├── __init__.py
│       │   └── normalizers.py
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── routes/
│       │   │   ├── bills.py
│       │   │   ├── members.py
│       │   │   ├── votes.py
│       │   │   ├── campaign_finance.py
│       │   │   └── stock_disclosures.py
│       │   └── schemas/
│       │
│       ├── mcp_server/
│       │   ├── __init__.py
│       │   └── server.py
│       │
│       └── utils/
│           ├── __init__.py
│           ├── rate_limiter.py
│           ├── logging_config.py
│           └── helpers.py
│
├── scripts/
│   ├── initial_bulk_load.py
│   ├── incremental_sync.py
│   ├── data_quality_check.py
│   └── export_dataset.py
│
├── tests/
│   ├── test_congress_gov.py
│   ├── test_fec.py
│   ├── test_models.py
│   └── test_api.py
│
├── notebooks/
│   ├── exploratory_analysis.ipynb
│   ├── voting_patterns.ipynb
│   └── money_in_politics.ipynb
│
└── docs/
    ├── schema.md
    ├── api.md
    └── ingestion_guide.md
```

---

## 7. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up repository and project structure
- [ ] Configure PostgreSQL database with schema
- [ ] Set up Alembic migrations
- [ ] Create SQLAlchemy models
- [ ] Configure Docker Compose (PostgreSQL, Redis, Celery)
- [ ] Set up CI/CD pipeline
- [ ] Create base ingestion framework (base classes, rate limiter, logging)

### Phase 2: Congress.gov Ingestion (Weeks 3-4)
- [ ] Implement Congress.gov API client
- [ ] Build member ingestion pipeline
- [ ] Build bill ingestion pipeline
- [ ] Build vote ingestion pipeline
- [ ] Build committee ingestion pipeline
- [ ] Build amendment ingestion pipeline
- [ ] Create initial bulk load script
- [ ] Create incremental sync scheduler

### Phase 3: GovInfo Ingestion (Weeks 5-6)
- [ ] Implement GovInfo API client
- [ ] Build bill text ingestion
- [ ] Build Congressional Record ingestion
- [ ] Build Federal Register ingestion
- [ ] Build CFR ingestion
- [ ] Set up bulk data downloads
- [ ] XML/JSON parsing pipeline

### Phase 4: Campaign Finance (Weeks 7-8)
- [ ] Implement FEC API client
- [ ] Build candidate ingestion
- [ ] Build committee ingestion
- [ ] Build contribution ingestion (Schedule A)
- [ ] Build disbursement ingestion (Schedule B)
- [ ] Build independent expenditure ingestion (Schedule E)
- [ ] Set up FEC bulk data downloads
- [ ] Implement OpenSecrets API client
- [ ] Build lobbying data ingestion

### Phase 5: Trading Disclosures (Weeks 9-10)
- [ ] Build STOCK Act scraper (Senate/House)
- [ ] Build financial disclosure parser
- [ ] Implement stock transaction ingestion
- [ ] Build PDF parsing pipeline for disclosures
- [ ] Integrate third-party APIs (Finnhub, FMP)
- [ ] Cross-reference with member data

### Phase 6: API & MCP Server (Weeks 11-12)
- [ ] Build FastAPI REST API
- [ ] Create query endpoints for all data types
- [ ] Implement full-text search
- [ ] Build MCP server
- [ ] Create MCP tools for all data domains
- [ ] Test with Claude/Cursor/other MCP clients

### Phase 7: Analysis & Visualization (Weeks 13-14)
- [ ] Create Jupyter notebooks for analysis
- [ ] Set up Metabase dashboards
- [ ] Create pre-built queries
- [ ] Build cross-domain correlation queries
- [ ] Create data export utilities

### Phase 8: Production Hardening (Weeks 15-16)
- [ ] Add comprehensive error handling
- [ ] Implement retry logic with exponential backoff
- [ ] Add monitoring and alerting
- [ ] Data quality checks
- [ ] Performance optimization
- [ ] Documentation
- [ ] Load testing

---

## 8. API Keys & Credentials Required

| Service | URL | Cost | Notes |
|---------|-----|------|-------|
| Congress.gov | `api.data.gov` | Free | 1000 req/hour |
| GovInfo | `api.data.gov` | Free | Same key as Congress.gov |
| FEC | `api.open.fec.gov` | Free | Rate limited |
| OpenSecrets | `opensecrets.org/api` | Free | Limited endpoints |
| Finnhub | `finnhub.io` | Free tier | 60 calls/min |
| FMP | `financialmodelingprep.com` | Free tier | 250 calls/day |
| Apify | `apify.com` | Free tier | For scraping |

---

## 9. Key Cross-Domain Queries (Use Cases)

1. **Money-Vote Correlation**: Find bills where top contributors lobbied for/against and how the member voted
2. **Trading Anomalies**: Stock trades by members within 30 days of committee actions on relevant bills
3. **Voting Loyalty**: Member voting patterns vs. party line, correlated with donor industries
4. **Legislative Effectiveness**: Bills sponsored/cosponsored, passage rate, by member and donor profile
5. **Influence Networks**: Committee membership + donor overlap + voting alignment graphs
6. **Temporal Analysis**: How member voting/donors/trading patterns change over congresses
7. **Geographic Analysis**: State/district-level donation patterns vs. representative behavior
8. **Lobbying Impact**: Lobbying spend vs. bill outcomes for specific industries

---

## 10. Estimated Data Volumes

| Data Type | Records | Size | Update Frequency |
|-----------|---------|------|------------------|
| Members | ~20,000 (historical) | ~10MB | Per congress |
| Bills | ~300,000 (historical) | ~2GB | Daily |
| Bill Actions | ~5,000,000 | ~10GB | Daily |
| Votes | ~50,000 (historical) | ~500MB | Daily |
| FEC Contributions | ~100,000,000+ | ~50GB | Quarterly |
| FEC Disbursements | ~50,000,000+ | ~25GB | Quarterly |
| Stock Disclosures | ~100,000 | ~1GB | Monthly |
| Lobbying | ~500,000 | ~2GB | Quarterly |
| Bill Texts | ~500,000 | ~100GB | Daily |

**Total estimated storage**: ~200-300GB for comprehensive historical data

---

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Congress.gov API outage | High | Cache aggressively, use GovInfo bulk as fallback |
| Rate limiting | Medium | Implement token bucket, batch requests, use bulk downloads |
| Schema changes in APIs | Medium | Version API clients, add schema validation |
| PDF parsing failures | Medium | Multiple parsers, manual review queue |
| Data inconsistencies | Medium | Data quality checks, reconciliation scripts |
| Large storage requirements | Low | Use server's existing PostgreSQL, compress old data |
| API key changes | Low | Centralized config, monitoring |

---

## 12. Quick Start Commands

```bash
# Clone and setup
git clone <repo> government-data-db
cd government-data-db
cp .env.example .env
# Edit .env with API keys

# Docker setup
docker compose up -d postgres redis

# Install dependencies
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Initial bulk load
python scripts/initial_bulk_load.py --source congress.gov --congress 118
python scripts/initial_bulk_load.py --source fec --year 2024

# Start workers
celery -A govdata.celery_app worker --loglevel=info

# Start scheduler
celery -A govdata.celery_app beat --loglevel=info

# Start API
uvicorn govdata.api.main:app --reload

# Start MCP server
python -m govdata.mcp_server.server
```

---

## 13. References & Resources

### Official Documentation
- Congress.gov API: `https://api.congress.gov`
- Congress.gov API GitHub: `https://github.com/LibraryOfCongress/api.congress.gov`
- GovInfo Developer Hub: `https://www.govinfo.gov/developers`
- GovInfo API Docs: `https://api.govinfo.gov/docs/`
- FEC API: `https://api.open.fec.gov/developers/`
- OpenSecrets API: `https://www.opensecrets.org/open-data/api-documentation`

### GitHub Repositories
- `usgpo/bulk-data` - GovInfo bulk data guides
- `usgpo/bill-status` - Bill status XML format
- `usgpo/api` - GovInfo API & MCP server
- `unitedstates/congress` - Python data collectors (1k stars)
- `LibraryOfCongress/api.congress.gov` - Congress.gov API source

### MCP Servers
- `cyanheads/congressgov-mcp-server`
- `amurshak/congressMCP`
- `bsmi021/mcp-congress_gov_server`
- `nawagner/congress-mcp`

### Third-Party APIs
- Finnhub Congressional Trading: `https://finnhub.io/docs/api/congressional-trading`
- FMP Congressional Trading: `https://site.financialmodelingprep.com/datasets/ownership-senate-insider`
- Apify Congress Stock Tracker: `https://apify.com/ryanclinton/congress-stock-tracker`

### Organizations
- Congressional Data Coalition: `https://congressionaldata.org`
- GovTrack.us: `https://www.govtrack.us`
- BICAM Dataset: `https://github.com/bicam-data/bicam`
