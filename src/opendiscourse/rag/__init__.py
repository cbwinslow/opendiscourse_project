"""
RAG (Retrieval-Augmented Generation) module for OpenDiscourse.

Provides semantic search and natural language querying over government documents
using LlamaIndex with PostgreSQL vector storage.
"""

from opendiscourse.rag.index import DocumentIndexer
from opendiscourse.rag.query import DocumentQueryEngine

__all__ = [
    "DocumentIndexer",
    "DocumentQueryEngine",
]
