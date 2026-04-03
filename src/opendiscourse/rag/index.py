"""
Document indexing module using LlamaIndex for OpenDiscourse.

Provides semantic indexing of government documents (bills, congressional records)
using PostgreSQL vector storage for fast retrieval.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from llama_index.core import Document, VectorStoreIndex
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core.storage import StorageContext
from sqlalchemy.ext.asyncio import AsyncSession

from opendiscourse.config import settings
from opendiscourse.database import get_async_session
from opendiscourse.models.congress import BillText, CongressionalRecord


class DocumentIndexer:
    """Indexes government documents for semantic search using LlamaIndex."""

    def __init__(self):
        self.vector_store = None
        self.storage_context = None
        self.index = None

    async def initialize(self):
        """Initialize the vector store and storage context."""
        # Create PostgreSQL vector store connection
        self.vector_store = PGVectorStore.from_params(
            host=settings.database_host,
            port=settings.database_port,
            database=settings.database_name,
            user=settings.database_user,
            password=settings.database_password,
            table_name="document_embeddings",
            embed_dim=1536,  # OpenAI text-embedding-ada-002 dimension
        )

        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

        # Load existing index or create new one
        try:
            self.index = VectorStoreIndex.from_vector_store(self.vector_store, storage_context=self.storage_context)
        except Exception:
            # Create new index if none exists
            self.index = VectorStoreIndex([], storage_context=self.storage_context)

    async def index_bill_texts(self, bill_ids: Optional[List[str]] = None) -> int:
        """
        Index bill text documents for semantic search.

        Args:
            bill_ids: Specific bill IDs to index, or None for all bills

        Returns:
            Number of documents indexed
        """
        async with get_async_session() as session:
            query = session.query(BillText)
            if bill_ids:
                query = query.filter(BillText.bill_id.in_(bill_ids))

            bills = await session.execute(query)
            bills = bills.scalars().all()

        documents = []
        for bill in bills:
            # Create document with metadata
            doc = Document(
                text=bill.full_text,
                metadata={
                    "doc_type": "bill_text",
                    "bill_id": bill.bill_id,
                    "congress": bill.congress,
                    "bill_type": bill.bill_type,
                    "bill_number": bill.bill_number,
                    "title": bill.title,
                    "indexed_at": datetime.utcnow().isoformat(),
                },
                id_=f"bill_{bill.bill_id}",
            )
            documents.append(doc)

        if documents:
            await self.index.aadd_documents(documents)

        return len(documents)

    async def index_congressional_records(self, record_ids: Optional[List[str]] = None) -> int:
        """
        Index congressional record documents.

        Args:
            record_ids: Specific record IDs to index, or None for all

        Returns:
            Number of documents indexed
        """
        async with get_async_session() as session:
            query = session.query(CongressionalRecord)
            if record_ids:
                query = query.filter(CongressionalRecord.id.in_(record_ids))

            records = await session.execute(query)
            records = records.scalars().all()

        documents = []
        for record in records:
            # Create document with metadata
            doc = Document(
                text=record.full_text,
                metadata={
                    "doc_type": "congressional_record",
                    "record_id": record.id,
                    "date": record.date.isoformat(),
                    "volume": record.volume,
                    "issue": record.issue,
                    "start_page": record.start_page,
                    "end_page": record.end_page,
                    "indexed_at": datetime.utcnow().isoformat(),
                },
                id_=f"record_{record.id}",
            )
            documents.append(doc)

        if documents:
            await self.index.aadd_documents(documents)

        return len(documents)

    async def reindex_all(self) -> Dict[str, int]:
        """
        Reindex all documents from scratch.

        Returns:
            Dictionary with counts of indexed documents by type
        """
        # Clear existing index
        await self.vector_store.aclear()

        # Reinitialize
        await self.initialize()

        # Index all bill texts
        bill_count = await self.index_bill_texts()

        # Index all congressional records
        record_count = await self.index_congressional_records()

        return {"bill_texts": bill_count, "congressional_records": record_count, "total": bill_count + record_count}
