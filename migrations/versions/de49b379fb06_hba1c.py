"""empty message

Revision ID: de49b379fb06
Revises: a30d3ce6eb56
Create Date: 2020-11-03 09:03:31.350640

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "de49b379fb06"
down_revision = "a30d3ce6eb56"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hba1c_reading",
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("created_by_", sa.String(), nullable=False),
        sa.Column("modified", sa.DateTime(timezone=True), nullable=False),
        sa.Column("modified_by_", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("units", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("measured_timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index("hba1c_reading_uuid", "hba1c_reading", ["uuid"], unique=True)
    op.create_index("hba1c_patient_id", "hba1c_reading", ["patient_id"], unique=False)
    op.create_index(
        "hba1c_reading_measured_ts",
        "hba1c_reading",
        ["measured_timestamp"],
        unique=False,
    )


def downgrade():
    op.drop_index("hba1c_reading_uuid", table_name="hba1c_reading")
    op.drop_index("hba1c_patient_id", table_name="hba1c_reading")
    op.drop_index("hba1c_reading_measured_ts", table_name="hba1c_reading")
    op.drop_table("hba1c_reading")
