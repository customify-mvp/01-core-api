"""Initial schema - users, subscriptions, designs, orders, shopify_stores

Revision ID: 001
Revises: 
Create Date: 2025-12-08 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema."""
    
    # ============================================================
    # TABLE: users
    # ============================================================
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        comment='Application users (merchants)'
    )
    
    # Users indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    op.create_index(
        'ix_users_active_not_deleted',
        'users',
        ['is_active'],
        postgresql_where=sa.text('is_deleted = false')
    )
    
    # Users check constraints
    op.create_check_constraint(
        'ck_users_email_format',
        'users',
        sa.text("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'")
    )
    
    # ============================================================
    # TABLE: subscriptions
    # ============================================================
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column(
            'user_id',
            sa.String(36),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            unique=True
        ),
        sa.Column(
            'plan',
            sa.String(50),
            nullable=False,
            server_default='free'
        ),
        sa.Column(
            'status',
            sa.String(50),
            nullable=False,
            server_default='active'
        ),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('designs_this_month', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_subscriptions_user_id'),
        comment='User subscription plans and usage'
    )
    
    # Subscriptions indexes
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'], unique=True)
    op.create_index('ix_subscriptions_stripe_customer_id', 'subscriptions', ['stripe_customer_id'])
    op.create_index('ix_subscriptions_stripe_subscription_id', 'subscriptions', ['stripe_subscription_id'])
    
    # Subscriptions check constraints
    op.create_check_constraint(
        'ck_subscriptions_plan',
        'subscriptions',
        sa.text("plan IN ('free', 'starter', 'professional', 'enterprise')")
    )
    op.create_check_constraint(
        'ck_subscriptions_status',
        'subscriptions',
        sa.text("status IN ('active', 'canceled', 'past_due', 'trialing')")
    )
    op.create_check_constraint(
        'ck_subscriptions_designs_positive',
        'subscriptions',
        sa.text("designs_this_month >= 0")
    )
    
    # ============================================================
    # TABLE: designs
    # ============================================================
    op.create_table(
        'designs',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column(
            'user_id',
            sa.String(36),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('product_type', sa.String(50), nullable=False),
        sa.Column('design_data', JSONB, nullable=False),
        sa.Column(
            'status',
            sa.String(50),
            nullable=False,
            server_default='draft'
        ),
        sa.Column('preview_url', sa.String(500), nullable=True),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),
        sa.PrimaryKeyConstraint('id'),
        comment='User-created designs for products'
    )
    
    # Designs indexes
    op.create_index('ix_designs_user_id', 'designs', ['user_id'])
    op.create_index('ix_designs_created_at', 'designs', ['created_at'])
    op.create_index(
        'ix_designs_user_created',
        'designs',
        ['user_id', 'created_at'],
        postgresql_where=sa.text('is_deleted = false')
    )
    op.create_index(
        'ix_designs_user_status',
        'designs',
        ['user_id', 'status'],
        postgresql_where=sa.text('is_deleted = false')
    )
    # GIN index for JSONB queries
    op.create_index(
        'ix_designs_data_gin',
        'designs',
        ['design_data'],
        postgresql_using='gin'
    )
    
    # Designs check constraints
    op.create_check_constraint(
        'ck_designs_product_type',
        'designs',
        sa.text("product_type IN ('t-shirt', 'mug', 'poster', 'hoodie', 'tote-bag')")
    )
    op.create_check_constraint(
        'ck_designs_status',
        'designs',
        sa.text("status IN ('draft', 'rendering', 'published', 'failed')")
    )
    
    # ============================================================
    # TABLE: orders
    # ============================================================
    op.create_table(
        'orders',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column(
            'user_id',
            sa.String(36),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'design_id',
            sa.String(36),
            sa.ForeignKey('designs.id', ondelete='SET NULL'),
            nullable=True
        ),
        sa.Column('external_order_id', sa.String(255), nullable=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column(
            'status',
            sa.String(50),
            nullable=False,
            server_default='pending'
        ),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        comment='Orders placed through integrations (Shopify, WooCommerce)'
    )
    
    # Orders indexes
    op.create_index('ix_orders_user_id', 'orders', ['user_id'])
    op.create_index('ix_orders_design_id', 'orders', ['design_id'])
    op.create_index('ix_orders_created_at', 'orders', ['created_at'])
    op.create_index(
        'ix_orders_user_created',
        'orders',
        ['user_id', 'created_at']
    )
    op.create_index(
        'ix_orders_external_platform',
        'orders',
        ['external_order_id', 'platform']
    )
    
    # Orders check constraints
    op.create_check_constraint(
        'ck_orders_platform',
        'orders',
        sa.text("platform IN ('shopify', 'woocommerce', 'manual')")
    )
    op.create_check_constraint(
        'ck_orders_status',
        'orders',
        sa.text("status IN ('pending', 'processing', 'completed', 'failed')")
    )
    
    # ============================================================
    # TABLE: shopify_stores
    # ============================================================
    op.create_table(
        'shopify_stores',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column(
            'user_id',
            sa.String(36),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            unique=True
        ),
        sa.Column('shop_domain', sa.String(255), nullable=False, unique=True),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('scopes', sa.String(500), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column(
            'installed_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ),
        sa.Column('uninstalled_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_shopify_stores_user_id'),
        sa.UniqueConstraint('shop_domain', name='uq_shopify_stores_shop_domain'),
        comment='Shopify store integrations'
    )
    
    # Shopify stores indexes
    op.create_index('ix_shopify_stores_user_id', 'shopify_stores', ['user_id'], unique=True)
    op.create_index('ix_shopify_stores_shop_domain', 'shopify_stores', ['shop_domain'], unique=True)
    op.create_index(
        'ix_shopify_stores_active',
        'shopify_stores',
        ['is_active']
    )
    
    # ============================================================
    # TRIGGERS: updated_at auto-update
    # ============================================================
    
    # Create trigger function (only once)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply trigger to tables
    for table in ['users', 'subscriptions', 'designs']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """Drop all tables and functions."""
    
    # Drop triggers
    for table in ['users', 'subscriptions', 'designs']:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")
    
    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop tables (in reverse order to respect foreign keys)
    op.drop_table('shopify_stores')
    op.drop_table('orders')
    op.drop_table('designs')
    op.drop_table('subscriptions')
    op.drop_table('users')