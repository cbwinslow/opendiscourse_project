"""enable pgvector extension for RAG

Revision ID: f2c3a4b5d6e7
Revises: ecc1fda708e0
Create Date: 2026-04-03 07:57:12.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f2c3a4b5d6e7"
down_revision: Union[str, None] = "ecc1fda708e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension for vector embeddings
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # Remove pgvector extension
    op.execute("DROP EXTENSION IF EXISTS vector")
