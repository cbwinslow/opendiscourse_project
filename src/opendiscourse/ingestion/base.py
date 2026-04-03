"""Base ingestion class for all data source pipelines."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional

import httpx
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from opendiscourse.config import get_settings
from opendiscourse.database import sync_engine
from opendiscourse.models.metadata import DataSource, IngestionLog

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseIngestion(ABC):
    """Base class for all data ingestion pipelines."""

    source_name: str = ""
    base_url: str = ""
    api_key: str = ""

    def __init__(self, batch_size: Optional[int] = None):
        self.batch_size = batch_size or settings.ingestion_batch_size
        self.session: Optional[Session] = None
        self._client: Optional[httpx.Client] = None
        self._source_record: Optional[DataSource] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    def get_source_record(self, db_session: Session) -> Optional[DataSource]:
        if self._source_record is None and self.source_name:
            self._source_record = db_session.query(DataSource).filter(DataSource.name == self.source_name).first()
        return self._source_record

    def log_ingestion(
        self,
        table_name: str,
        records_processed: int,
        records_inserted: int,
        records_updated: int,
        records_failed: int,
        status: str = "completed",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log ingestion results to the database."""
        with Session(sync_engine) as session:
            source_id = None
            if self.source_name:
                source = session.query(DataSource).filter(DataSource.name == self.source_name).first()
                if source:
                    source_id = source.id

            log = IngestionLog(
                source_id=source_id,
                table_name=table_name,
                records_processed=records_processed,
                records_inserted=records_inserted,
                records_updated=records_updated,
                records_failed=records_failed,
                status=status,
                error_message=error_message,
                extra_metadata=metadata,
            )
            session.add(log)
            session.commit()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def fetch_page(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Fetch a single page of results with retry logic."""
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def paginate(
        self,
        url: str,
        params: Optional[Dict] = None,
        offset_key: str = "offset",
        limit_key: str = "limit",
        limit: int = 100,
        results_key: Optional[str] = None,
        count_key: Optional[str] = None,
        max_pages: Optional[int] = None,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """Paginate through API results with rate limiting.

        The offset parameter is incremented by `limit` after each page is fetched
        and yielded. This ensures every request includes the correct offset value.

        Args:
            url: API endpoint path (relative to base_url).
            params: Additional query params. offset/limit are added/overridden.
            offset_key: Query param name for offset (default "offset").
            limit_key: Query param name for limit (default "limit").
            limit: Number of records per page.
            results_key: Key in response JSON containing the result list.
                If None, tries data["results"], then data["data"], then
                treats the top-level response as a list.
            count_key: Key in response JSON containing total record count.
                If provided, pagination stops when offset + limit >= total.
            max_pages: Hard cap on number of pages to fetch (safety valve).
        """
        params = dict(params) if params else {}
        params[limit_key] = limit

        if offset_key not in params:
            params[offset_key] = 0

        page = 0
        while True:
            logger.debug(f"Fetching page {page}: {url} offset={params[offset_key]} limit={limit}")
            data = self.fetch_page(url, params=params)

            if results_key:
                results = data.get(results_key, [])
            elif isinstance(data, list):
                results = data
            else:
                results = data.get("results", data.get("data", []))

            if not results:
                logger.info(f"No more results at offset={params[offset_key]}, stopping pagination.")
                break

            yield results
            page += 1

            if max_pages and page >= max_pages:
                logger.info(f"Reached max_pages={max_pages}, stopping pagination.")
                break

            if count_key:
                total_count = data.get(count_key, 0)
                if total_count and params[offset_key] + limit >= total_count:
                    logger.info(f"Reached total_count={total_count}, stopping pagination.")
                    break

            if len(results) < limit:
                logger.info(f"Received {len(results)} results < limit={limit}, stopping pagination.")
                break

            params[offset_key] += limit
            logger.debug(f"Advancing offset to {params[offset_key]} for next page.")

            if settings.ingestion_rate_limit_delay > 0:
                time.sleep(settings.ingestion_rate_limit_delay)

    def upsert_batch(self, session: Session, model, records: List[Dict], unique_columns: List[str]):
        """Upsert a batch of records using PostgreSQL ON CONFLICT."""
        if not records:
            return 0, 0

        from sqlalchemy.dialects.postgresql import insert

        inserted = 0
        updated = 0

        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]
            stmt = insert(model).values(batch)

            exclude_cols = [
                c.name
                for c in model.__table__.columns
                if c.name not in unique_columns and c.name not in ("id", "created_at")
            ]

            stmt = stmt.on_conflict_do_update(
                index_elements=unique_columns,
                set_={col: getattr(stmt.excluded, col) for col in exclude_cols},
            )

            session.execute(stmt)
            inserted += len(batch)

        return inserted, updated

    def close(self):
        """Clean up resources."""
        if self._client:
            self._client.close()
            self._client = None

    @abstractmethod
    def ingest(self, **kwargs) -> Dict[str, int]:
        """Run the ingestion pipeline. Returns stats dict."""
        ...
