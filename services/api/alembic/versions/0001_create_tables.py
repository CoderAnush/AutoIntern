"""initial create tables

Revision ID: 0001_create_tables
Revises: 
Create Date: 2026-02-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Use models' metadata to create all tables (sa is available if needed)
    bind = op.get_bind()
    from app.models.models import Base
    Base.metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    from app.models.models import Base
    Base.metadata.drop_all(bind=bind)
