"""empty message

Revision ID: 4b1da562a98d
Revises: 537a505b8d46
Create Date: 2018-02-01 23:41:30.619094

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = '4b1da562a98d'
down_revision = '537a505b8d46'
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
        "uuid": "abce2c07-cbf3-46ca-bec5-2a35bcc45c95",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": None,
        "maximum_value": 4.0,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-BREAKFAST",
        "reading_banding_id": "BG-READING-BANDING-LOW"
    },
    {
        "uuid": "4591044f-26ef-4042-bce3-0d2902c53fe5",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 4.0,
        "maximum_value": 5.3,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-BREAKFAST",
        "reading_banding_id": "BG-READING-BANDING-NORMAL"
    },
    {
        "uuid": "707138bf-e7c2-4bbe-9bdf-15490306a5d9",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 5.3,
        "maximum_value": None,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-BREAKFAST",
        "reading_banding_id": "BG-READING-BANDING-HIGH"
    },
    {
        "uuid": "d8e86dc9-c74f-4c5e-b9d2-afb880028deb",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": None,
        "maximum_value": 4.0,
        "prandial_tag_id": None,
        "reading_banding_id": "BG-READING-BANDING-LOW"
    },
    {
        "uuid": "e7af1d13-27d6-43c2-9c05-ea032ff56c78",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 4.0,
        "maximum_value": 7.8,
        "prandial_tag_id": None,
        "reading_banding_id": "BG-READING-BANDING-NORMAL"
    },
    {
        "uuid": "83f95fd2-38a5-4c79-b6c1-5050389072e3",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 7.8,
        "maximum_value": None,
        "prandial_tag_id": None,
        "reading_banding_id": "BG-READING-BANDING-HIGH"
    }
]


def upgrade():

    op.bulk_insert(reading_banding_rule_table, data)


def downgrade():

    op.execute(
        reading_banding_rule_table.delete()
    )
