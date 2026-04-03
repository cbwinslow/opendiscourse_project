"""Congress.gov API ingestion pipeline."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from opendiscourse.config import get_settings
from opendiscourse.database import sync_engine
from opendiscourse.ingestion.base import BaseIngestion
from opendiscourse.models.congress import (
    Bill,
    Committee,
    Congress,
    Member,
    Vote,
    VotePosition,
)
from opendiscourse.models.metadata import DataSource
from opendiscourse.utils.helpers import (
    clean_text,
    parse_date,
    safe_int,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class CongressGovIngestion(BaseIngestion):
    """Ingest data from the Congress.gov API (v3)."""

    source_name = "congress.gov"
    base_url = "https://api.congress.gov/v3"
    api_key = settings.congress_gov_api_key

    def __init__(self, batch_size: Optional[int] = None):
        super().__init__(batch_size=batch_size)
        if self.api_key:
            self.client.headers["X-API-Key"] = self.api_key

    def ingest_congresses(self) -> Dict[str, int]:
        """Ingest all congress sessions."""
        logger.info("Ingesting congresses...")
        data = self.fetch_page("/congress")
        congresses = data.get("congresses", [])

        with Session(sync_engine) as session:
            records = []
            for c in congresses:
                start_year = safe_int(c.get("startYear"))
                end_year = safe_int(c.get("endYear"))
                name = c.get("name", "")
                number = safe_int(
                    name.replace("th", "")
                    .replace("nd", "")
                    .replace("rd", "")
                    .replace("st", "")
                    .replace(" Congress", "")
                    .strip()
                )
                if start_year and end_year and number:
                    records.append(
                        {
                            "congress_number": number,
                            "start_date": datetime(start_year, 1, 3).date(),
                            "end_date": datetime(end_year, 1, 3).date(),
                        }
                    )

            from sqlalchemy.dialects.postgresql import insert

            stmt = insert(Congress).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=["congress_number"],
                set_={
                    "start_date": stmt.excluded.start_date,
                    "end_date": stmt.excluded.end_date,
                    "updated_at": datetime.utcnow(),
                },
            )
            session.execute(stmt)
            session.commit()

        stats = {
            "records_processed": len(congresses),
            "records_inserted": len(records),
            "records_updated": 0,
            "records_failed": 0,
        }
        self.log_ingestion("congresses", **stats)
        logger.info(f"Ingested {len(records)} congresses")
        return stats

    def ingest_members(self, congress_number: Optional[int] = None) -> Dict[str, int]:
        """Ingest all members."""
        logger.info(f"Ingesting members (congress={congress_number})...")
        url = "/member"

        total = 0
        with Session(sync_engine) as session:
            for page in self.paginate(url, limit=250, results_key="members"):
                records = []
                for m in page:
                    terms = m.get("terms", {})
                    term_items = terms.get("item", []) if isinstance(terms, dict) else terms
                    chambers = [t.get("chamber", "").lower() for t in term_items if t.get("chamber")]
                    chamber_raw = chambers[0] if chambers else ""

                    if "senate" in chamber_raw:
                        chamber_norm = "senate"
                    elif "house" in chamber_raw:
                        chamber_norm = "house"
                    elif "joint" in chamber_raw:
                        chamber_norm = "joint"
                    else:
                        chamber_norm = chamber_raw[:20]

                    name = m.get("name", "")
                    parts = name.split(", ") if ", " in name else name.split(" ", 1)
                    last_name = parts[0] if parts else ""
                    first_name = parts[1] if len(parts) > 1 else ""

                    records.append(
                        {
                            "bioguide_id": clean_text(m.get("bioguideId")),
                            "first_name": clean_text(first_name),
                            "last_name": clean_text(last_name),
                            "party": clean_text(m.get("partyName")),
                            "state": clean_text(m.get("state")),
                            "chamber": chamber_norm,
                            "is_current": True,
                        }
                    )

                if records:
                    from sqlalchemy.dialects.postgresql import insert

                    stmt = insert(Member).values(records)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["bioguide_id"],
                        set_={
                            "first_name": stmt.excluded.first_name,
                            "last_name": stmt.excluded.last_name,
                            "party": stmt.excluded.party,
                            "state": stmt.excluded.state,
                            "chamber": stmt.excluded.chamber,
                            "updated_at": datetime.utcnow(),
                        },
                    )
                    session.execute(stmt)
                    total += len(records)

            session.commit()

        stats = {"records_processed": total, "records_inserted": total, "records_updated": 0, "records_failed": 0}
        self.log_ingestion("members", **stats)
        logger.info(f"Ingested {total} members")
        return stats

    def ingest_committees(self, congress_number: Optional[int] = None) -> Dict[str, int]:
        """Ingest committees."""
        logger.info(f"Ingesting committees (congress={congress_number})...")
        url = "/committee"

        total = 0
        with Session(sync_engine) as session:
            for page in self.paginate(url, limit=100, results_key="committees"):
                records = []
                for c in page:
                    system_code = clean_text(c.get("systemCode"))
                    records.append(
                        {
                            "congress_gov_id": system_code,
                            "name": clean_text(c.get("name")),
                            "chamber": clean_text(c.get("chamber", "").lower()),
                            "committee_type": clean_text(c.get("committeeTypeCode")),
                            "is_current": True,
                        }
                    )

                if records:
                    from sqlalchemy.dialects.postgresql import insert

                    stmt = insert(Committee).values(records)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["congress_gov_id"],
                        set_={
                            "name": stmt.excluded.name,
                            "updated_at": datetime.utcnow(),
                        },
                    )
                    session.execute(stmt)
                    total += len(records)

            session.commit()

        stats = {"records_processed": total, "records_inserted": total, "records_updated": 0, "records_failed": 0}
        self.log_ingestion("committees", **stats)
        logger.info(f"Ingested {total} committees")
        return stats

    def ingest_bills(
        self,
        congress_number: int = 118,
        bill_type: Optional[str] = None,
    ) -> Dict[str, int]:
        """Ingest bills for a given congress, optionally filtered by type."""
        logger.info(f"Ingesting bills (congress={congress_number}, type={bill_type})...")
        url = f"/bill/{congress_number}"
        if bill_type:
            url = f"/bill/{congress_number}/{bill_type}"

        total_processed = 0
        total_inserted = 0
        total_failed = 0

        with Session(sync_engine) as session:
            for page in self.paginate(url, limit=250, results_key="bills"):
                seen_ids = set()
                records = []
                for b in page:
                    try:
                        cgov_id = clean_text(b.get("url", "").split("/")[-1].replace("?format=json", ""))
                        if not cgov_id or cgov_id in seen_ids:
                            continue
                        seen_ids.add(cgov_id)
                        records.append(
                            {
                                "congress_gov_id": cgov_id,
                                "congress_id": safe_int(b.get("congress")),
                                "bill_type": clean_text(b.get("type", "").lower()),
                                "number": safe_int(b.get("number")),
                                "display_number": clean_text(b.get("updateDate")),
                                "title": clean_text(b.get("title")),
                                "status": clean_text(b.get("latestAction", {}).get("actionDate")),
                                "introduced_date": parse_date(b.get("introducedDate")),
                                "latest_action_date": parse_date(b.get("latestAction", {}).get("actionDate")),
                                "latest_action": clean_text(b.get("latestAction", {}).get("text")),
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to parse bill: {e}")
                        total_failed += 1

                if records:
                    from sqlalchemy.dialects.postgresql import insert

                    stmt = insert(Bill).values(records)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["congress_gov_id"],
                        set_={
                            "title": stmt.excluded.title,
                            "status": stmt.excluded.status,
                            "latest_action_date": stmt.excluded.latest_action_date,
                            "latest_action": stmt.excluded.latest_action,
                            "updated_at": datetime.utcnow(),
                        },
                    )
                    session.execute(stmt)
                    total_inserted += len(records)

                total_processed += len(records)

            session.commit()

        stats = {
            "records_processed": total_processed,
            "records_inserted": total_inserted,
            "records_updated": 0,
            "records_failed": total_failed,
        }
        self.log_ingestion("bills", **stats)
        logger.info(f"Ingested {total_processed} bills ({total_failed} failed)")
        return stats

    def ingest_votes(self, congress_number: int = 118) -> Dict[str, int]:
        """Ingest roll call votes - not available in v3 API."""
        logger.info(f"Ingesting votes for congress {congress_number}...")
        logger.warning("Votes endpoint not available in Congress.gov v3 API - skipping")
        return {"records_processed": 0, "records_inserted": 0, "records_updated": 0, "records_failed": 0}

    def ingest(self, congress_number: int = 118, **kwargs) -> Dict[str, int]:
        """Run full Congress.gov ingestion for a given congress."""
        logger.info(f"Starting Congress.gov ingestion for congress {congress_number}...")
        self._ensure_source_record()

        total_stats = {"records_processed": 0, "records_inserted": 0, "records_updated": 0, "records_failed": 0}

        for method_name in [
            "ingest_congresses",
            "ingest_members",
            "ingest_committees",
            "ingest_bills",
        ]:
            method = getattr(self, method_name)
            try:
                if method_name in ("ingest_members", "ingest_committees", "ingest_bills"):
                    stats = method(congress_number=congress_number)
                else:
                    stats = method()

                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)
            except Exception as e:
                logger.error(f"Failed {method_name}: {e}")
                total_stats["records_failed"] += 1

        logger.info(f"Congress.gov ingestion complete: {total_stats}")
        return total_stats

    def _ensure_source_record(self):
        """Ensure a DataSource record exists for congress.gov."""
        with Session(sync_engine) as session:
            existing = session.query(DataSource).filter(DataSource.name == self.source_name).first()
            if not existing:
                session.add(
                    DataSource(
                        name=self.source_name,
                        url=self.base_url,
                        api_type="rest",
                        auth_type="api_key",
                        status="active",
                    )
                )
                session.commit()
