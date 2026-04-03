"""
Natural language query interface using LlamaIndex for OpenDiscourse.

Provides semantic search capabilities over indexed government documents
with support for filtering by document type, date ranges, and metadata.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date

from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

from opendiscourse.rag.index import DocumentIndexer


class DocumentQueryEngine:
    """Natural language query interface for government documents."""

    def __init__(self, indexer: DocumentIndexer):
        self.indexer = indexer
        self.query_engine = None

    async def initialize(self):
        """Initialize the query engine."""
        if self.indexer.index is None:
            await self.indexer.initialize()

        # Create query engine with postprocessing
        retriever = self.indexer.index.as_retriever(similarity_top_k=10)

        self.query_engine = RetrieverQueryEngine(
            retriever=retriever, node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.7)]
        )

    async def search_bills(
        self, query: str, congress: Optional[int] = None, bill_type: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search bill texts using natural language.

        Args:
            query: Natural language search query
            congress: Filter by congress number
            bill_type: Filter by bill type (HR, S, HJRES, etc.)
            limit: Maximum results to return

        Returns:
            List of matching bill documents with metadata
        """
        filters = [MetadataFilter(key="doc_type", value="bill_text")]

        if congress:
            filters.append(MetadataFilter(key="congress", value=congress))
        if bill_type:
            filters.append(MetadataFilter(key="bill_type", value=bill_type))

        metadata_filters = MetadataFilters(filters=filters)

        response = await self.query_engine.aquery(query, filters=metadata_filters)

        results = []
        for node in response.source_nodes[:limit]:
            results.append(
                {
                    "bill_id": node.metadata.get("bill_id"),
                    "congress": node.metadata.get("congress"),
                    "bill_type": node.metadata.get("bill_type"),
                    "bill_number": node.metadata.get("bill_number"),
                    "title": node.metadata.get("title"),
                    "text_snippet": node.text[:500] + "..." if len(node.text) > 500 else node.text,
                    "similarity_score": node.score,
                    "indexed_at": node.metadata.get("indexed_at"),
                }
            )

        return results

    async def search_congressional_records(
        self,
        query: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        volume: Optional[int] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search congressional records using natural language.

        Args:
            query: Natural language search query
            start_date: Filter records from this date onward
            end_date: Filter records up to this date
            volume: Filter by volume number
            limit: Maximum results to return

        Returns:
            List of matching congressional record documents
        """
        filters = [MetadataFilter(key="doc_type", value="congressional_record")]

        if volume:
            filters.append(MetadataFilter(key="volume", value=volume))

        metadata_filters = MetadataFilters(filters=filters)

        response = await self.query_engine.aquery(query, filters=metadata_filters)

        # Apply date filtering post-query since metadata filters don't support date ranges well
        results = []
        for node in response.source_nodes:
            record_date_str = node.metadata.get("date")
            if record_date_str:
                record_date = datetime.fromisoformat(record_date_str).date()

                if start_date and record_date < start_date:
                    continue
                if end_date and record_date > end_date:
                    continue

            if len(results) >= limit:
                break

            results.append(
                {
                    "record_id": node.metadata.get("record_id"),
                    "date": node.metadata.get("date"),
                    "volume": node.metadata.get("volume"),
                    "issue": node.metadata.get("issue"),
                    "start_page": node.metadata.get("start_page"),
                    "end_page": node.metadata.get("end_page"),
                    "text_snippet": node.text[:500] + "..." if len(node.text) > 500 else node.text,
                    "similarity_score": node.score,
                    "indexed_at": node.metadata.get("indexed_at"),
                }
            )

        return results

    async def search_all_documents(
        self, query: str, doc_types: Optional[List[str]] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search across all document types.

        Args:
            query: Natural language search query
            doc_types: List of document types to search ("bill_text", "congressional_record")
            limit: Maximum results to return

        Returns:
            List of matching documents with metadata
        """
        if doc_types:
            filters = [MetadataFilter(key="doc_type", operator="in", value=doc_types)]
            metadata_filters = MetadataFilters(filters=filters)
        else:
            metadata_filters = None

        response = await self.query_engine.aquery(query, filters=metadata_filters)

        results = []
        for node in response.source_nodes[:limit]:
            result = {
                "doc_type": node.metadata.get("doc_type"),
                "text_snippet": node.text[:500] + "..." if len(node.text) > 500 else node.text,
                "similarity_score": node.score,
                "indexed_at": node.metadata.get("indexed_at"),
            }

            # Add type-specific metadata
            if node.metadata.get("doc_type") == "bill_text":
                result.update(
                    {
                        "bill_id": node.metadata.get("bill_id"),
                        "congress": node.metadata.get("congress"),
                        "bill_type": node.metadata.get("bill_type"),
                        "bill_number": node.metadata.get("bill_number"),
                        "title": node.metadata.get("title"),
                    }
                )
            elif node.metadata.get("doc_type") == "congressional_record":
                result.update(
                    {
                        "record_id": node.metadata.get("record_id"),
                        "date": node.metadata.get("date"),
                        "volume": node.metadata.get("volume"),
                        "issue": node.metadata.get("issue"),
                        "start_page": node.metadata.get("start_page"),
                        "end_page": node.metadata.get("end_page"),
                    }
                )

            results.append(result)

        return results
