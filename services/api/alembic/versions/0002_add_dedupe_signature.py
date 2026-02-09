"""add dedupe_signature to jobs

Revision ID: 0002_add_dedupe_signature
Revises: 0001_create_tables
Create Date: 2026-02-09 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_dedupe_signature'
down_revision = '0001_create_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('jobs', sa.Column('dedupe_signature', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_jobs_dedupe_signature'), 'jobs', ['dedupe_signature'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_jobs_dedupe_signature'), table_name='jobs')
    op.drop_column('jobs', 'dedupe_signature')
