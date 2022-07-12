"""empty message

Revision ID: 3f30fb1e5fa0
Revises: 22fa67623d95
Create Date: 2018-03-19 16:56:36.141977

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '3f30fb1e5fa0'
down_revision = '22fa67623d95'
branch_labels = None
depends_on = None

# Minimal table definition for poulate value query
reading_bandings_table = sa.Table('reading_banding', sa.MetaData(),
    sa.Column('uuid', sa.String, primary_key=True),
    sa.Column('value', sa.Integer),
    sa.Column('description', sa.String()),
    sa.Column('created', sa.DateTime),
    sa.Column('modified', sa.DateTime)
)

description_to_value = {"low": 1,
                        "normal": 2,
                        "high": 3
                        }


def upgrade():
    connection = op.get_bind()
    connection.execute(reading_bandings_table
                       .delete()
                       .where(sa.not_(reading_bandings_table.c.description.in_(description_to_value))))

    op.add_column('reading_banding', sa.Column('value', sa.Integer(), nullable=True))
    op.create_unique_constraint('reading_banding_value', 'reading_banding', ['value'])

    # Populate each value based on the description
    for row in connection.execute(sa.select([reading_bandings_table.c.uuid, reading_bandings_table.c.description])):
        connection.execute(
            reading_bandings_table.update()
                                  .values(value=description_to_value[row['description']])
                                  .where(reading_bandings_table.c.uuid == row['uuid'])
        )


def downgrade():

    op.drop_constraint('reading_banding_value', 'reading_banding', type_='unique')
    op.drop_column('reading_banding', 'value')

    connection = op.get_bind()
    connection.execute(reading_bandings_table
                       .insert(),
                       [
                           {
                               "uuid": "BG-READING-BANDING-VERY-LOW",
                               "created": datetime.utcnow(),
                               "modified": datetime.utcnow(),
                               "description": "very low"
                           },
                           {
                               "uuid": "BG-READING-BANDING-VERY-HIGH",
                               "created": datetime.utcnow(),
                               "modified": datetime.utcnow(),
                               "description": "very high"
                           }
                       ])
