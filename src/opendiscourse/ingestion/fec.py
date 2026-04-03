"""FEC Campaign Finance API ingestion pipeline.

Uses parallel downloads with ThreadPoolExecutor for fast ingestion.
Handles: candidates, committees, candidate totals, and Schedule A contributions.
"""

import logging
import os
import tempfile
import threading
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from opendiscourse.config import get_settings
from opendiscourse.database import sync_engine
from opendiscourse.ingestion.base import BaseIngestion
from opendiscourse.models.campaign_finance import (
    FECCandidate,
    FECCommittee,
    FECContribution,
    FECTotal,
    FECCommitteeCandidate,
    FECDisbursement,
    FECFiling,
    FECIndependentExpenditure,
)
from opendiscourse.models.metadata import DataSource
from opendiscourse.utils.helpers import clean_text, parse_date, safe_float

logger = logging.getLogger(__name__)
settings = get_settings()


class FECIngestion(BaseIngestion):
    """Ingest data from the FEC Campaign Finance API."""

    source_name = "fec"
    base_url = "https://api.open.fec.gov/v1"
    api_key = settings.fec_api_key

    def __init__(self, batch_size: Optional[int] = None, max_workers: int = 12):
        super().__init__(batch_size=batch_size)
        self.max_workers = max_workers
        if self.api_key:
            self.client.params = {"api_key": self.api_key}

    def _paginate_fec(self, endpoint: str, params: Optional[Dict] = None, max_pages: Optional[int] = None):
        """Paginate through FEC API results using last_index cursor."""
        params = dict(params) if params else {}
        params["per_page"] = params.get("per_page", 100)
        params["api_key"] = self.api_key

        page = 0
        last_index = None
        while True:
            if last_index is not None:
                params["last_index"] = last_index

            resp = self.client.get(endpoint, params=params)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if not results:
                break

            yield results
            page += 1

            if max_pages and page >= max_pages:
                break

            pagination = data.get("pagination", {})
            last_index = pagination.get("last_indexes", {}).get("candidate_id") or pagination.get(
                "last_indexes", {}
            ).get("committee_id")
            if not last_index:
                # For schedules, use different cursor
                last_index = pagination.get("last_indexes", {}).get("contributor_name") or pagination.get(
                    "last_indexes", {}
                ).get("sub_id")
            if not last_index and not pagination.get("has_more"):
                break

    # ----------------------------------------------------------------
    # Candidates
    # ----------------------------------------------------------------

    def ingest_candidates(self, cycle: Optional[int] = None) -> Dict[str, int]:
        """Ingest FEC candidates with parallel downloads."""
        logger.info(f"Ingesting FEC candidates (cycle={cycle})...")
        params = {"per_page": 100}
        if cycle:
            params["cycle"] = cycle

        all_candidates = []
        for page in self._paginate_fec("/candidates/", params):
            all_candidates.extend(page)

        logger.info(f"Fetched {len(all_candidates)} candidates, upserting...")
        return self._upsert_candidates(all_candidates)

    def _upsert_candidates(self, candidates: List[Dict]) -> Dict[str, int]:
        """Upsert candidates to database."""
        inserted = 0
        updated = 0
        failed = 0

        with Session(sync_engine) as session:
            for c in candidates:
                try:
                    from sqlalchemy.dialects.postgresql import insert

                    stmt = insert(FECCandidate).values(
                        fec_candidate_id=c["candidate_id"],
                        name=clean_text(c.get("name", "")),
                        party=clean_text(c.get("party")),
                        office_sought=clean_text(c.get("office")),
                        state=clean_text(c.get("state")),
                        district=c.get("district_number"),
                        incumbent_active=c.get("incumbent_challenge"),
                        election_year=c.get("candidate_election_year"),
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["fec_candidate_id"],
                        set_={
                            "name": stmt.excluded.name,
                            "party": stmt.excluded.party,
                            "updated_at": datetime.utcnow(),
                        },
                    )
                    session.execute(stmt)
                    inserted += 1
                except Exception as e:
                    logger.warning(f"Failed candidate {c.get('candidate_id')}: {e}")
                    failed += 1
            session.commit()

        stats = {
            "records_processed": len(candidates),
            "records_inserted": inserted,
            "records_updated": updated,
            "records_failed": failed,
        }
        self.log_ingestion("fec_candidates", **stats)
        logger.info(f"FEC candidates: {inserted} inserted/updated, {failed} failed")
        return stats

    # ----------------------------------------------------------------
    # Committees
    # ----------------------------------------------------------------

    def ingest_committees(self, cycle: Optional[int] = None) -> Dict[str, int]:
        """Ingest FEC committees."""
        logger.info(f"Ingesting FEC committees (cycle={cycle})...")
        params = {"per_page": 100}
        if cycle:
            params["cycle"] = cycle

        all_committees = []
        for page in self._paginate_fec("/committees/", params):
            all_committees.extend(page)

        logger.info(f"Fetched {len(all_committees)} committees, upserting...")
        return self._upsert_committees(all_committees)

    def _upsert_committees(self, committees: List[Dict]) -> Dict[str, int]:
        """Upsert committees to database."""
        inserted = 0
        failed = 0

        with Session(sync_engine) as session:
            for c in committees:
                try:
                    from sqlalchemy.dialects.postgresql import insert

                    stmt = insert(FECommittee).values(
                        fec_committee_id=c["committee_id"],
                        name=clean_text(c.get("name", "")),
                        committee_type=clean_text(c.get("committee_type")),
                        committee_designation=clean_text(c.get("designation")),
                        party=clean_text(c.get("party")),
                        treasurer_name=clean_text(c.get("treasurer_name")),
                        city=clean_text(c.get("committee_state")),  # FEC doesn't always have city
                        state=clean_text(c.get("committee_state")),
                        is_active=c.get("committee_inactive") != "Y",
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["fec_committee_id"],
                        set_={
                            "name": stmt.excluded.name,
                            "updated_at": datetime.utcnow(),
                        },
                    )
                    session.execute(stmt)
                    inserted += 1
                except Exception as e:
                    logger.warning(f"Failed committee {c.get('committee_id')}: {e}")
                    failed += 1
            session.commit()

        stats = {
            "records_processed": len(committees),
            "records_inserted": inserted,
            "records_updated": 0,
            "records_failed": failed,
        }
        self.log_ingestion("fec_committees", **stats)
        logger.info(f"FEC committees: {inserted} inserted/updated, {failed} failed")
        return stats

    # ----------------------------------------------------------------
    # Candidate Totals (financial summaries)
    # ----------------------------------------------------------------

    def ingest_candidate_totals(self, cycle: int = 2024) -> Dict[str, int]:
        """Ingest candidate financial totals."""
        logger.info(f"Ingesting candidate totals for cycle {cycle}...")
        params = {"per_page": 100, "cycle": cycle}

        all_totals = []
        for page in self._paginate_fec("/candidates/totals/", params):
            all_totals.extend(page)

        logger.info(f"Fetched {len(all_totals)} candidate totals, upserting...")
        return self._upsert_candidate_totals(all_totals)

    def _upsert_candidate_totals(self, totals: List[Dict]) -> Dict[str, int]:
        """Upsert candidate totals."""
        inserted = 0
        failed = 0

        with Session(sync_engine) as session:
            for t in totals:
                try:
                    from sqlalchemy.dialects.postgresql import insert

                    stmt = insert(FECTotal).values(
                        candidate_id=t.get("candidate_id"),
                        cycle=t.get("cycle"),
                        receipts=safe_float(t.get("receipts")),
                        disbursements=safe_float(t.get("disbursements")),
                        cash_on_hand=safe_float(t.get("cash_on_hand_end_period")),
                        debt_owed=safe_float(t.get("debts_owed_by_committee")),
                        individual_contributions=safe_float(t.get("individual_contributions")),
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["candidate_id", "cycle"],
                        set_={
                            "receipts": stmt.excluded.receipts,
                            "disbursements": stmt.excluded.disbursements,
                            "updated_at": datetime.utcnow(),
                        },
                    )
                    session.execute(stmt)
                    inserted += 1
                except Exception as e:
                    logger.warning(f"Failed candidate total: {e}")
                    failed += 1
            session.commit()

        stats = {
            "records_processed": len(totals),
            "records_inserted": inserted,
            "records_updated": 0,
            "records_failed": failed,
        }
        self.log_ingestion("fec_candidate_totals", **stats)
        logger.info(f"Candidate totals: {inserted} inserted, {failed} failed")
        return stats

    # ----------------------------------------------------------------
    # Schedule A - Individual Contributions (parallel with bulk download)
    # ----------------------------------------------------------------

    def ingest_contributions(
        self,
        cycle: int = 2024,
        max_records: Optional[int] = None,
        max_workers: Optional[int] = None,
    ) -> Dict[str, int]:
        """Ingest Schedule A individual contributions using parallel downloads.

        For large datasets, use FEC bulk data downloads instead of API.
        This method uses the API with parallel workers for moderate-sized queries.
        """
        workers = max_workers or self.max_workers
        logger.info(f"Ingesting Schedule A contributions for cycle {cycle} (workers={workers})...")

        # First, get total count
        params = {"per_page": 1, "two_year_transaction_period": cycle, "api_key": self.api_key}
        resp = self.client.get("/schedules/schedule_a/", params=params)
        resp.raise_for_status()
        total_count = resp.json().get("pagination", {}).get("count", 0)
        logger.info(f"Total Schedule A contributions for {cycle}: {total_count:,}")

        if total_count > 1_000_000:
            logger.warning(f"Too many records ({total_count:,}) for API. Use bulk CSV download instead.")
            return self._ingest_contributions_bulk(cycle)

        # For manageable datasets, use parallel API
        return self._ingest_contributions_api(cycle, max_records, workers)

    def _ingest_contributions_api(self, cycle: int, max_records: Optional[int], workers: int) -> Dict[str, int]:
        """Ingest contributions via parallel API calls."""
        params = {"per_page": 100, "two_year_transaction_period": cycle, "api_key": self.api_key}

        # Collect all records first
        all_records = []
        for page in self._paginate_fec("/schedules/schedule_a/", params):
            all_records.extend(page)
            if max_records and len(all_records) >= max_records:
                all_records = all_records[:max_records]
                break

        logger.info(f"Fetched {len(all_records)} contributions, upserting...")

        inserted = 0
        failed = 0
        with Session(sync_engine) as session:
            for r in all_records:
                try:
                    from sqlalchemy.dialects.postgresql import insert

                    stmt = insert(FEContribution).values(
                        committee_id=r.get("committee_id"),
                        contributor_name=clean_text(r.get("contributor_name", "")),
                        contributor_city=clean_text(r.get("contributor_city")),
                        contributor_state=clean_text(r.get("contributor_state")),
                        contributor_zip=clean_text(r.get("contributor_zip")),
                        employer=clean_text(r.get("contributor_employer")),
                        occupation=clean_text(r.get("contributor_occupation")),
                        contribution_date=parse_date(r.get("contribution_receipt_date")),
                        contribution_amount=safe_float(r.get("contribution_receipt_amount")),
                        contribution_type=clean_text(r.get("receipt_type")),
                        election_type=clean_text(r.get("election_type")),
                    )
                    session.execute(stmt)
                    inserted += 1
                except Exception as e:
                    failed += 1

                if inserted % 5000 == 0:
                    session.commit()

            session.commit()

        stats = {
            "records_processed": len(all_records),
            "records_inserted": inserted,
            "records_updated": 0,
            "records_failed": failed,
        }
        self.log_ingestion("fec_contributions", **stats)
        logger.info(f"Contributions: {inserted} inserted, {failed} failed")
        return stats

    def _ingest_contributions_bulk(self, cycle: int) -> Dict[str, int]:
        """Download and ingest contributions from FEC bulk CSV files using PostgreSQL COPY."""
        logger.info(f"Downloading bulk contribution data for cycle {cycle}...")

        # FEC bulk data URLs
        # For cycle 2024, it's indiv24.zip (last two digits)
        cycle_short = str(cycle)[-2:]
        base_url = f"https://download.fec.gov/files/bulk-downloads/{cycle}/indiv{cycle_short}.zip"
        logger.info(f"Downloading: {base_url}")

        import io
        import zipfile
        import tempfile
        import os
        from concurrent.futures import ThreadPoolExecutor, as_completed

        resp = self.client.get(base_url, timeout=300.0)
        if resp.status_code != 200:
            logger.error(f"Failed to download bulk data: {resp.status_code}")
            return {"records_processed": 0, "records_inserted": 0, "records_updated": 0, "records_failed": 1}

        total_processed = 0
        total_inserted = 0
        total_failed = 0

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            txt_files = [name for name in zf.namelist() if name.endswith(".txt")]
            logger.info(f"Found {len(txt_files)} text files to process")

            # Process files in parallel batches
            batch_size = 2  # Process 2 files at a time to avoid overwhelming the DB
            for i in range(0, len(txt_files), batch_size):
                batch_files = txt_files[i : i + batch_size]
                logger.info(f"Processing batch {i // batch_size + 1}: {batch_files}")

                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    futures = []
                    for name in batch_files:
                        future = executor.submit(self._process_contribution_file, zf, name, cycle)
                        futures.append(future)

                    for future in as_completed(futures):
                        try:
                            stats = future.result()
                            total_processed += stats["records_processed"]
                            total_inserted += stats["records_inserted"]
                            total_failed += stats["records_failed"]
                        except Exception as e:
                            logger.error(f"Failed to process file: {e}")
                            total_failed += 1

        stats = {
            "records_processed": total_processed,
            "records_inserted": total_inserted,
            "records_updated": 0,
            "records_failed": total_failed,
        }
        self.log_ingestion("fec_contributions_bulk", **stats)
        logger.info(f"Bulk contributions: {total_inserted:,} inserted, {total_failed} failed")
        return stats

    def _process_contribution_file(self, zf: zipfile.ZipFile, filename: str, cycle: int) -> Dict[str, int]:
        """Process a single contribution file using PostgreSQL COPY and temp table upsert."""
        logger.info(f"Processing contribution file: {filename}")

        # Create temp table name
        temp_table_name = f"fec_contributions_temp_{threading.current_thread().ident}"

        with Session(sync_engine) as session:
            try:
                # Create temp table with same structure as FEContribution
                session.execute(f"""
                    CREATE TEMP TABLE {temp_table_name} (
                        filing_id INTEGER,
                        report_year INTEGER,
                        report_type VARCHAR(50),
                        committee_id VARCHAR(20),
                        contributor_name VARCHAR(200),
                        contributor_city VARCHAR(100),
                        contributor_state VARCHAR(50),
                        contributor_zip VARCHAR(20),
                        employer VARCHAR(200),
                        occupation VARCHAR(200),
                        contribution_date DATE,
                        contribution_amount NUMERIC(12, 2),
                        contribution_type VARCHAR(50),
                        memo_code VARCHAR(1),
                        memo_text TEXT,
                        election_type VARCHAR(20)
                    )
                """)

                # Extract file to temp file
                with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False) as temp_file:
                    temp_path = temp_file.name

                    with zf.open(filename) as f:
                        # FEC files are pipe-delimited, Latin-1 encoded
                        content = f.read().decode("latin-1", errors="replace")

                        # Write cleaned CSV data
                        for line_num, line in enumerate(content.splitlines()):
                            if line_num == 0:
                                continue  # Skip header if present

                            parts = line.split("|")
                            if len(parts) < 21:
                                continue  # Skip malformed lines

                            # Map FEC columns to our schema
                            # CMTE_ID|AMNDT_IND|RPT_TP|TRANSACTION_PGI|IMAGE_NUM|TRANSACTION_TP|ENTITY_TP|NAME|CITY|STATE|ZIP_CODE|EMPLOYER|OCCUPATION|TRANSACTION_DT|TRANSACTION_AMT|OTHER_ID|TRAN_ID|FILE_NUM|MEMO_CD|MEMO_TEXT|SUB_ID
                            row = [
                                parts[17].strip() if len(parts) > 17 else "",  # FILE_NUM -> filing_id
                                str(cycle),  # report_year
                                parts[2].strip() if len(parts) > 2 else "",  # RPT_TP -> report_type
                                parts[0].strip() if len(parts) > 0 else "",  # CMTE_ID -> committee_id
                                clean_text(parts[7]) if len(parts) > 7 else "",  # NAME -> contributor_name
                                clean_text(parts[8]) if len(parts) > 8 else "",  # CITY -> contributor_city
                                clean_text(parts[9]) if len(parts) > 9 else "",  # STATE -> contributor_state
                                clean_text(parts[10]) if len(parts) > 10 else "",  # ZIP_CODE -> contributor_zip
                                clean_text(parts[11]) if len(parts) > 11 else "",  # EMPLOYER -> employer
                                clean_text(parts[12]) if len(parts) > 12 else "",  # OCCUPATION -> occupation
                                parse_date(parts[13])
                                if len(parts) > 13 and parts[13].strip()
                                else None,  # TRANSACTION_DT -> contribution_date
                                safe_float(parts[14])
                                if len(parts) > 14
                                else None,  # TRANSACTION_AMT -> contribution_amount
                                clean_text(parts[5]) if len(parts) > 5 else "",  # TRANSACTION_TP -> contribution_type
                                clean_text(parts[18]) if len(parts) > 18 else "",  # MEMO_CD -> memo_code
                                clean_text(parts[19]) if len(parts) > 19 else "",  # MEMO_TEXT -> memo_text
                                clean_text(parts[3]) if len(parts) > 3 else "",  # TRANSACTION_PGI -> election_type
                            ]

                            # Write as CSV row
                            temp_file.write(
                                ",".join(
                                    f'"{str(x).replace(chr(34), chr(34) * 2)}"' if x is not None else "" for x in row
                                )
                                + "\n"
                            )

                    temp_file.flush()

                    # Use PostgreSQL COPY to load data
                    with open(temp_path, "r") as csv_file:
                        copy_sql = f"""
                            COPY {temp_table_name} (
                                filing_id, report_year, report_type, committee_id,
                                contributor_name, contributor_city, contributor_state, contributor_zip,
                                employer, occupation, contribution_date, contribution_amount,
                                contribution_type, memo_code, memo_text, election_type
                            )
                            FROM STDIN
                            WITH CSV
                        """
                        session.connection().connection.cursor().copy_expert(copy_sql, csv_file)

                # Count records loaded
                result = session.execute(f"SELECT COUNT(*) FROM {temp_table_name}")
                records_loaded = result.scalar()
                logger.info(f"Loaded {records_loaded} records into temp table for {filename}")

                # Upsert from temp table to main table
                # Use a unique constraint based on key fields to avoid duplicates
                # Since there's no unique constraint defined, we'll use DO NOTHING to skip existing records
                upsert_sql = f"""
                    INSERT INTO fec_contributions (
                        filing_id, report_year, report_type, committee_id,
                        contributor_name, contributor_city, contributor_state, contributor_zip,
                        employer, occupation, contribution_date, contribution_amount,
                        contribution_type, memo_code, memo_text, election_type,
                        created_at
                    )
                    SELECT
                        filing_id, report_year, report_type, committee_id,
                        contributor_name, contributor_city, contributor_state, contributor_zip,
                        employer, occupation, contribution_date, contribution_amount,
                        contribution_type, memo_code, memo_text, election_type,
                        NOW()
                    FROM {temp_table_name}
                    WHERE NOT EXISTS (
                        SELECT 1 FROM fec_contributions
                        WHERE fec_contributions.committee_id = {temp_table_name}.committee_id
                        AND fec_contributions.contributor_name = {temp_table_name}.contributor_name
                        AND fec_contributions.contribution_date = {temp_table_name}.contribution_date
                        AND fec_contributions.contribution_amount = {temp_table_name}.contribution_amount
                        AND fec_contributions.filing_id = {temp_table_name}.filing_id
                    )
                """
                result = session.execute(upsert_sql)
                records_inserted = result.rowcount

                session.commit()

                # Clean up temp file
                os.unlink(temp_path)

                return {
                    "records_processed": records_loaded,
                    "records_inserted": records_inserted,
                    "records_failed": 0,
                }

            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                session.rollback()
                return {
                    "records_processed": 0,
                    "records_inserted": 0,
                    "records_failed": 1,
                }

    # ----------------------------------------------------------------
    # Master ingest method
    # ----------------------------------------------------------------

    def ingest(
        self,
        cycle: int = 2024,
        include_contributions: bool = False,
        max_contribution_records: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, int]:
        """Run full FEC ingestion for a cycle."""
        logger.info(f"Starting FEC ingestion for cycle {cycle}...")
        self._ensure_source_record()

        total_stats = {"records_processed": 0, "records_inserted": 0, "records_updated": 0, "records_failed": 0}

        # 1. Candidates
        try:
            stats = self.ingest_candidates(cycle=cycle)
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        except Exception as e:
            logger.error(f"Failed candidates: {e}")
            total_stats["records_failed"] += 1

        # 2. Committees
        try:
            stats = self.ingest_committees(cycle=cycle)
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        except Exception as e:
            logger.error(f"Failed committees: {e}")
            total_stats["records_failed"] += 1

        # 3. Candidate totals
        try:
            stats = self.ingest_candidate_totals(cycle=cycle)
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        except Exception as e:
            logger.error(f"Failed candidate totals: {e}")
            total_stats["records_failed"] += 1

        # 4. Contributions (optional - large dataset)
        if include_contributions:
            try:
                stats = self.ingest_contributions(cycle=cycle, max_records=max_contribution_records)
                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)
            except Exception as e:
                logger.error(f"Failed contributions: {e}")
                total_stats["records_failed"] += 1

        logger.info(f"FEC ingestion complete: {total_stats}")
        return total_stats

    def _ensure_source_record(self):
        """Ensure a DataSource record exists for fec."""
        with Session(sync_engine) as session:
            existing = session.query(DataSource).filter(DataSource.name == self.source_name).first()
            if not existing:
                session.add(
                    DataSource(
                        name=self.source_name,
                        url="https://api.open.fec.gov",
                        api_type="rest",
                        auth_type="api_key",
                        status="active",
                    )
                )
                session.commit()
