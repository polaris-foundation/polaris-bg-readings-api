"""percentages alerts

Revision ID: a30d3ce6eb56
Revises: e43e8b7886fc
Create Date: 2019-10-14 14:28:49.589433

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a30d3ce6eb56"
down_revision = "e43e8b7886fc"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "patient_alert",
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("created_by_", sa.String(), nullable=False),
        sa.Column("modified", sa.DateTime(), nullable=False),
        sa.Column("modified_by_", sa.String(), nullable=False),
        sa.Column("dismissed_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column(
            "alert_type",
            sa.Enum(
                "COUNTS_RED",
                "COUNTS_AMBER",
                "PERCENTAGES_RED",
                "PERCENTAGES_AMBER",
                "ACTIVITY_GREY",
                name="alerttype",
            ),
            nullable=False,
        ),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patient.uuid"]),
        sa.PrimaryKeyConstraint("uuid"),
    )


def downgrade():
    op.drop_table("patient_alert")
    sa.Enum(name="alerttype").drop(op.get_bind(), checkfirst=False)
