"""empty message

Revision ID: 537a505b8d46
Revises: 92cb53bbc59b
Create Date: 2018-02-01 23:27:17.719240

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = '537a505b8d46'
down_revision = '92cb53bbc59b'
branch_labels = None
depends_on = None

reading_banding_table = table('reading_banding',
    column('uuid', sa.String),
    column('created', sa.DateTime),
    column('modified', sa.DateTime),
    column('description', sa.String)
)


data = [
    {
        "uuid": "BG-READING-BANDING-VERY-LOW",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "description": "very low"
    },
    {
        "uuid": "BG-READING-BANDING-LOW",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "description": "low"
    },
    {
        "uuid": "BG-READING-BANDING-NORMAL",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "description": "normal"
    },
    {
        "uuid": "BG-READING-BANDING-HIGH",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "description": "high"
    },
    {
        "uuid": "BG-READING-BANDING-VERY-HIGH",
        "created": datetime.utcnow(),
        "modified": datetime.utcnow(),
        "description": "very high"
    }
]


def upgrade():

    op.bulk_insert(reading_banding_table, data)


def downgrade():
    
    op.execute(
        reading_banding_table.delete()
    )
