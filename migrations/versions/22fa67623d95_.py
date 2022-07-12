"""empty message

Revision ID: 22fa67623d95
Revises: 5ab8a42be883
Create Date: 2018-03-19 15:41:44.530040

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22fa67623d95'
down_revision = '5ab8a42be883'
branch_labels = None
depends_on = None


def upgrade():

    op.create_index('reading_patient_id', 'reading', ['patient_id'], unique=False)


def downgrade():

    op.drop_index('reading_patient_id', table_name='reading')
