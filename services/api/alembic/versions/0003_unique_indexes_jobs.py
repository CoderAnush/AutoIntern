"""add unique indexes on jobs (dedupe_signature, external_id)

Revision ID: 0003_unique_indexes_jobs
Revises: 0002_add_dedupe_signature
Create Date: 2026-02-09 00:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_unique_indexes_jobs'
down_revision = '0002_add_dedupe_signature'
branch_labels = None
depends_on = None


def upgrade():
    # Create unique index on dedupe_signature when not null
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_jobs_dedupe_signature ON jobs (dedupe_signature) WHERE dedupe_signature IS NOT NULL")
    # Create unique index on external_id when not null
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_jobs_external_id ON jobs (external_id) WHERE external_id IS NOT NULL")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ux_jobs_dedupe_signature")
    op.execute("DROP INDEX IF EXISTS ux_jobs_external_id")
