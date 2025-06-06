"""Ajout des champs objet et sender à Email

Revision ID: d909cecf09c7
Revises: 83c48b6dc890
Create Date: 2025-05-26 18:08:51.016006

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd909cecf09c7'
down_revision = '83c48b6dc890'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('email', schema=None) as batch_op:
        batch_op.add_column(sa.Column('isRead', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('isDelete', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('email', schema=None) as batch_op:
        batch_op.drop_column('isDelete')
        batch_op.drop_column('isRead')

    # ### end Alembic commands ###
