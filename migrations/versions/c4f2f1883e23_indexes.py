"""indexes

Revision ID: c4f2f1883e23
Revises: 87bae830fb1e
Create Date: 2018-08-22 12:22:04.323269

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4f2f1883e23'
down_revision = '87bae830fb1e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('reading_metadata_uuid', 'reading_metadata', ['uuid'], unique=True)
    op.create_index('reading_uuid', 'reading', ['uuid'], unique=True)
    op.create_index('reading_patient_id', 'reading', ['patient_id'], unique=False)
    op.create_index('reading_measured_ts', 'reading', ['measured_timestamp'], unique=False)
    op.create_index('prandial_tag_uuid', 'prandial_tag', ['uuid'], unique=True)
    op.create_index('dose_uuid', 'dose', ['uuid'], unique=True)


def downgrade():
    op.drop_index('dose_uuid', table_name='dose')
    op.drop_index('prandial_tag_uuid', table_name='prandial_tag')
    op.drop_index('reading_patient_id', table_name='reading')
    op.drop_index('reading_measured_ts', table_name='reading')
    op.drop_index('reading_uuid', table_name='reading')
    op.drop_index('reading_metadata_uuid', table_name='reading_metadata')

