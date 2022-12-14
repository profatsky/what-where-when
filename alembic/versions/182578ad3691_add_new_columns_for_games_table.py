"""add new columns for games table

Revision ID: 182578ad3691
Revises: 79b08576d4fa
Create Date: 2022-09-18 12:38:45.512991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '182578ad3691'
down_revision = '79b08576d4fa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('games', sa.Column('respondent_id', sa.Integer(), nullable=True))
    op.add_column('games', sa.Column('question_time', sa.TIMESTAMP(), nullable=True))
    op.add_column('games', sa.Column('is_started', sa.Boolean(), nullable=False))
    op.create_index(op.f('ix_games_respondent_id'), 'games', ['respondent_id'], unique=False)
    op.create_foreign_key(None, 'games', 'users', ['respondent_id'], ['id'], ondelete='RESTRICT')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'games', type_='foreignkey')
    op.drop_index(op.f('ix_games_respondent_id'), table_name='games')
    op.drop_column('games', 'is_started')
    op.drop_column('games', 'question_time')
    op.drop_column('games', 'respondent_id')
    # ### end Alembic commands ###
