"""update vk_id column in table users

Revision ID: 3011073d5f8c
Revises: a6282258c7f1
Create Date: 2022-09-14 15:43:23.887301

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3011073d5f8c'
down_revision = 'a6282258c7f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'users', ['vk_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='unique')
    # ### end Alembic commands ###
