"""Phase 5: User enhancements - add is_active and updated_at

Revision ID: 0006_phase5_user_enhancements
Revises: 0005_phase4_embedding_indices
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = '0006_phase5_user_enhancements'
down_revision = '0005_phase4_embedding_indices'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active column to users table
    op.add_column('users', sa.Column(
        'is_active',
        sa.Boolean(),
        server_default=sa.true(),
        nullable=False
    ))

    # Add updated_at column to users table
    op.add_column('users', sa.Column(
        'updated_at',
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=True
    ))

    # Add index on email for faster lookups
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Add index on is_active for filtering active users
    op.create_index('ix_users_is_active', 'users', ['is_active'])


def downgrade() -> None:
    # Drop indices
    op.drop_index('ix_users_is_active', table_name='users')
    op.drop_index('ix_users_email', table_name='users')

    # Remove columns
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'is_active')
