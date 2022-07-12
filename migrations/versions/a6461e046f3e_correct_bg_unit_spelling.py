"""correct bg unit spelling

Revision ID: a6461e046f3e
Revises: c4f2f1883e23
Create Date: 2019-09-13 15:46:47.113395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a6461e046f3e"
down_revision = "c4f2f1883e23"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE Reading SET units='mmol/L' WHERE units='mmmol/l'")


def downgrade():
    op.execute("UPDATE Reading SET units='mmmol/l' WHERE units='mmol/L'")
