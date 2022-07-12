"""empty message

Revision ID: 95f6577955d6
Revises: facb6f6c8ceb
Create Date: 2018-02-14 16:03:57.071731

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95f6577955d6'
down_revision = 'facb6f6c8ceb'
branch_labels = None
depends_on = None


def upgrade():

    op.alter_column('reading_metadata', 'manufacturer', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column('reading_metadata', 'meter_model', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column('reading_metadata', 'meter_serial_number', existing_type=sa.VARCHAR(), nullable=True)


def downgrade():

    op.alter_column('reading_metadata', 'meter_serial_number', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('reading_metadata', 'meter_model', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('reading_metadata', 'manufacturer', existing_type=sa.VARCHAR(), nullable=False)
