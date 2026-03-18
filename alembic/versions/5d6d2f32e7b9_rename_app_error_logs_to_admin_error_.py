"""rename app_error_logs to admin_error_logs

Revision ID: 5d6d2f32e7b9
Revises: f7497b85e984
Create Date: 2026-03-18 16:28:34.802616

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5d6d2f32e7b9'
down_revision: Union[str, Sequence[str], None] = 'f7497b85e984'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 重命名表
    op.rename_table('app_error_logs', 'admin_error_logs')

    # 重命名索引
    op.execute('ALTER INDEX ix_app_error_logs_id RENAME TO ix_admin_error_logs_id')
    op.execute('ALTER INDEX ix_app_error_logs_is_deleted RENAME TO ix_admin_error_logs_is_deleted')
    op.execute('ALTER INDEX ix_app_error_logs_level RENAME TO ix_admin_error_logs_level')
    op.execute('ALTER INDEX ix_app_error_logs_request_path RENAME TO ix_admin_error_logs_request_path')
    op.execute('ALTER INDEX ix_app_error_logs_user_id RENAME TO ix_admin_error_logs_user_id')


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table('admin_error_logs', 'app_error_logs')

    op.execute('ALTER INDEX ix_admin_error_logs_id RENAME TO ix_app_error_logs_id')
    op.execute('ALTER INDEX ix_admin_error_logs_is_deleted RENAME TO ix_app_error_logs_is_deleted')
    op.execute('ALTER INDEX ix_admin_error_logs_level RENAME TO ix_app_error_logs_level')
    op.execute('ALTER INDEX ix_admin_error_logs_request_path RENAME TO ix_app_error_logs_request_path')
    op.execute('ALTER INDEX ix_admin_error_logs_user_id RENAME TO ix_app_error_logs_user_id')
