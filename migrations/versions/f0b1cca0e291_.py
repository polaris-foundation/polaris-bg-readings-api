"""empty message

Revision ID: 1cf1274a0f26
Revises: aec5b45a6424
Create Date: 2017-12-21 13:29:20.028473

"""
from alembic import op
import sqlalchemy as sa

from datetime import datetime
from sqlalchemy.sql import table, column
from alembic import op


# revision identifiers, used by Alembic.
revision = 'f0b1cca0e291'
down_revision = '254b34815457'
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
        'uuid': 'PRANDIAL-TAG-NONE',
        'created': datetime.utcnow(),
        'modified': datetime.utcnow(),
        'description': 'none',
        'value': 0,
    },
    {
        'uuid': 'PRANDIAL-TAG-BEFORE-BREAKFAST',
        'created': datetime.utcnow(),
        'modified': datetime.utcnow(),
        'description': 'before_breakfast',
        'value': 1,
    },
    {
        'uuid': 'PRANDIAL-TAG-AFTER-BREAKFAST',
        'created': datetime.utcnow(),
        'modified': datetime.utcnow(),
        'description': 'after_breakfast',
        'value': 2,
    },
    {
        'uuid': 'PRANDIAL-TAG-BEFORE-LUNCH',
        'created': datetime.utcnow(),
        'modified': datetime.utcnow(),
        'description': 'before_lunch',
        'value': 3,
    },
    {
        'uuid': 'PRANDIAL-TAG-AFTER-LUNCH',
        'created': datetime.utcnow(),
        'modified': datetime.utcnow(),
        'description': 'after_lunch',
        'value': 4,
    },
    {
        'uuid': 'PRANDIAL-TAG-BEFORE-DINNER',
        'created': datetime.utcnow(),
        'modified': datetime.utcnow(),
        'description': 'before_dinner',
        'value': 5,
    },
    {
        'uuid': 'PRANDIAL-TAG-AFTER-DINNER',
        'created': datetime.utcnow(),
        'modified': datetime.utcnow(),
        'description': 'after_dinner',
        'value': 6,
    },
    {
        'uuid': 'PRANDIAL-TAG-OTHER',
        'created': datetime.utcnow(),
        'modified': datetime.utcnow(),
        'description': 'other',
        'value': 7,
    },
]


def upgrade():
    op.bulk_insert(prandial_tag_table, data)


def downgrade():
    op.execute(
        prandial_tag_table.delete()
    )
