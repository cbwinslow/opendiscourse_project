"""GovInfo bulk data ingestion pipeline.

Uses GovInfo.gov sitemaps and bulk data downloads to fetch:
- Bill text (BILLS collection - XML format)
- Bill status (BILLSTATUS bulk collection)
- Congressional Record (CREC collection)
- Federal Register (FR collection)

The GovInfo REST API is unreliable (frequent 500 errors), so we use
direct sitemap/bulk data downloads instead.
"""

import logging
import os
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import httpx
from lxml import etree
from sqlalchemy.orm import Session

from opendiscourse.config import get_settings
from opendiscourse.database import sync_engine
from opendiscourse.ingestion.base import BaseIngestion
from opendiscourse.models.congress import (
    Bill,
    BillText,
    CongressionalRecord,
    FederalRegister,
)
from opendiscourse.models.metadata import DataSource
from opendiscourse.utils.helpers import clean_text, parse_date

logger = logging.getLogger(__name__)
settings = get_settings()

# GovInfo bulk data and sitemap URLs
GOVINFO_BASE = "https://www.govinfo.gov"
BULKDATA_BASE = f"{GOVINFO_BASE}/bulkdata"
SITEMAP_BASE = f"{GOVINFO_BASE}/sitemap"

# Bill text version code descriptions
VERSION_DESCRIPTIONS = {
    "ih": "Introduced in House",
    "eh": "Engrossed in House",
    "enr": "Enrolled Bill",
    "rfh": "Referred in House",
    "rh": "Reported in House",
    "pcs": "Public Print Senate",
    "isc": "Introduced in Senate",
    "es": "Engrossed in Senate",
    "srs": "Submitted in Senate",
    "rs": "Reported in Senate",
}


class GovInfoIngestion(BaseIngestion):
    """Ingest data from GovInfo bulk data and sitemaps."""

    source_name = "govinfo"
    base_url = GOVINFO_BASE
    api_key = settings.govinfo_api_key

    def __init__(self, batch_size: Optional[int] = None):
        super().__init__(batch_size=batch_size)
        self.download_dir = Path(settings.data_dir) / "govinfo"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------
    # Sitemap parsing
    # ----------------------------------------------------------------

    def _fetch_sitemap_index(self, collection: str) -> List[str]:
        """Fetch sitemap index for a collection and return sitemap URLs."""
        # GovInfo uses different URL patterns for different collections
        url_patterns = {
            "BILLSTATUS": f"{SITEMAP_BASE}/bulkdata/BILLSTATUS/sitemapindex.xml",
            "BILLS": f"{SITEMAP_BASE}/BILLS_sitemap_index.xml",
            "BILLSUM": f"{SITEMAP_BASE}/BILLSUM_sitemap_index.xml",
            "CREC": f"{SITEMAP_BASE}/CREC_sitemap_index.xml",
            "FR": f"{SITEMAP_BASE}/FR_sitemap_index.xml",
            "CFR": f"{SITEMAP_BASE}/CFR_sitemap_index.xml",
            "CRPT": f"{SITEMAP_BASE}/CRPT_sitemap_index.xml",
            "PLAW": f"{SITEMAP_BASE}/PLAW_sitemap_index.xml",
        }
        url = url_patterns.get(collection, f"{SITEMAP_BASE}/{collection}_sitemap_index.xml")

        logger.info(f"Fetching sitemap index: {url}")
        resp = self.client.get(url)
        resp.raise_for_status()

        root = etree.fromstring(resp.content)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        return [loc.text for loc in root.findall(".//s:loc", ns)]

    def _fetch_sitemap(self, url: str) -> List[Dict[str, str]]:
        """Fetch a single sitemap and return package entries."""
        resp = self.client.get(url)
        resp.raise_for_status()

        root = etree.fromstring(resp.content)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        entries = []
        for entry in root.findall(".//s:url", ns):
            loc = entry.find("s:loc", ns)
            lastmod = entry.find("s:lastmod", ns)
            if loc is not None:
                entries.append(
                    {
                        "url": loc.text,
                        "lastmod": lastmod.text if lastmod is not None else None,
                    }
                )
        return entries

    def _download_package(self, url: str) -> Optional[bytes]:
        """Download a GovInfo package ZIP file."""
        logger.debug(f"Downloading: {url}")
        resp = self.client.get(url, timeout=60.0)
        if resp.status_code == 200:
            return resp.content
        return None

    def _extract_xml_from_zip(self, zip_data: bytes) -> Optional[bytes]:
        """Extract the first XML file from a ZIP archive."""
        import io

        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            for name in zf.namelist():
                if name.endswith(".xml"):
                    return zf.read(name)
        return None

    def _process_entries_batch(self, entries: List[Dict[str, str]], process_fn, batch_label: str) -> Dict[str, int]:
        """Process a batch of entries using thread pool for parallel downloads.

        Args:
            entries: List of entry dicts with 'url' key
            process_fn: Callable that takes xml_data and returns True if updated
            batch_label: Label for logging

        Returns:
            Dict with processed, updated, failed counts
        """
        processed = 0
        updated = 0
        failed = 0
        results_lock = __import__("threading").Lock()

        def process_one(entry):
            nonlocal processed, updated, failed
            try:
                xml_data = self._download_package(entry["url"])
                if not xml_data:
                    with results_lock:
                        failed += 1
                    return
                result = process_fn(xml_data)
                with results_lock:
                    processed += 1
                    if result:
                        updated += 1
            except Exception as e:
                logger.warning(f"Failed to process {batch_label}: {e}")
                with results_lock:
                    failed += 1

        max_workers = min(10, len(entries))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_one, entry) for entry in entries]
            for i, future in enumerate(as_completed(futures)):
                if (i + 1) % 500 == 0:
                    logger.info(f"  {batch_label}: {i + 1}/{len(entries)} processed")

        return {"processed": processed, "updated": updated, "failed": failed}

    def _process_entries_batch(self, entries: List[Dict[str, str]], process_fn, batch_label: str) -> Dict[str, int]:
        """Process a batch of entries using thread pool for parallel downloads.

        Args:
            entries: List of entry dicts with 'url' key
            process_fn: Callable that takes xml_data and returns True if updated
            batch_label: Label for logging

        Returns:
            Dict with processed, updated, failed counts
        """
        processed = 0
        updated = 0
        failed = 0
        results_lock = __import__("threading").Lock()

        def process_one(entry):
            nonlocal processed, updated, failed
            try:
                xml_data = self._download_package(entry["url"])
                if not xml_data:
                    with results_lock:
                        failed += 1
                    return
                result = process_fn(xml_data)
                with results_lock:
                    processed += 1
                    if result:
                        updated += 1
            except Exception as e:
                logger.warning(f"Failed to process {batch_label}: {e}")
                with results_lock:
                    failed += 1

        max_workers = min(10, len(entries))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_one, entry) for entry in entries]
            for i, future in enumerate(as_completed(futures)):
                if (i + 1) % 500 == 0:
                    logger.info(f"  {batch_label}: {i + 1}/{len(entries)} processed")

        return {"processed": processed, "updated": updated, "failed": failed}

    # ----------------------------------------------------------------
    # Bill Status (BILLSTATUS bulk collection - plain XML, no ZIP)
    # ----------------------------------------------------------------

    def ingest_bill_status(
        self,
        congress_numbers: Optional[List[int]] = None,
        bill_types: Optional[List[str]] = None,
        max_workers: int = 8,
    ) -> Dict[str, int]:
        """Ingest bill status XML from GovInfo BILLSTATUS bulk collection.

        Updates existing Bill records with detailed status information
        from the official GovInfo XML. Processes multiple congresses in parallel.

        Args:
            congress_numbers: List of congress numbers to process. Defaults to [118, 119].
            bill_types: Bill types to process. Defaults to all types.
            max_workers: Max parallel download threads.
        """
        congress_numbers = congress_numbers or [118, 119]
        bill_types = bill_types or ["hr", "s", "hres", "sres", "hjres", "sjres", "hconres", "sconres"]

        logger.info(f"Ingesting bill status for congresses {congress_numbers}...")

        # Get all BILLSTATUS sitemaps
        try:
            all_sitemap_urls = self._fetch_sitemap_index("BILLSTATUS")
        except Exception as e:
            logger.error(f"Failed to fetch BILLSTATUS sitemap index: {e}")
            return {"records_processed": 0, "records_inserted": 0, "records_updated": 0, "records_failed": 1}

        # Filter sitemaps for target congresses
        target_sitemaps = []
        for cn in congress_numbers:
            sitemaps = [u for u in all_sitemap_urls if f"/{cn}" in u]
            # Filter by bill type
            if bill_types:
                type_patterns = [f"/{t.lower()}/" for t in bill_types]
                sitemaps = [u for u in sitemaps if any(p in u for p in type_patterns)]
            target_sitemaps.extend(sitemaps)

        logger.info(f"Found {len(target_sitemaps)} BILLSTATUS sitemaps for congresses {congress_numbers}")

        # Collect all entries across all sitemaps
        all_entries = []
        for sitemap_url in target_sitemaps:
            try:
                entries = self._fetch_sitemap(sitemap_url)
                all_entries.extend(entries)
            except Exception as e:
                logger.warning(f"Failed to fetch sitemap {sitemap_url}: {e}")

        logger.info(f"Total bill status files to process: {len(all_entries)}")

        # Phase 1: Parallel download and parse - collect results
        parsed_results: List[Dict] = []
        results_lock = __import__("threading").Lock()
        processed = 0
        updated = 0
        failed = 0
        count_lock = __import__("threading").Lock()

        def process_one(entry):
            nonlocal processed, updated, failed
            try:
                xml_data = self._download_package(entry["url"])
                if not xml_data:
                    with count_lock:
                        failed += 1
                    return

                # Parse without DB session - extract all fields
                result = self._extract_bill_status_data(xml_data)
                if result is None:
                    with count_lock:
                        failed += 1
                    return

                with results_lock:
                    parsed_results.append(result)
                with count_lock:
                    processed += 1
                    if result.get("changed"):
                        updated += 1

            except Exception as e:
                logger.warning(f"Failed to process bill status: {e}")
                with count_lock:
                    failed += 1

        # Run parallel downloads
        workers = min(max_workers, len(all_entries))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(process_one, entry) for entry in all_entries]
            for i, future in enumerate(as_completed(futures)):
                if (i + 1) % 500 == 0:
                    logger.info(f"  Downloaded {i + 1}/{len(all_entries)} bill status files...")

        logger.info(f"Downloads complete: {processed} processed, {updated} changed, {failed} failed")

        # Phase 2: Batch upsert to database
        logger.info(f"Upserting {len(parsed_results)} bill status records to database...")
        upserted = 0
        upsert_failed = 0

        with Session(sync_engine) as session:
            for result in parsed_results:
                try:
                    bill = (
                        session.query(Bill)
                        .filter(
                            Bill.congress_id == result["congress"],
                            Bill.bill_type == result["bill_type"],
                            Bill.number == result["number"],
                        )
                        .first()
                    )
                    if not bill:
                        continue

                    changed = False
                    if result.get("title") and bill.title != result["title"]:
                        bill.title = result["title"]
                        changed = True
                    if result.get("introduced_date") and bill.introduced_date != result["introduced_date"]:
                        bill.introduced_date = result["introduced_date"]
                        changed = True
                    if result.get("origin_chamber") and bill.origin_chamber != result["origin_chamber"]:
                        bill.origin_chamber = result["origin_chamber"]
                        changed = True
                    if result.get("latest_action_date") and bill.latest_action_date != result["latest_action_date"]:
                        bill.latest_action_date = result["latest_action_date"]
                        changed = True
                    if result.get("latest_action") and bill.latest_action != result["latest_action"]:
                        bill.latest_action = result["latest_action"]
                        changed = True
                    if result.get("sponsor_bioguide"):
                        from opendiscourse.models.congress import Member

                        member = session.query(Member).filter(Member.bioguide_id == result["sponsor_bioguide"]).first()
                        if member and bill.sponsor_id != member.id:
                            bill.sponsor_id = member.id
                            changed = True

                    if changed:
                        upserted += 1

                except Exception as e:
                    logger.warning(f"Failed to upsert bill status: {e}")
                    upsert_failed += 1

            session.commit()

        stats = {
            "records_processed": processed,
            "records_inserted": 0,
            "records_updated": upserted,
            "records_failed": failed + upsert_failed,
        }
        self.log_ingestion("bill_status", **stats)
        logger.info(
            f"Bill status ingestion complete: {processed} processed, {upserted} updated, {failed + upsert_failed} failed"
        )
        return stats

    def _extract_bill_status_data(self, xml_data: bytes) -> Optional[Dict]:
        """Extract bill status data from XML without DB operations (thread-safe).

        Returns dict with congress, bill_type, number, title, etc. or None if invalid.
        """
        try:
            root = etree.fromstring(xml_data)
            bill = root.find("bill")
            if bill is None:
                return None

            congress = bill.findtext("congress")
            bill_type = bill.findtext("type")
            bill_number = bill.findtext("number")

            if not all([congress, bill_type, bill_number]):
                return None

            data = {
                "congress": int(congress),
                "bill_type": bill_type.lower(),
                "number": int(bill_number),
                "changed": False,
            }

            title = bill.findtext("title")
            if title:
                data["title"] = clean_text(title)

            introduced = bill.findtext("introducedDate")
            if introduced:
                data["introduced_date"] = parse_date(introduced)

            origin = bill.findtext("originChamber", "").lower()
            if origin:
                data["origin_chamber"] = origin

            latest = bill.find("latestAction")
            if latest is not None:
                action_date = latest.findtext("actionDate")
                if action_date:
                    data["latest_action_date"] = parse_date(action_date)
                action_text = latest.findtext("text")
                if action_text:
                    data["latest_action"] = clean_text(action_text)

            sponsor = bill.find("sponsors/item")
            if sponsor is not None:
                bioguide = sponsor.findtext("bioguideId")
                if bioguide:
                    data["sponsor_bioguide"] = bioguide

            data["changed"] = True
            return data

        except Exception as e:
            logger.warning(f"Failed to extract bill status data: {e}")
            return None

    # ----------------------------------------------------------------
    # Bill Text (BILLS collection - XML format)
    # ----------------------------------------------------------------

    def ingest_bill_text(
        self,
        congress_number: int = 118,
        bill_types: Optional[List[str]] = None,
        max_bills: Optional[int] = None,
    ) -> Dict[str, int]:
        """Ingest bill text XML from GovInfo BILLS collection.

        Downloads bill text ZIP files, extracts XML, and stores
        full text content in BillText records.
        """
        logger.info(f"Ingesting bill text for congress {congress_number}...")
        bill_types = bill_types or ["hr", "s"]

        total_processed = 0
        total_inserted = 0
        total_failed = 0

        with Session(sync_engine) as session:
            for bill_type in bill_types:
                # Build sitemap URL
                sitemap_url = f"{SITEMAP_BASE}/{bill_type.upper()}_sitemap_index.xml"
                try:
                    sitemap_urls = self._fetch_sitemap_index(bill_type.upper())
                except Exception as e:
                    logger.warning(f"Failed to fetch sitemap for {bill_type}: {e}")
                    continue

                # Filter to relevant congress
                all_entries = []
                for surl in sitemap_urls:
                    try:
                        entries = self._fetch_sitemap(surl)
                        # Filter by congress number in URL
                        for e in entries:
                            if f"/{congress_number}/" in e["url"]:
                                all_entries.append(e)
                    except Exception as e:
                        logger.warning(f"Failed to fetch sitemap {surl}: {e}")

                logger.info(f"  {bill_type}: {len(all_entries)} bill text files for congress {congress_number}")

                for i, entry in enumerate(all_entries):
                    if max_bills and i >= max_bills:
                        logger.info(f"  Reached max_bills={max_bills}, stopping")
                        break

                    try:
                        zip_data = self._download_package(entry["url"])
                        if not zip_data:
                            total_failed += 1
                            continue

                        xml_data = self._extract_xml_from_zip(zip_data)
                        if not xml_data:
                            total_failed += 1
                            continue

                        inserted = self._parse_bill_text_xml(session, xml_data, entry["url"])
                        if inserted:
                            total_inserted += 1
                        total_processed += 1

                    except Exception as e:
                        logger.warning(f"Failed to process bill text: {e}")
                        total_failed += 1

                    if total_processed % 50 == 0:
                        session.commit()
                        logger.info(f"  Processed {total_processed} bill text files...")

            session.commit()

        stats = {
            "records_processed": total_processed,
            "records_inserted": total_inserted,
            "records_updated": 0,
            "records_failed": total_failed,
        }
        self.log_ingestion("bill_text", **stats)
        logger.info(f"Bill text ingestion complete: {total_processed} processed, {total_inserted} inserted")
        return stats

    def _parse_bill_text_xml(self, session: Session, xml_data: bytes, source_url: str) -> bool:
        """Parse GovInfo bill text XML and create BillText record."""
        try:
            root = etree.fromstring(xml_data)

            # Parse bill type, number, and version from filename
            # URL format: https://www.govinfo.gov/content/pkg/BILLS-118hr1ih/xml/BILLS-118hr1ih.xml
            filename = source_url.split("/")[-1].replace(".xml", "") if "/" in source_url else ""
            import re

            match = re.match(r"BILLS-(\d+)([a-z]+)(\d+)([a-z]+)", filename, re.IGNORECASE)
            if not match:
                return False

            cong = int(match.group(1))
            btype = match.group(2).lower()
            bnum = int(match.group(3))
            version = match.group(4).lower()

            # Find existing bill
            bill = (
                session.query(Bill)
                .filter(
                    Bill.congress_id == cong,
                    Bill.bill_type == btype,
                    Bill.number == bnum,
                )
                .first()
            )

            if not bill:
                return False

            # Check if we already have this version
            existing = (
                session.query(BillText)
                .filter(
                    BillText.bill_id == bill.id,
                    BillText.version_code == version,
                )
                .first()
            )

            if not bill:
                return False

            # Check if we already have this version
            existing = (
                session.query(BillText)
                .filter(
                    BillText.bill_id == bill.id,
                    BillText.version_code == version,
                )
                .first()
            )
            if existing:
                return False

            # Extract full text - strip XML tags to get plain text
            # GovInfo bill text uses <legis-body> element (not <bill-text>)
            bill_text_elem = root.find(".//legis-body")
            if bill_text_elem is None:
                bill_text_elem = root.find(".//{*}legis-body")
            if bill_text_elem is None:
                bill_text_elem = root.find(".//bill-text")
            if bill_text_elem is None:
                bill_text_elem = root.find(".//{*}bill-text")

            full_text = ""
            if bill_text_elem is not None:
                full_text = etree.tostring(bill_text_elem, encoding="unicode", method="text")
                full_text = full_text.strip()[:500000]

            session.add(
                BillText(
                    bill_id=int(bill.id),
                    version_code=version,
                    version_description=VERSION_DESCRIPTIONS.get(version, version),
                    url=source_url,
                    format="xml",
                    full_text=full_text,
                )
            )
            return True

        except Exception as e:
            logger.warning(f"Failed to parse bill text XML: {e}")
            return False

    # ----------------------------------------------------------------
    # Congressional Record (CREC collection)
    # ----------------------------------------------------------------

    def ingest_congressional_record(
        self,
        date_from: str = "2024-01-01",
        date_to: str = "2024-12-31",
        max_days: Optional[int] = None,
    ) -> Dict[str, int]:
        """Ingest Congressional Record from GovInfo CREC collection."""
        logger.info(f"Ingesting Congressional Record ({date_from} to {date_to})...")

        sitemap_url = f"{SITEMAP_BASE}/CREC_sitemap_index.xml"
        try:
            sitemap_urls = self._fetch_sitemap_index("CREC")
        except Exception as e:
            logger.error(f"Failed to fetch CREC sitemap: {e}")
            return {"records_processed": 0, "records_inserted": 0, "records_updated": 0, "records_failed": 1}

        total_processed = 0
        total_inserted = 0
        total_failed = 0

        with Session(sync_engine) as session:
            for surl in sitemap_urls:
                try:
                    entries = self._fetch_sitemap(surl)
                except Exception as e:
                    logger.warning(f"Failed to fetch sitemap {surl}: {e}")
                    continue

                for entry in entries:
                    # Parse date from URL: CREC-2024-01-09
                    url_path = entry["url"]
                    import re

                    date_match = re.search(r"CREC-(\d{4}-\d{2}-\d{2})", url_path)
                    if not date_match:
                        continue

                    record_date = parse_date(date_match.group(1))
                    if not record_date:
                        continue

                    if record_date < parse_date(date_from) or record_date > parse_date(date_to):
                        continue

                    if max_days and total_processed >= max_days:
                        break

                    try:
                        zip_data = self._download_package(entry["url"])
                        if not zip_data:
                            total_failed += 1
                            continue

                        # Extract text or PDF content
                        xml_data = self._extract_xml_from_zip(zip_data)
                        text_content = ""
                        if xml_data:
                            root = etree.fromstring(xml_data)
                            text_content = etree.tostring(root, encoding="unicode", method="text")[:500000]

                        session.add(
                            CongressionalRecord(
                                congress_gov_id=url_path.split("/")[-1].replace(".zip", ""),
                                date=record_date,
                                url=entry["url"],
                                full_text=text_content[:100000] if text_content else None,
                            )
                        )
                        total_inserted += 1
                        total_processed += 1

                    except Exception as e:
                        logger.warning(f"Failed to process CREC entry: {e}")
                        total_failed += 1

                    if total_processed % 10 == 0:
                        session.commit()

            session.commit()

        stats = {
            "records_processed": total_processed,
            "records_inserted": total_inserted,
            "records_updated": 0,
            "records_failed": total_failed,
        }
        self.log_ingestion("congressional_record", **stats)
        logger.info(f"Congressional Record ingestion complete: {total_processed} processed, {total_inserted} inserted")
        return stats

    # ----------------------------------------------------------------
    # Federal Register (FR collection)
    # ----------------------------------------------------------------

    def ingest_federal_register(
        self,
        date_from: str = "2024-01-01",
        date_to: str = "2024-12-31",
        max_days: Optional[int] = None,
    ) -> Dict[str, int]:
        """Ingest Federal Register from GovInfo FR collection."""
        logger.info(f"Ingesting Federal Register ({date_from} to {date_to})...")

        sitemap_url = f"{SITEMAP_BASE}/FR_sitemap_index.xml"
        try:
            sitemap_urls = self._fetch_sitemap_index("FR")
        except Exception as e:
            logger.error(f"Failed to fetch FR sitemap: {e}")
            return {"records_processed": 0, "records_inserted": 0, "records_updated": 0, "records_failed": 1}

        total_processed = 0
        total_inserted = 0
        total_failed = 0

        with Session(sync_engine) as session:
            for surl in sitemap_urls:
                try:
                    entries = self._fetch_sitemap(surl)
                except Exception as e:
                    logger.warning(f"Failed to fetch sitemap {surl}: {e}")
                    continue

                for entry in entries:
                    url_path = entry["url"]
                    import re

                    date_match = re.search(r"FR-(\d{4}-\d{2}-\d{2})", url_path)
                    if not date_match:
                        continue

                    record_date = parse_date(date_match.group(1))
                    if not record_date:
                        continue

                    if record_date < parse_date(date_from) or record_date > parse_date(date_to):
                        continue

                    if max_days and total_processed >= max_days:
                        break

                    try:
                        zip_data = self._download_package(entry["url"])
                        if not zip_data:
                            total_failed += 1
                            continue

                        xml_data = self._extract_xml_from_zip(zip_data)
                        text_content = ""
                        if xml_data:
                            root = etree.fromstring(xml_data)
                            text_content = etree.tostring(root, encoding="unicode", method="text")[:500000]

                        # Extract document number and type from XML
                        doc_number = None
                        doc_type = None
                        if xml_data:
                            doc_num_elem = root.find(".//FRDOCBP")
                            if doc_num_elem is not None:
                                doc_number = doc_num_elem.get("DOCNO")
                                doc_type = doc_num_elem.get("TYPE")

                        session.add(
                            FederalRegister(
                                document_number=doc_number or url_path.split("/")[-1].replace(".zip", ""),
                                date=record_date,
                                type=doc_type or "unknown",
                                url=entry["url"],
                                full_text=text_content[:100000] if text_content else None,
                            )
                        )
                        total_inserted += 1
                        total_processed += 1

                    except Exception as e:
                        logger.warning(f"Failed to process FR entry: {e}")
                        total_failed += 1

                    if total_processed % 10 == 0:
                        session.commit()

            session.commit()

        stats = {
            "records_processed": total_processed,
            "records_inserted": total_inserted,
            "records_updated": 0,
            "records_failed": total_failed,
        }
        self.log_ingestion("federal_register", **stats)
        logger.info(f"Federal Register ingestion complete: {total_processed} processed, {total_inserted} inserted")
        return stats

    # ----------------------------------------------------------------
    # Master ingest method
    # ----------------------------------------------------------------

    def ingest(
        self,
        congress_number: int = 118,
        bill_types: Optional[List[str]] = None,
        crec_date_from: str = "2024-01-01",
        crec_date_to: str = "2024-12-31",
        fr_date_from: str = "2024-01-01",
        fr_date_to: str = "2024-12-31",
        max_bill_text: Optional[int] = None,
        max_crec_days: Optional[int] = None,
        max_fr_days: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, int]:
        """Run full GovInfo ingestion."""
        logger.info(f"Starting GovInfo ingestion for congress {congress_number}...")
        self._ensure_source_record()

        total_stats = {"records_processed": 0, "records_inserted": 0, "records_updated": 0, "records_failed": 0}

        # 1. Bill status (updates existing bills with detailed info)
        try:
            stats = self.ingest_bill_status(
                congress_number=congress_number,
                bill_types=bill_types,
            )
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        except Exception as e:
            logger.error(f"Failed bill_status: {e}")
            total_stats["records_failed"] += 1

        # 2. Bill text
        try:
            stats = self.ingest_bill_text(
                congress_number=congress_number,
                bill_types=bill_types,
                max_bills=max_bill_text,
            )
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        except Exception as e:
            logger.error(f"Failed bill_text: {e}")
            total_stats["records_failed"] += 1

        # 3. Congressional Record
        try:
            stats = self.ingest_congressional_record(
                date_from=crec_date_from,
                date_to=crec_date_to,
                max_days=max_crec_days,
            )
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        except Exception as e:
            logger.error(f"Failed congressional_record: {e}")
            total_stats["records_failed"] += 1

        # 4. Federal Register
        try:
            stats = self.ingest_federal_register(
                date_from=fr_date_from,
                date_to=fr_date_to,
                max_days=max_fr_days,
            )
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
        except Exception as e:
            logger.error(f"Failed federal_register: {e}")
            total_stats["records_failed"] += 1

        logger.info(f"GovInfo ingestion complete: {total_stats}")
        return total_stats

    def _ensure_source_record(self):
        """Ensure a DataSource record exists for govinfo."""
        with Session(sync_engine) as session:
            existing = session.query(DataSource).filter(DataSource.name == self.source_name).first()
            if not existing:
                session.add(
                    DataSource(
                        name=self.source_name,
                        url=GOVINFO_BASE,
                        api_type="bulk",
                        auth_type="api_key",
                        status="active",
                    )
                )
                session.commit()
