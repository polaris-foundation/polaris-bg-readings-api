"""empty message

Revision ID: ab54f0b42094
Revises: 3a231d87e302
Create Date: 2018-03-22 17:39:04.961212

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab54f0b42094'
down_revision = '3a231d87e302'
branch_labels = None
depends_on = None


def upgrade():

    op.add_column('patient', sa.Column('current_activity_alert', sa.Boolean(), nullable=True))
    op.add_column('patient', sa.Column('current_reading_alert', sa.Boolean(), nullable=True))
    op.create_foreign_key('reading_patient', 'reading', 'patient', ['patient_id'], ['uuid'])


def downgrade():

    op.drop_constraint('reading_patient', 'reading', type_='foreignkey')
    op.drop_column('patient', 'current_reading_alert')
    op.drop_column('patient', 'current_activity_alert')
