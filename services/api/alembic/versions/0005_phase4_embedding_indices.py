"""Ensure embeddings table exists with proper indices - PHASE 4."""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Create embeddings table with indices if it doesn't exist."""
    # This migration ensures the Embedding table from models.py is properly indexed
    # The table was already defined in models.py, so we just need to ensure indices

    # Create composite index on (parent_type, parent_id) for faster lookups
    op.create_index(
        'idx_embeddings_parent',
        'embeddings',
        ['parent_type', 'parent_id'],
        unique=False,
        if_not_exists=True
    )

    # Create index on model_name for filtering by embedding model version
    op.create_index(
        'idx_embeddings_model',
        'embeddings',
        ['model_name'],
        unique=False,
        if_not_exists=True
    )

    # Create index on parent_type for fast filtering (jobs vs resumes)
    op.create_index(
        'idx_embeddings_type',
        'embeddings',
        ['parent_type'],
        unique=False,
        if_not_exists=True
    )


def downgrade():
    """Remove embedding indices if needed."""
    op.drop_index('idx_embeddings_parent', 'embeddings', if_exists=True)
    op.drop_index('idx_embeddings_model', 'embeddings', if_exists=True)
    op.drop_index('idx_embeddings_type', 'embeddings', if_exists=True)
