"""
Alembic migration for Phase 7: Email Notifications

Adds email notification preferences to users table and creates email_logs table.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0007_phase7_email_notifications'
down_revision = '0006_phase5_user_enhancements'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add email notification columns to users table and create email_logs table."""

    # Add email notification preference columns to users table
    op.add_column(
        'users',
        sa.Column('notify_on_new_jobs', sa.Boolean(), server_default='true', nullable=False)
    )
    op.add_column(
        'users',
        sa.Column('notify_on_resume_upload', sa.Boolean(), server_default='true', nullable=False)
    )
    op.add_column(
        'users',
        sa.Column('notify_on_password_change', sa.Boolean(), server_default='true', nullable=False)
    )
    op.add_column(
        'users',
        sa.Column('weekly_digest', sa.Boolean(), server_default='true', nullable=False)
    )
    op.add_column(
        'users',
        sa.Column('email_frequency', sa.String(50), server_default='weekly', nullable=False)
    )

    # Create email_logs table
    op.create_table(
        'email_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email_type', sa.String(50), nullable=False),
        sa.Column('recipient_email', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retries', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indices on email_logs table
    op.create_index('ix_email_logs_user_id', 'email_logs', ['user_id'])
    op.create_index('ix_email_logs_status', 'email_logs', ['status'])
    op.create_index('ix_email_logs_created_at', 'email_logs', ['created_at'])


def downgrade() -> None:
    """Reverse the migration."""

    # Drop indices
    op.drop_index('ix_email_logs_created_at', table_name='email_logs')
    op.drop_index('ix_email_logs_status', table_name='email_logs')
    op.drop_index('ix_email_logs_user_id', table_name='email_logs')

    # Drop email_logs table
    op.drop_table('email_logs')

    # Remove email notification columns from users table
    op.drop_column('users', 'email_frequency')
    op.drop_column('users', 'weekly_digest')
    op.drop_column('users', 'notify_on_password_change')
    op.drop_column('users', 'notify_on_resume_upload')
    op.drop_column('users', 'notify_on_new_jobs')
