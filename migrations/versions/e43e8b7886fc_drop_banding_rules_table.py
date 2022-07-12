"""Drop banding rules table

Revision ID: e43e8b7886fc
Revises: a6461e046f3e
Create Date: 2019-09-26 11:04:09.488859

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from sqlalchemy import table, column

revision = "e43e8b7886fc"
down_revision = "a6461e046f3e"
branch_labels = None
depends_on = None

reading_banding_rule_table = table(
    "reading_banding_rule",
    column("uuid", sa.String),
    column("created", sa.DateTime),
    column("modified", sa.DateTime),
    column("reading_banding_id", sa.String(36)),
    column("prandial_tag_id", sa.String(36)),
    column("minimum_value", sa.Float()),
    column("maximum_value", sa.Float()),
)

data = [
    {
        "uuid": "abce2c07-cbf3-46ca-bec5-2a35bcc45c95",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": None,
        "maximum_value": 4.0,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-BREAKFAST",
        "reading_banding_id": "BG-READING-BANDING-LOW",
    },
    {
        "uuid": "4591044f-26ef-4042-bce3-0d2902c53fe5",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 4.0,
        "maximum_value": 5.3,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-BREAKFAST",
        "reading_banding_id": "BG-READING-BANDING-NORMAL",
    },
    {
        "uuid": "707138bf-e7c2-4bbe-9bdf-15490306a5d9",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 5.3,
        "maximum_value": None,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-BREAKFAST",
        "reading_banding_id": "BG-READING-BANDING-HIGH",
    },
    {
        "uuid": "d8e86dc9-c74f-4c5e-b9d2-afb880028deb",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": None,
        "maximum_value": 4.0,
        "prandial_tag_id": None,
        "reading_banding_id": "BG-READING-BANDING-LOW",
    },
    {
        "uuid": "e7af1d13-27d6-43c2-9c05-ea032ff56c78",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 4.0,
        "maximum_value": 7.8,
        "prandial_tag_id": None,
        "reading_banding_id": "BG-READING-BANDING-NORMAL",
    },
    {
        "uuid": "83f95fd2-38a5-4c79-b6c1-5050389072e3",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 7.8,
        "maximum_value": None,
        "prandial_tag_id": None,
        "reading_banding_id": "BG-READING-BANDING-HIGH",
    },
    {
        "uuid": "cfb805c0-6655-4b36-92f7-57995f3681de",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 4.0,
        "maximum_value": 6.0,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-LUNCH",
        "reading_banding_id": "BG-READING-BANDING-NORMAL",
    },
    {
        "uuid": "90d29eea-d6ae-4a04-ad9b-c1fba5cc6d80",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 6.0,
        "maximum_value": None,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-LUNCH",
        "reading_banding_id": "BG-READING-BANDING-HIGH",
    },
    {
        "uuid": "f3b08430-e45d-4e00-987b-b888269debe5",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 4.0,
        "maximum_value": 6.0,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-DINNER",
        "reading_banding_id": "BG-READING-BANDING-NORMAL",
    },
    {
        "uuid": "2fd65e9b-8db0-4fd1-9136-5304c321a30d",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "minimum_value": 6.0,
        "maximum_value": None,
        "prandial_tag_id": "PRANDIAL-TAG-BEFORE-DINNER",
        "reading_banding_id": "BG-READING-BANDING-HIGH",
    },
]


def upgrade():
    op.drop_table("reading_banding_rule")


def downgrade():
    op.create_table(
        "reading_banding_rule",
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("modified", sa.DateTime(), nullable=False),
        sa.Column("minimum_value", sa.Float(), nullable=True),
        sa.Column("maximum_value", sa.Float(), nullable=True),
        sa.Column("prandial_tag_id", sa.String(length=36), nullable=True),
        sa.Column("reading_banding_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(("prandial_tag_id",), ["prandial_tag.uuid"]),
        sa.ForeignKeyConstraint(("reading_banding_id",), ["reading_banding.uuid"]),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.bulk_insert(reading_banding_rule_table, data)
