"""add_composite_indexes_for_performance

Revision ID: 17a3491fc814
Revises: 7338f5c14070
Create Date: 2025-11-14 23:19:33.578345

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17a3491fc814'
down_revision: Union[str, None] = '7338f5c14070'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite indexes for performance optimization."""
    
    # Designs: user + status + created (common query pattern)
    # Partial index excludes soft-deleted records
    op.create_index(
        'ix_designs_user_status_created',
        'designs',
        ['user_id', 'status', 'created_at'],
        postgresql_where=sa.text('is_deleted = false')
    )
    
    # Orders: user + status + created (for order history queries)
    op.create_index(
        'ix_orders_user_status_created',
        'orders',
        ['user_id', 'status', 'created_at']
    )
    
    # Subscriptions: status + period_end (for billing jobs and expiry checks)
    op.create_index(
        'ix_subscriptions_status_period',
        'subscriptions',
        ['status', 'current_period_end']
    )
    
    # Designs: product_type + status (for analytics and filtering)
    op.create_index(
        'ix_designs_product_status',
        'designs',
        ['product_type', 'status'],
        postgresql_where=sa.text('is_deleted = false')
    )


def downgrade() -> None:
    """Remove composite indexes."""
    op.drop_index('ix_designs_user_status_created', table_name='designs')
    op.drop_index('ix_orders_user_status_created', table_name='orders')
    op.drop_index('ix_subscriptions_status_period', table_name='subscriptions')
    op.drop_index('ix_designs_product_status', table_name='designs')