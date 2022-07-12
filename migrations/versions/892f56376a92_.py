"""empty message

Revision ID: 892f56376a92
Revises: 5eadddc831f2
Create Date: 2018-04-12 15:43:52.740217

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '892f56376a92'
down_revision = '5eadddc831f2'
branch_labels = None
depends_on = None


def upgrade():

    op.add_column('alert', sa.Column('created_by_', sa.String(), nullable=False))
    op.add_column('alert', sa.Column('modified_by_', sa.String(), nullable=False))
    op.add_column('dose', sa.Column('created_by_', sa.String(), nullable=False))
    op.add_column('dose', sa.Column('modified_by_', sa.String(), nullable=False))
    op.add_column('patient', sa.Column('created_by_', sa.String(), nullable=False))
    op.add_column('patient', sa.Column('modified_by_', sa.String(), nullable=False))
    op.add_column('reading', sa.Column('created_by_', sa.String(), nullable=False))
    op.add_column('reading', sa.Column('modified_by_', sa.String(), nullable=False))
    op.add_column('reading_metadata', sa.Column('created_by_', sa.String(), nullable=False))
    op.add_column('reading_metadata', sa.Column('modified_by_', sa.String(), nullable=False))

    # Prepopulated data by sys
    op.add_column('prandial_tag', sa.Column('created_by_', sa.String(), nullable=False, server_default='sys'))
    op.add_column('prandial_tag', sa.Column('modified_by_', sa.String(), nullable=False, server_default='sys'))
    op.add_column('reading_banding', sa.Column('created_by_', sa.String(), nullable=False, server_default='sys'))
    op.add_column('reading_banding', sa.Column('modified_by_', sa.String(), nullable=False, server_default='sys'))
    op.add_column('reading_banding_rule', sa.Column('created_by_', sa.String(), nullable=False, server_default='sys'))
    op.add_column('reading_banding_rule', sa.Column('modified_by_', sa.String(), nullable=False, server_default='sys'))


def downgrade():

    op.drop_column('reading_metadata', 'modified_by_')
    op.drop_column('reading_metadata', 'created_by_')
    op.drop_column('reading_banding_rule', 'modified_by_')
    op.drop_column('reading_banding_rule', 'created_by_')
    op.drop_column('reading_banding', 'modified_by_')
    op.drop_column('reading_banding', 'created_by_')
    op.drop_column('reading', 'modified_by_')
    op.drop_column('reading', 'created_by_')
    op.drop_column('prandial_tag', 'modified_by_')
    op.drop_column('prandial_tag', 'created_by_')
    op.drop_column('patient', 'modified_by_')
    op.drop_column('patient', 'created_by_')
    op.drop_column('dose', 'modified_by_')
    op.drop_column('dose', 'created_by_')
    op.drop_column('alert', 'modified_by_')
    op.drop_column('alert', 'created_by_')
