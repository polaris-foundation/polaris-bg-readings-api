"""empty message

Revision ID: 6389580aa4c2
Revises: de49b379fb06
Create Date: 2020-11-16 10:39:40.159810

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6389580aa4c2"
down_revision = "de49b379fb06"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("hba1c_reading", sa.Column("deleted", sa.DateTime(), nullable=True))
    op.alter_column(
        "hba1c_reading",
        "measured_timestamp",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
    )


def downgrade():
    op.drop_column("hba1c_reading", "deleted")
    op.alter_column(
        "hba1c_reading",
        "measured_timestamp",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
    )
