"""Create initial tables for Epic C

Revision ID: 001
Revises: 
Create Date: 2025-10-26 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create normalized_trades table
    op.create_table(
        'normalized_trades',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', sa.String(length=50), nullable=True),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('price', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ingest_job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_account_symbol', 'normalized_trades', ['account_id', 'symbol'])
    op.create_index('idx_symbol_executed_at', 'normalized_trades', ['symbol', 'executed_at'])
    op.create_index(op.f('ix_normalized_trades_account_id'), 'normalized_trades', ['account_id'])
    op.create_index(op.f('ix_normalized_trades_executed_at'), 'normalized_trades', ['executed_at'])
    op.create_index(op.f('ix_normalized_trades_ingest_job_id'), 'normalized_trades', ['ingest_job_id'])
    op.create_index(op.f('ix_normalized_trades_symbol'), 'normalized_trades', ['symbol'])
    
    # Create closed_lots table
    op.create_table(
        'closed_lots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', sa.String(length=50), nullable=True),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('position_type', sa.String(length=10), nullable=False),
        sa.Column('open_trade_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('open_quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('open_price', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('open_executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('close_trade_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('close_quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('close_price', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('close_executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('realized_pnl', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_account_close_date', 'closed_lots', ['account_id', 'close_executed_at'])
    op.create_index('idx_symbol_close_date', 'closed_lots', ['symbol', 'close_executed_at'])
    op.create_index(op.f('ix_closed_lots_account_id'), 'closed_lots', ['account_id'])
    op.create_index(op.f('ix_closed_lots_close_executed_at'), 'closed_lots', ['close_executed_at'])
    op.create_index(op.f('ix_closed_lots_open_executed_at'), 'closed_lots', ['open_executed_at'])
    op.create_index(op.f('ix_closed_lots_realized_pnl'), 'closed_lots', ['realized_pnl'])
    op.create_index(op.f('ix_closed_lots_symbol'), 'closed_lots', ['symbol'])
    
    # Create per_day_pnl table
    op.create_table(
        'per_day_pnl',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', sa.String(length=50), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('cumulative_pnl', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('daily_pnl', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('lots_closed', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_account_date', 'per_day_pnl', ['account_id', 'date'], unique=True)
    op.create_index(op.f('ix_per_day_pnl_account_id'), 'per_day_pnl', ['account_id'])
    op.create_index(op.f('ix_per_day_pnl_date'), 'per_day_pnl', ['date'])
    
    # Create aggregates table
    op.create_table(
        'aggregates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', sa.String(length=50), nullable=True),
        sa.Column('total_realized_pnl', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('total_lots_closed', sa.Integer(), nullable=False),
        sa.Column('total_trades', sa.Integer(), nullable=False),
        sa.Column('winning_lots', sa.Integer(), nullable=False),
        sa.Column('losing_lots', sa.Integer(), nullable=False),
        sa.Column('total_gains', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('total_losses', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('win_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('profit_factor', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('average_gain', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('average_loss', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('best_symbol', sa.String(length=10), nullable=True),
        sa.Column('best_symbol_pnl', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('worst_symbol', sa.String(length=10), nullable=True),
        sa.Column('worst_symbol_pnl', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('best_weekday', sa.String(length=10), nullable=True),
        sa.Column('best_weekday_pnl', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('worst_weekday', sa.String(length=10), nullable=True),
        sa.Column('worst_weekday_pnl', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('first_trade_date', sa.Date(), nullable=True),
        sa.Column('last_trade_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_aggregates_account_id'), 'aggregates', ['account_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_aggregates_account_id'), table_name='aggregates')
    op.drop_table('aggregates')
    
    op.drop_index(op.f('ix_per_day_pnl_date'), table_name='per_day_pnl')
    op.drop_index(op.f('ix_per_day_pnl_account_id'), table_name='per_day_pnl')
    op.drop_index('idx_account_date', table_name='per_day_pnl')
    op.drop_table('per_day_pnl')
    
    op.drop_index(op.f('ix_closed_lots_symbol'), table_name='closed_lots')
    op.drop_index(op.f('ix_closed_lots_realized_pnl'), table_name='closed_lots')
    op.drop_index(op.f('ix_closed_lots_open_executed_at'), table_name='closed_lots')
    op.drop_index(op.f('ix_closed_lots_close_executed_at'), table_name='closed_lots')
    op.drop_index(op.f('ix_closed_lots_account_id'), table_name='closed_lots')
    op.drop_index('idx_symbol_close_date', table_name='closed_lots')
    op.drop_index('idx_account_close_date', table_name='closed_lots')
    op.drop_table('closed_lots')
    
    op.drop_index(op.f('ix_normalized_trades_symbol'), table_name='normalized_trades')
    op.drop_index(op.f('ix_normalized_trades_ingest_job_id'), table_name='normalized_trades')
    op.drop_index(op.f('ix_normalized_trades_executed_at'), table_name='normalized_trades')
    op.drop_index(op.f('ix_normalized_trades_account_id'), table_name='normalized_trades')
    op.drop_index('idx_symbol_executed_at', table_name='normalized_trades')
    op.drop_index('idx_account_symbol', table_name='normalized_trades')
    op.drop_table('normalized_trades')
