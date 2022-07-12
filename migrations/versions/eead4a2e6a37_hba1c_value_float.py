"""hba1c value float

Revision ID: eead4a2e6a37
Revises: 4c93c26f0634
Create Date: 2021-01-15 11:01:07.556917

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.

revision = "eead4a2e6a37"
down_revision = "4c93c26f0634"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("hba1c_target", "value", type_=sa.Float())


def downgrade():
    op.alter_column("hba1c_target", "value", type_=sa.Integer())
