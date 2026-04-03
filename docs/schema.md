# Database Schema Documentation

## Overview
PostgreSQL 16 database with 40+ tables across 5 domains: Congress, Campaign Finance, Lobbying, Stock Disclosures, and Metadata.

---

## Domain 1: Congressional Data

### congresses
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| congress_number | INTEGER | UNIQUE, NOT NULL | 108, 109, 110, etc. |
| start_date | DATE | NOT NULL | |
| end_date | DATE | NOT NULL | |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | DEFAULT NOW() | |

### chambers
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| code | VARCHAR(10) | UNIQUE, NOT NULL | 'house', 'senate', 'joint' |
| name | VARCHAR(50) | NOT NULL | |

### members
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| bioguide_id | VARCHAR(20) | UNIQUE | Congress.gov ID |
| govtrack_id | INTEGER | UNIQUE | GovTrack ID |
| thomas_id | VARCHAR(20) | | Legacy THOMAS ID |
| lis_id | VARCHAR(20) | | Senate LIS ID |
| fec_id | VARCHAR(20) | | FEC candidate ID |
| opensecrets_id | VARCHAR(20) | | OpenSecrets ID |
| first_name | VARCHAR(100) | NOT NULL | |
| last_name | VARCHAR(100) | NOT NULL | |
| date_of_birth | DATE | | |
| gender | VARCHAR(20) | | |
| party | VARCHAR(50) | | Current party |
| state | VARCHAR(50) | NOT NULL | |
| district | INTEGER | | NULL for Senators |
| chamber | VARCHAR(20) | | 'house' or 'senate' |
| twitter_id | VARCHAR(100) | | |
| is_current | BOOLEAN | DEFAULT TRUE | |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | DEFAULT NOW() | |

### member_terms
Tracks changes in membership over time (party changes, district changes, etc.)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| member_id | INTEGER | FK -> members | |
| congress_id | INTEGER | FK -> congresses | |
| chamber | VARCHAR(20) | NOT NULL | |
| party | VARCHAR(50) | NOT NULL | |
| class | INTEGER | | Senate class (1, 2, 3) |
| start_date | DATE | NOT NULL | |
| end_date | DATE | | |
| how_ended | VARCHAR(50) | | 'term_expired', 'resigned', 'died' | |

### committees
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| congress_gov_id | VARCHAR(50) | UNIQUE | |
| name | VARCHAR(200) | NOT NULL | |
| chamber | VARCHAR(20) | | 'house', 'senate', 'joint' |
| committee_type | VARCHAR(50) | | 'standing', 'select', 'joint', 'subcommittee' |
| parent_committee_id | INTEGER | FK -> committees | For subcommittees |
| congress_id | INTEGER | FK -> congresses | |
| is_current | BOOLEAN | DEFAULT TRUE | |

### committee_memberships
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| committee_id | INTEGER | FK -> committees | |
| member_id | INTEGER | FK -> members | |
| congress_id | INTEGER | FK -> congresses | |
| role | VARCHAR(50) | | 'chair', 'ranking_member', 'member' | |

### bills
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| congress_gov_id | VARCHAR(50) | UNIQUE, NOT NULL | |
| congress_id | INTEGER | FK -> congresses | |
| bill_type | VARCHAR(20) | NOT NULL | 'hr', 's', 'hjres', 'sjres', 'hconres', 'sconres', 'hres', 'sres' |
| number | INTEGER | NOT NULL | |
| display_number | VARCHAR(50) | | 'HR 1', 'S 234' |
| title | TEXT | | |
| sponsor_id | INTEGER | FK -> members | |
| status | VARCHAR(50) | | 'introduced', 'reported', 'passed', 'enacted', 'vetoed' |
| introduced_date | DATE | | |
| latest_action_date | DATE | | |
| law_number | VARCHAR(50) | | Public law number | |

### bill_actions
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| bill_id | INTEGER | FK -> bills | |
| action_date | TIMESTAMP | NOT NULL | |
| chamber | VARCHAR(20) | | |
| action_type | VARCHAR(50) | | |
| text | TEXT | | |
| committee_id | INTEGER | FK -> committees | |

### bill_cosponsors
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| bill_id | INTEGER | FK -> bills | |
| member_id | INTEGER | FK -> members | |
| is_original_cosponsor | BOOLEAN | DEFAULT FALSE | |
| sponsorship_date | DATE | | |
| withdrawal_date | DATE | | |

### bill_committees
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| bill_id | INTEGER | FK -> bills | |
| committee_id | INTEGER | FK -> committees | |
| activity | VARCHAR(100) | | 'referred to', 'reported by', 'discharged from' | |

### bill_subjects
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| bill_id | INTEGER | FK -> bills | |
| subject_type | VARCHAR(50) | | 'legislative', 'policy_area' |
| name | VARCHAR(200) | NOT NULL | |

### bill_summaries
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| bill_id | INTEGER | FK -> bills | |
| action_date | DATE | | |
| text | TEXT | NOT NULL | |
| source | VARCHAR(50) | | 'CRS', 'LCS' |

### bill_texts
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| bill_id | INTEGER | FK -> bills | |
| version_code | VARCHAR(20) | | 'ih', 'eh', 'enr' |
| version_description | VARCHAR(200) | | |
| format | VARCHAR(20) | | 'xml', 'html', 'pdf', 'txt' |
| full_text | TEXT | | |

### votes
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| congress_gov_id | VARCHAR(50) | UNIQUE | |
| congress_id | INTEGER | FK -> congresses | |
| chamber | VARCHAR(20) | NOT NULL | |
| roll_number | INTEGER | NOT NULL | |
| vote_date | DATE | NOT NULL | |
| question | VARCHAR(200) | | 'On Passage', 'On Motion to Recommit' |
| vote_type | VARCHAR(50) | | 'YEA-AND-NAY', 'RECORDED VOTE' |
| vote_result | VARCHAR(50) | | 'Agreed to', 'Failed' |
| bill_id | INTEGER | FK -> bills | |
| total_yes | INTEGER | | |
| total_no | INTEGER | | |
| total_present | INTEGER | | |
| total_not_voting | INTEGER | | |

### vote_positions
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| vote_id | INTEGER | FK -> votes | |
| member_id | INTEGER | FK -> members | |
| position | VARCHAR(20) | | 'Yea', 'Nay', 'Present', 'Not Voting' |

### amendments
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| congress_gov_id | VARCHAR(50) | UNIQUE | |
| bill_id | INTEGER | FK -> bills | |
| amendment_type | VARCHAR(20) | | 'hamdt', 'samdt' |
| number | INTEGER | | |
| purpose | TEXT | | |
| sponsor_id | INTEGER | FK -> members | |
| status | VARCHAR(50) | | |

### nominations
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| congress_gov_id | VARCHAR(50) | UNIQUE | |
| congress_id | INTEGER | FK -> congresses | |
| position_title | TEXT | | |
| nominee_name | VARCHAR(200) | | |
| received_date | DATE | | |
| status | VARCHAR(50) | | |
| committee_id | INTEGER | FK -> committees | |

### treaties
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| congress_gov_id | VARCHAR(50) | UNIQUE | |
| congress_id | INTEGER | FK -> congresses | |
| treaty_number | INTEGER | | |
| title | TEXT | | |
| received_date | DATE | | |
| status | VARCHAR(50) | | |

### committee_reports
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| congress_gov_id | VARCHAR(50) | UNIQUE | |
| congress_id | INTEGER | FK -> congresses | |
| report_type | VARCHAR(20) | | 'h rpt', 's rpt', 'e rpt' |
| number | INTEGER | | |
| title | TEXT | | |
| committee_id | INTEGER | FK -> committees | |
| bill_id | INTEGER | FK -> bills | |

### congressional_records
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| congress_gov_id | VARCHAR(50) | UNIQUE | |
| date | DATE | NOT NULL | |
| volume | VARCHAR(20) | | |
| section | VARCHAR(20) | | 'Daily Digest', 'Senate', 'House' |
| full_text | TEXT | | |

### federal_register
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| document_number | VARCHAR(50) | UNIQUE | |
| date | DATE | NOT NULL | |
| type | VARCHAR(50) | | 'rule', 'proposed_rule', 'notice', 'presidential_document' |
| title | TEXT | | |
| agency | VARCHAR(200) | | |
| full_text | TEXT | | |

### cfr_entries
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| title | INTEGER | NOT NULL | CFR Title number |
| part | INTEGER | NOT NULL | |
| section | INTEGER | | |
| heading | TEXT | | |
| text | TEXT | | |
| last_updated | DATE | | |

---

## Domain 2: Campaign Finance

### fec_candidates
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| fec_candidate_id | VARCHAR(20) | UNIQUE, NOT NULL | |
| name | VARCHAR(200) | NOT NULL | |
| party | VARCHAR(50) | | |
| office_sought | VARCHAR(50) | | 'P', 'S', 'H' |
| state | VARCHAR(50) | | |
| district | INTEGER | | |
| election_year | INTEGER | | |

### fec_committees
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| fec_committee_id | VARCHAR(20) | UNIQUE, NOT NULL | |
| name | VARCHAR(300) | NOT NULL | |
| committee_type | VARCHAR(50) | | 'H', 'S', 'P', 'X', 'Y', 'Z' |
| party | VARCHAR(50) | | |
| treasurer_name | VARCHAR(200) | | |
| is_active | BOOLEAN | DEFAULT TRUE | |

### fec_contributions (Schedule A)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| committee_id | VARCHAR(20) | FK -> fec_committees | |
| contributor_name | VARCHAR(200) | | |
| contributor_city | VARCHAR(100) | | |
| contributor_state | VARCHAR(50) | | |
| employer | VARCHAR(200) | | |
| occupation | VARCHAR(200) | | |
| contribution_date | DATE | NOT NULL | |
| contribution_amount | NUMERIC(12,2) | NOT NULL | |
| contribution_type | VARCHAR(50) | | '15', '15E', '15J' |
| election_type | VARCHAR(20) | | 'P', 'G', 'R', 'O' |

### fec_disbursements (Schedule B)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| committee_id | VARCHAR(20) | FK -> fec_committees | |
| payee_name | VARCHAR(200) | | |
| disbursement_date | DATE | NOT NULL | |
| disbursement_amount | NUMERIC(12,2) | NOT NULL | |
| purpose | VARCHAR(200) | | |
| category | VARCHAR(100) | | |

### fec_independent_expenditures (Schedule E)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| committee_id | VARCHAR(20) | FK -> fec_committees | |
| candidate_id | VARCHAR(20) | FK -> fec_candidates | |
| support_oppose | VARCHAR(10) | | 'S' or 'O' |
| expenditure_date | DATE | NOT NULL | |
| expenditure_amount | NUMERIC(12,2) | NOT NULL | |

### fec_filings
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| filing_number | INTEGER | UNIQUE, NOT NULL | |
| committee_id | VARCHAR(20) | FK -> fec_committees | |
| report_type | VARCHAR(50) | | |
| report_year | INTEGER | | |
| coverage_start | DATE | | |
| coverage_end | DATE | | |
| receipt_date | DATE | | |
| pdf_url | TEXT | | |

### fec_totals
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| committee_id | VARCHAR(20) | FK -> fec_committees | |
| report_year | INTEGER | | |
| receipts | NUMERIC(14,2) | | |
| disbursements | NUMERIC(14,2) | | |
| cash_on_hand | NUMERIC(14,2) | | |
| debt_owed | NUMERIC(14,2) | | |
| individual_contributions | NUMERIC(14,2) | | |
| pac_contributions | NUMERIC(14,2) | | |

---

## Domain 3: Lobbying & OpenSecrets

### opensecrets_legislators
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| member_id | INTEGER | FK -> members | |
| opensecrets_id | VARCHAR(20) | UNIQUE | |
| firstlast | VARCHAR(200) | | |
| party | VARCHAR(50) | | |
| first_elected | INTEGER | | |

### opensecrets_contributors
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| legislator_id | INTEGER | FK -> opensecrets_legislators | |
| cycle | INTEGER | NOT NULL | |
| org_name | VARCHAR(300) | NOT NULL | |
| total | NUMERIC(14,2) | NOT NULL | |
| pacs | NUMERIC(14,2) | | |
| indivs | NUMERIC(14,2) | | |
| rank | INTEGER | | |

### opensecrets_industry_contributions
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| legislator_id | INTEGER | FK -> opensecrets_legislators | |
| cycle | INTEGER | NOT NULL | |
| industry_code | VARCHAR(10) | | |
| industry_name | VARCHAR(200) | | |
| total | NUMERIC(14,2) | | |
| pacs | NUMERIC(14,2) | | |
| indivs | NUMERIC(14,2) | | |

### lobbying_disclosures
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| filing_id | VARCHAR(50) | UNIQUE | |
| registrant_name | VARCHAR(300) | | |
| client_name | VARCHAR(300) | | |
| lobby_year | INTEGER | | |
| income | NUMERIC(14,2) | | |
| expenses | NUMERIC(14,2) | | |
| filing_date | DATE | | |

### lobbying_issues
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| disclosure_id | INTEGER | FK -> lobbying_disclosures | |
| issue_code | VARCHAR(10) | | |
| issue_description | TEXT | | |
| specific_issues | TEXT | | |

### lobbying_lobbyists
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| disclosure_id | INTEGER | FK -> lobbying_disclosures | |
| lobbyist_name | VARCHAR(200) | | |
| covered_official_position | VARCHAR(200) | | |

### lobbying_contacts
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| disclosure_id | INTEGER | FK -> lobbying_disclosures | |
| senator_bioguide_id | VARCHAR(20) | | |
| rep_bioguide_id | VARCHAR(20) | | |

---

## Domain 4: Stock/Trading Disclosures

### stock_disclosures
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| member_id | INTEGER | FK -> members | |
| filing_date | DATE | NOT NULL | |
| report_type | VARCHAR(50) | | 'periodic', 'late', 'amended' |
| report_url | TEXT | | |
| pdf_url | TEXT | | |

### stock_transactions
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| disclosure_id | INTEGER | FK -> stock_disclosures | |
| member_id | INTEGER | FK -> members | |
| filer_name | VARCHAR(200) | | Member, spouse, dependent |
| filer_relation | VARCHAR(50) | | 'self', 'spouse', 'dependent_child' |
| asset_name | VARCHAR(300) | NOT NULL | |
| asset_type | VARCHAR(50) | | 'stock', 'bond', 'mutual_fund', 'etf', 'option' |
| ticker | VARCHAR(20) | | |
| transaction_type | VARCHAR(50) | | 'purchase', 'sale', 'exchange', 'gift' |
| transaction_date | DATE | | |
| transaction_amount_low | NUMERIC(12,2) | | Range minimum |
| transaction_amount_high | NUMERIC(12,2) | | Range maximum |
| ownership_type | VARCHAR(50) | | 'joint', 'individual' |

### financial_disclosures
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| member_id | INTEGER | FK -> members | |
| year | INTEGER | NOT NULL | |
| filing_type | VARCHAR(50) | | 'senate', 'house' |
| pdf_url | TEXT | | |
| filing_date | DATE | | |

### financial_assets
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| disclosure_id | INTEGER | FK -> financial_disclosures | |
| asset_name | VARCHAR(300) | | |
| asset_type | VARCHAR(100) | | |
| value_low | NUMERIC(14,2) | | |
| value_high | NUMERIC(14,2) | | |
| income_type | VARCHAR(50) | | |
| income_low | NUMERIC(14,2) | | |
| income_high | NUMERIC(14,2) | | |

### financial_gifts
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| disclosure_id | INTEGER | FK -> financial_disclosures | |
| source_name | VARCHAR(300) | | |
| description | TEXT | | |
| value | NUMERIC(12,2) | | |

### financial_travel
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| disclosure_id | INTEGER | FK -> financial_disclosures | |
| source_name | VARCHAR(300) | | |
| destination | VARCHAR(200) | | |
| dates | VARCHAR(100) | | |
| purpose | VARCHAR(200) | | |
| amount | NUMERIC(12,2) | | |

---

## Domain 5: Metadata

### data_sources
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| name | VARCHAR(100) | UNIQUE, NOT NULL | |
| url | TEXT | | |
| api_type | VARCHAR(50) | | 'rest', 'bulk', 'scrape', 'mcp' |
| rate_limit | INTEGER | | |
| last_sync | TIMESTAMP | | |
| status | VARCHAR(50) | | 'active', 'inactive', 'error' |

### ingestion_logs
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| source_id | INTEGER | FK -> data_sources | |
| table_name | VARCHAR(100) | | |
| records_processed | INTEGER | | |
| records_inserted | INTEGER | | |
| records_updated | INTEGER | | |
| records_failed | INTEGER | | |
| started_at | TIMESTAMP | DEFAULT NOW() | |
| completed_at | TIMESTAMP | | |
| status | VARCHAR(50) | | |
| error_message | TEXT | | |
| metadata | JSONB | | |

### api_rate_limits
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| source_id | INTEGER | FK -> data_sources | |
| endpoint | VARCHAR(200) | | |
| requests_made | INTEGER | DEFAULT 0 | |
| limit_total | INTEGER | | |
| limit_reset | TIMESTAMP | | |
| last_request | TIMESTAMP | DEFAULT NOW() | |

### data_quality_checks
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PK | |
| table_name | VARCHAR(100) | | |
| check_name | VARCHAR(100) | | |
| check_type | VARCHAR(50) | | 'completeness', 'uniqueness', 'validity', 'consistency' |
| records_checked | INTEGER | | |
| records_failed | INTEGER | | |
| passed | BOOLEAN | | |
| details | JSONB | | |
| checked_at | TIMESTAMP | DEFAULT NOW() | |

---

## Indexes

### Performance Indexes
```sql
CREATE INDEX idx_bills_congress_type ON bills(congress_id, bill_type);
CREATE INDEX idx_bills_sponsor ON bills(sponsor_id);
CREATE INDEX idx_bills_status ON bills(status);
CREATE INDEX idx_bills_introduced_date ON bills(introduced_date);
CREATE INDEX idx_bill_actions_bill ON bill_actions(bill_id);
CREATE INDEX idx_bill_actions_date ON bill_actions(action_date);
CREATE INDEX idx_votes_congress_chamber ON votes(congress_id, chamber);
CREATE INDEX idx_votes_date ON votes(vote_date);
CREATE INDEX idx_votes_bill ON votes(bill_id);
CREATE INDEX idx_vote_positions_vote ON vote_positions(vote_id);
CREATE INDEX idx_vote_positions_member ON vote_positions(member_id);
CREATE INDEX idx_fec_contributions_committee ON fec_contributions(committee_id);
CREATE INDEX idx_fec_contributions_date ON fec_contributions(contribution_date);
CREATE INDEX idx_stock_transactions_member ON stock_transactions(member_id);
CREATE INDEX idx_stock_transactions_date ON stock_transactions(transaction_date);
CREATE INDEX idx_stock_transactions_ticker ON stock_transactions(ticker);
CREATE INDEX idx_opensecrets_contributors_legislator ON opensecrets_contributors(legislator_id);
CREATE INDEX idx_opensecrets_contributors_cycle ON opensecrets_contributors(cycle);
```

### Full-Text Search Indexes
```sql
CREATE INDEX idx_bills_title_search ON bills USING gin(to_tsvector('english', title));
CREATE INDEX idx_bill_actions_text_search ON bill_actions USING gin(to_tsvector('english', text));
CREATE INDEX idx_bill_summaries_text_search ON bill_summaries USING gin(to_tsvector('english', text));
CREATE INDEX idx_contributor_name_search ON fec_contributions USING gin(to_tsvector('english', contributor_name));
CREATE INDEX idx_member_name_search ON members USING gin(to_tsvector('english', first_name || ' ' || last_name));
```
