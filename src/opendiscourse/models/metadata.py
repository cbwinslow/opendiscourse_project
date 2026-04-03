from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from opendiscourse.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    url = Column(Text)
    description = Column(Text)
    api_type = Column(String(50))
    auth_type = Column(String(50))
    rate_limit = Column(Integer)
    last_sync = Column(DateTime)
    status = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())


class IngestionLog(Base):
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"))
    table_name = Column(String(100))
    records_processed = Column(Integer)
    records_inserted = Column(Integer)
    records_updated = Column(Integer)
    records_failed = Column(Integer)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    status = Column(String(50))
    error_message = Column(Text)
    extra_metadata = Column("metadata", JSONB)


class APIRateLimit(Base):
    __tablename__ = "api_rate_limits"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"))
    endpoint = Column(String(200))
    requests_made = Column(Integer, default=0)
    limit_total = Column(Integer)
    limit_reset = Column(DateTime)
    last_request = Column(DateTime, server_default=func.now())


class DataQualityCheck(Base):
    __tablename__ = "data_quality_checks"

    id = Column(Integer, primary_key=True)
    table_name = Column(String(100))
    check_name = Column(String(100))
    check_type = Column(String(50))
    records_checked = Column(Integer)
    records_failed = Column(Integer)
    passed = Column(Boolean)
    details = Column(JSONB)
    checked_at = Column(DateTime, server_default=func.now())
