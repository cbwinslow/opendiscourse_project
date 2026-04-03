"""Download state tracking and management for resumable downloads."""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, func
from sqlalchemy.orm import Session

from opendiscourse.database import Base

logger = logging.getLogger(__name__)


class DownloadStatus(Enum):
    """Status of a download operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    """Represents a single download task."""

    url: str
    filename: str
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    status: DownloadStatus = DownloadStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    completed_at: Optional[datetime] = None
    retries: int = 0
    max_retries: int = 3
    priority: int = 1  # 1=low, 5=high

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "DownloadTask":
        """Create from dictionary."""
        data["status"] = DownloadStatus(data["status"])
        return cls(**data)


class DownloadState(Base):
    """Database table for tracking download states."""

    __tablename__ = "download_states"

    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False, index=True)  # govinfo, fec, etc.
    collection = Column(String(50), nullable=False, index=True)  # bills, crec, fr, etc.
    url = Column(Text, nullable=False, unique=True)
    filename = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False, default=DownloadStatus.PENDING.value)
    size_bytes = Column(Integer)
    checksum = Column(String(128))
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    priority = Column(Integer, default=1)


class DownloadStateManager:
    """Manages download state persistence and resumption."""

    def __init__(self, session: Session):
        self.session = session

    def create_task(self, source: str, collection: str, url: str, filename: str, priority: int = 1) -> DownloadState:
        """Create a new download task."""
        task = DownloadState(
            source=source,
            collection=collection,
            url=url,
            filename=filename,
            status=DownloadStatus.PENDING.value,
            priority=priority,
        )
        self.session.add(task)
        self.session.commit()
        return task

    def update_task_status(
        self,
        task_id: int,
        status: DownloadStatus,
        error_message: Optional[str] = None,
        size_bytes: Optional[int] = None,
        checksum: Optional[str] = None,
    ) -> None:
        """Update task status."""
        task = self.session.query(DownloadState).filter_by(id=task_id).first()
        if task:
            task.status = status.value
            task.updated_at = datetime.utcnow()

            if error_message:
                task.error_message = error_message

            if size_bytes:
                task.size_bytes = size_bytes

            if checksum:
                task.checksum = checksum

            if status == DownloadStatus.COMPLETED:
                task.completed_at = datetime.utcnow()

            self.session.commit()

    def get_pending_tasks(
        self, source: Optional[str] = None, collection: Optional[str] = None, limit: int = 100
    ) -> List[DownloadState]:
        """Get pending tasks, ordered by priority and creation time."""
        query = self.session.query(DownloadState).filter_by(status=DownloadStatus.PENDING.value)

        if source:
            query = query.filter_by(source=source)

        if collection:
            query = query.filter_by(collection=collection)

        return query.order_by(DownloadState.priority.desc(), DownloadState.created_at.asc()).limit(limit).all()

    def get_failed_tasks(self, max_retries: int = 3) -> List[DownloadState]:
        """Get failed tasks that can be retried."""
        return (
            self.session.query(DownloadState)
            .filter(
                DownloadState.status == DownloadStatus.FAILED.value, DownloadState.retries < DownloadState.max_retries
            )
            .all()
        )

    def increment_retry_count(self, task_id: int) -> bool:
        """Increment retry count for a task."""
        task = self.session.query(DownloadState).filter_by(id=task_id).first()
        if task:
            task.retries += 1
            if task.retries >= task.max_retries:
                task.status = DownloadStatus.FAILED.value
            self.session.commit()
            return True
        return False

    def get_download_stats(self, source: Optional[str] = None) -> Dict[str, int]:
        """Get download statistics."""
        from sqlalchemy import func

        query = self.session.query(DownloadState.status, func.count(DownloadState.id)).group_by(DownloadState.status)

        if source:
            query = query.filter_by(source=source)

        stats = {row[0]: row[1] for row in query.all()}

        # Ensure all status types are present
        for status in DownloadStatus:
            stats.setdefault(status.value, 0)

        return stats

    def cleanup_completed_tasks(self, days_old: int = 30) -> int:
        """Clean up old completed tasks."""
        from sqlalchemy import text

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = self.session.execute(
            text("""
            DELETE FROM download_states
            WHERE status = :completed_status
            AND completed_at < :cutoff_date
        """),
            {"completed_status": DownloadStatus.COMPLETED.value, "cutoff_date": cutoff_date},
        )

        deleted_count = result.rowcount
        self.session.commit()

        logger.info(f"Cleaned up {deleted_count} old completed download tasks")
        return deleted_count

    def mark_duplicate_urls(self) -> int:
        """Mark duplicate URLs as cancelled."""
        from sqlalchemy import text

        # Find URLs that appear more than once
        duplicates = self.session.execute(
            text("""
            SELECT url, COUNT(*) as count
            FROM download_states
            WHERE status IN (:pending, :in_progress)
            GROUP BY url
            HAVING COUNT(*) > 1
        """),
            {"pending": DownloadStatus.PENDING.value, "in_progress": DownloadStatus.IN_PROGRESS.value},
        )

        updated = 0
        for row in duplicates:
            url = row[0]

            # Keep the highest priority task, cancel others
            tasks = (
                self.session.query(DownloadState)
                .filter_by(url=url)
                .order_by(DownloadState.priority.desc(), DownloadState.created_at.asc())
                .all()
            )

            for task in tasks[1:]:  # Skip the first (highest priority)
                task.status = DownloadStatus.CANCELLED.value
                task.error_message = "Duplicate URL - cancelled in favor of higher priority task"
                updated += 1

        self.session.commit()
        logger.info(f"Marked {updated} duplicate download tasks as cancelled")
        return updated
