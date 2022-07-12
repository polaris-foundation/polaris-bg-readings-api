"""hba1c target

Revision ID: 8b9ef35d3500
Revises: 3153188409e2
Create Date: 2020-12-11 14:34:44.292769

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8b9ef35d3500"
down_revision = "3153188409e2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hba1c_target",
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("created_by_", sa.String(), nullable=False),
        sa.Column("modified", sa.DateTime(), nullable=False),
        sa.Column("modified_by_", sa.String(), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("units", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ("patient_id",), ["patient.uuid"], name="hba1c_target_patient_id"
        ),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index(
        op.f("ix_hba1c_target_patient_id"), "hba1c_target", ["patient_id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_hba1c_target_patient_id"), table_name="hba1c_target")
    op.drop_table("hba1c_target")
