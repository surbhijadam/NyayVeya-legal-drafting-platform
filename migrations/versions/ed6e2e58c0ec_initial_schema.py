"""initial_schema

Revision ID: ed6e2e58c0ec
Revises: 
Create Date: 2026-10-23 11:31:24.041649

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ed6e2e58c0ec'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. document_templates table
    op.create_table(
        'document_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('subtitle', sa.String(length=300), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('short_description', sa.Text(), nullable=False),
        sa.Column('long_description', sa.Text(), nullable=False),
        sa.Column('what_you_get_json', sa.Text(), nullable=True),
        sa.Column('information_needed_json', sa.Text(), nullable=True),
        sa.Column('important_notes_json', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=100), nullable=True),
        sa.Column('badge_text', sa.String(length=50), nullable=True),
        sa.Column('badge_class', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_templates_slug'), 'document_templates', ['slug'], unique=True)

    # 3. orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_number', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('document_template_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('form_data_json', sa.Text(), nullable=True),
        sa.Column('docx_filename', sa.String(length=255), nullable=True),
        sa.Column('pdf_filename', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_template_id'], ['document_templates.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_orders_user_id'), 'orders', ['user_id'], unique=False)
    op.create_index(op.f('ix_orders_document_template_id'), 'orders', ['document_template_id'], unique=False)

    # 4. payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('gateway', sa.String(length=50), nullable=False),
        sa.Column('gateway_order_id', sa.String(length=100), nullable=True),
        sa.Column('gateway_payment_id', sa.String(length=100), nullable=True),
        sa.Column('gateway_signature', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('error_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=False)
    op.create_index(op.f('ix_payments_gateway_order_id'), 'payments', ['gateway_order_id'], unique=False)
    op.create_index(op.f('ix_payments_gateway_payment_id'), 'payments', ['gateway_payment_id'], unique=False)


def downgrade():
    op.drop_table('payments')
    op.drop_table('orders')
    op.drop_table('document_templates')
    op.drop_table('users')
