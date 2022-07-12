"""empty message

Revision ID: facb6f6c8ceb
Revises: 4b1da562a98d
Create Date: 2018-02-14 14:12:39.081185

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'facb6f6c8ceb'
down_revision = '4b1da562a98d'
branch_labels = None
depends_on = None


def upgrade():

    op.add_column('reading_metadata', sa.Column('control', sa.Boolean(), nullable=False))
    op.add_column('reading_metadata', sa.Column('manual', sa.Boolean(), nullable=False))


def downgrade():

    op.drop_column('reading_metadata', 'manual')
    op.drop_column('reading_metadata', 'control')

