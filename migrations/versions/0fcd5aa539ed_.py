"""empty message

Revision ID: 0fcd5aa539ed
Revises: 3f30fb1e5fa0
Create Date: 2018-03-23 21:37:16.706155

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = '0fcd5aa539ed'
down_revision = '3f30fb1e5fa0'
branch_labels = None
depends_on = None

reading_banding_rule_table = table('reading_banding_rule',
    column('uuid', sa.String),
    column('created', sa.DateTime),
    column('modified', sa.DateTime),
    column('reading_banding_id', sa.String(36)),
    column('prandial_tag_id', sa.String(36)),
    column('minimum_value', sa.Float()),
    column('maximum_value', sa.Float())
)

data = [
    {
        "uuid": "cfb805c0-6655-4b36-92f7-57995f3681de",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 4.0,
        "maximum_value": 6.0,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-LUNCH",
        "reading_banding_id": "BG-READING-BANDING-NORMAL"
    },
    {
        "uuid": "90d29eea-d6ae-4a04-ad9b-c1fba5cc6d80",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 6.0,
        "maximum_value": None,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-LUNCH",
        "reading_banding_id": "BG-READING-BANDING-HIGH"
    },
    {
        "uuid": "f3b08430-e45d-4e00-987b-b888269debe5",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 4.0,
        "maximum_value": 6.0,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-DINNER",
        "reading_banding_id": "BG-READING-BANDING-NORMAL"
    },
    {
        "uuid": "2fd65e9b-8db0-4fd1-9136-5304c321a30d",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 6.0,
        "maximum_value": None,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-DINNER",
        "reading_banding_id": "BG-READING-BANDING-HIGH"
    }
]


def upgrade():

    op.bulk_insert(reading_banding_rule_table, data)


def downgrade():

    op.execute(
        reading_banding_rule_table
        .delete()
        .where(reading_banding_rule_table.c.uuid.in_(["2fd65e9b-8db0-4fd1-9136-5304c321a30d",
                                                      "f3b08430-e45d-4e00-987b-b888269debe5",
                                                      "90d29eea-d6ae-4a04-ad9b-c1fba5cc6d80",
                                                      "cfb805c0-6655-4b36-92f7-57995f3681de"]))
    )
