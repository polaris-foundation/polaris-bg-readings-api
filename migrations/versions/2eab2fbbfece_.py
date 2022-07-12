"""empty message

Revision ID: 2eab2fbbfece
Revises: 0fcd5aa539ed
Create Date: 2018-03-22 11:16:31.076602

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2eab2fbbfece'
down_revision = '0fcd5aa539ed'
branch_labels = None
depends_on = None


def upgrade():

    op.create_table('alert',
                    sa.Column('uuid', sa.String(length=36), nullable=False),
                    sa.Column('created', sa.DateTime(), nullable=False),
                    sa.Column('modified', sa.DateTime(), nullable=False),
                    sa.PrimaryKeyConstraint('uuid')
                    )

    op.add_column('reading', sa.Column(
        'alert_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('reading_alert', 'reading',
                          'alert', ['alert_id'], ['uuid'])
    op.alter_column('reading_banding', 'value',
                    existing_type=sa.INTEGER(), nullable=False)


def downgrade():

    op.alter_column('reading_banding', 'value',
                    existing_type=sa.INTEGER(), nullable=True)
    op.drop_constraint('reading_alert', 'reading', type_='foreignkey')
    op.drop_column('reading', 'alert_id')
    op.drop_table('alert')
