"""empty message

Revision ID: 3a231d87e302
Revises: 2eab2fbbfece
Create Date: 2018-03-22 12:09:46.787706

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a231d87e302'
down_revision = '2eab2fbbfece'
branch_labels = None
depends_on = None


reading_banding_rules_table = sa.Table('reading_banding_rule',
                                       sa.MetaData(),
                                       sa.Column('reading_banding_id',
                                                 sa.String, primary_key=True),
                                       sa.Column('alertable', sa.Boolean),
                                       )


def upgrade():

    op.create_table('patient',
                    sa.Column('uuid', sa.String(length=36), nullable=False),
                    sa.Column('created', sa.DateTime(), nullable=False),
                    sa.Column('modified', sa.DateTime(), nullable=False),
                    sa.Column('suppress_reading_alerts_until',
                              sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('uuid')
                    )
    op.add_column('alert', sa.Column('dismissed', sa.Boolean(), nullable=True))

    connection = op.get_bind()


def downgrade():

    op.drop_column('alert', 'dismissed')
    op.drop_table('patient')
