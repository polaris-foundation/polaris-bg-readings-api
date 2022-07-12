"""amber_alert

Revision ID: d8a8dd9d1055
Revises: 8fdfb572fd2b
Create Date: 2018-06-12 10:40:49.354434

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8a8dd9d1055'
down_revision = '8fdfb572fd2b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('amber_alert',
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('created_by_', sa.String(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('modified_by_', sa.String(), nullable=False),
        sa.Column('dismissed', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('uuid')
    )
    op.add_column('reading', sa.Column('amber_alert_id', sa.String(length=36),
                                       nullable=True))
    op.create_foreign_key(None, 'reading', 'amber_alert', ['amber_alert_id'],
                          ['uuid'])
    op.alter_column('patient', 'current_reading_alert', nullable=False,
                    new_column_name='current_red_alert')


def downgrade():
    op.alter_column('patient', 'current_red_alert', nullable=False,
                    new_column_name='current_reading_alert')
    op.drop_column('reading', 'amber_alert_id')
    op.drop_table('amber_alert')

