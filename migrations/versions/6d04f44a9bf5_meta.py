"""meta

Revision ID: 6d04f44a9bf5
Revises: eead4a2e6a37
Create Date: 2022-01-21 13:49:08.375362

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6d04f44a9bf5"
down_revision = "eead4a2e6a37"
branch_labels = None
depends_on = None


def upgrade():
    print("Adding columns `reading_is_correct` and `transmitted_reading` to metadata.")
    op.add_column(
        "reading_metadata",
        sa.Column("reading_is_correct", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "reading_metadata",
        sa.Column("transmitted_reading", sa.Float(), nullable=True),
    )
    print(
        "Completed adding columns `reading_is_correct` and `transmitted_reading` to metadata."
    )


def downgrade():
    print(
        "Removing columns `reading_is_correct` and `transmitted_reading` from metadata."
    )
    op.drop_column("reading_metadata", "reading_is_correct")
    op.drop_column("reading_metadata", "transmitted_reading")
    print(
        "Completed removal of columns `reading_is_correct` and `transmitted_reading` from metadata."
    )
