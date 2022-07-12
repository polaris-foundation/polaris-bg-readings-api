"""empty message

Revision ID: d04a111aa4fc
Revises: 95f6577955d6
Create Date: 2018-02-16 16:18:11.412929

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd04a111aa4fc'
down_revision = '95f6577955d6'
branch_labels = None
depends_on = None


def upgrade():

    op.drop_table('note')
    op.add_column('reading', sa.Column('comment', sa.String(), nullable=True))


def downgrade():

    op.drop_column('reading', 'comment')
    op.create_table('note',
                    sa.Column('uuid', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
                    sa.Column('created', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
                    sa.Column('modified', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
                    sa.Column('creator', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
                    sa.Column('content', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.Column('reading_id', sa.VARCHAR(length=36), autoincrement=False, nullable=True),
                    sa.Column('added_timestamp', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
                    sa.Column('added_timezone', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('visible_to_patient', sa.BOOLEAN(), autoincrement=False, nullable=False),
                    sa.ForeignKeyConstraint(['reading_id'], ['reading.uuid'], name='note_reading_id_fkey'),
                    sa.PrimaryKeyConstraint('uuid', name='note_pkey')
    )
