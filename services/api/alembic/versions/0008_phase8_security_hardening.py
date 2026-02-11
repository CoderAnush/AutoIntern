"""
Alembic migration for Phase 8: Security Hardening

Adds account lockout tracking to users table and creates request_logs table for audit trail.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0008_phase8_security_hardening'
down_revision = '0007_phase7_email_notifications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add account lockout columns to users table and create request_logs table."""

    # Add account lockout tracking columns to users table
    op.add_column(
        'users',
        sa.Column(
            'failed_login_attempts',
            sa.Integer(),
            server_default='0',
            nullable=False
        )
    )
    op.add_column(
        'users',
        sa.Column(
            'locked_until',
            sa.DateTime(timezone=True),
            nullable=True
        )
    )
    op.add_column(
        'users',
        sa.Column(
            'last_login_attempt',
            sa.DateTime(timezone=True),
            nullable=True
        )
    )

    # Create request_logs table for audit trail
    op.create_table(
        'request_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('path', sa.String(512), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('request_body_hash', sa.String(64), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indices on request_logs table for fast queries
    op.create_index('ix_request_logs_user_id', 'request_logs', ['user_id'])
    op.create_index('ix_request_logs_status_code', 'request_logs', ['status_code'])
    op.create_index('ix_request_logs_created_at', 'request_logs', ['created_at'])
    op.create_index('ix_request_logs_path_status', 'request_logs', ['path', 'status_code'])


def downgrade() -> None:
    """Reverse the migration."""

    # Drop indices on request_logs table
    op.drop_index('ix_request_logs_path_status', table_name='request_logs')
    op.drop_index('ix_request_logs_created_at', table_name='request_logs')
    op.drop_index('ix_request_logs_status_code', table_name='request_logs')
    op.drop_index('ix_request_logs_user_id', table_name='request_logs')

    # Drop request_logs table
    op.drop_table('request_logs')

    # Remove account lockout columns from users table
    op.drop_column('users', 'last_login_attempt')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
