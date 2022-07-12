"""empty message

Revision ID: 5ab8a42be883
Revises: d04a111aa4fc
Create Date: 2018-03-06 18:46:42.599175

"""
from alembic import op
import sqlalchemy as sa

from datetime import datetime
from sqlalchemy.sql import table, column
from alembic import op


# revision identifiers, used by Alembic.
revision = '5ab8a42be883'
down_revision = 'd04a111aa4fc'
branch_labels = None
depends_on = None



# Create an ad-hoc table to use for the insert statement.
prandial_tag_table = table('prandial_tag',
    column('uuid', sa.String),
    column('created', sa.DateTime),
    column('modified', sa.DateTime),
    column('description', sa.String),
    column('value', sa.Integer)
)

data = [
    {
        'uuid': 'PRANDIAL-TAG-BED',
        'created': datetime.utcnow(),
        'modified': datetime.utcnow(),
        'description': 'bedtime',
        'value': 8,
    }
]


def upgrade():
    op.bulk_insert(prandial_tag_table, data)


def downgrade():
    op.execute(
        prandial_tag_table.delete(prandial_tag_table.c.uuid == 'PRANDIAL-TAG-BED')
    )
