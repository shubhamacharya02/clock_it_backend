"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-30 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # 2. Create recipes & recipe_ingredients tables
    op.create_table(
        'recipes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.String(length=1024), nullable=True),
        sa.Column('storage_path', sa.String(length=1024), nullable=True),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='processing'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_recipes_user_id', 'recipes', ['user_id'])

    op.create_table(
        'recipe_ingredients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('raw_name', sa.String(length=255), nullable=False),
        sa.Column('canonical_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('requires_confirmation', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_user_modified', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_recipe_ingredients_recipe_id', 'recipe_ingredients', ['recipe_id'])
    op.create_index('idx_recipe_ingredients_canonical', 'recipe_ingredients', ['canonical_name'])

    # 3. Create products, product_variants, and inventory tables
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('brand', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_products_brand', 'products', ['brand'])
    op.create_index('idx_products_category', 'products', ['category'])
    op.create_index('idx_products_metadata_json_gin', 'products', ['metadata_json'], postgresql_using='gin')

    op.create_table(
        'product_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('size', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('size_unit', sa.String(length=50), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku')
    )
    op.create_index('idx_product_variants_product_id', 'product_variants', ['product_id'])
    op.create_index('idx_product_variants_sku', 'product_variants', ['sku'])

    op.create_table(
        'inventory',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('available_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('variant_id')
    )
    op.create_index('idx_inventory_variant_id', 'inventory', ['variant_id'])

    # 4. Create carts & cart_items tables
    op.create_table(
        'carts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_carts_user_id', 'carts', ['user_id'])

    op.create_table(
        'cart_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cart_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cart_id', 'variant_id', name='uq_cart_items_cart_variant')
    )
    op.create_index('idx_cart_items_cart_id', 'cart_items', ['cart_id'])
    op.create_index('idx_cart_items_variant_id', 'cart_items', ['variant_id'])

    # 5. Create orders & order_items tables
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_number', sa.String(length=100), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='confirmed'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number')
    )
    op.create_index('idx_orders_user_id', 'orders', ['user_id'])
    op.create_index('idx_orders_order_number', 'orders', ['order_number'])

    op.create_table(
        'order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_name_snapshot', sa.String(length=255), nullable=False),
        sa.Column('brand_snapshot', sa.String(length=255), nullable=False),
        sa.Column('size_snapshot', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('unit_snapshot', sa.String(length=50), nullable=False),
        sa.Column('unit_price_snapshot', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('line_total', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_order_items_order_id', 'order_items', ['order_id'])


def downgrade() -> None:
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('cart_items')
    op.drop_table('carts')
    op.drop_table('inventory')
    op.drop_table('product_variants')
    op.drop_table('products')
    op.drop_table('recipe_ingredients')
    op.drop_table('recipes')
    op.drop_table('users')
