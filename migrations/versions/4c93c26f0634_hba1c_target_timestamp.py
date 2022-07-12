"""hba1c target timestamp


Revision ID: 4c93c26f0634
Revises: 8b9ef35d3500
Create Date: 2021-01-14 15:31:25.649147

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4c93c26f0634"
down_revision = "8b9ef35d3500"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "hba1c_target",
        sa.Column("target_timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE hba1c_target SET target_timestamp = modified")
    op.alter_column("hba1c_target", "target_timestamp", nullable=False)


def downgrade():
    op.drop_column("hba1c_target", "target_timestamp")
