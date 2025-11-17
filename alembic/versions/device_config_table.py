"""add device_config table

Revision ID: a1b2c3d4e5f6
Revises: d776ab29a494
Create Date: 2025-11-03 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd776ab29a494'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'device_config',
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('mode', sa.String(length=16), nullable=False, server_default='fallback'),
        sa.Column('fc_vwc_pct', sa.Float(), nullable=True),
        sa.Column('pwp_vwc_pct', sa.Float(), nullable=True),
        sa.Column('expected_interval_min', sa.Integer(), nullable=True),
        sa.Column('farm_id', sa.String(length=64), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['device.id'], name='fk_device_config_device_id_device', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('device_id', name='pk_device_config')
    )
    op.create_index('ix_device_config_device_id', 'device_config', ['device_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_device_config_device_id', table_name='device_config')
    op.drop_table('device_config')

