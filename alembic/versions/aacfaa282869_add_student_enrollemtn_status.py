"""Add student enrollemtn status

Revision ID: aacfaa282869
Revises: 03bdded6f550
Create Date: 2026-03-01 09:23:52.769607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'aacfaa282869'
down_revision: Union[str, Sequence[str], None] = '03bdded6f550'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Define and explicitly create the custom ENUM type in PostgreSQL
    enrollment_status_enum = postgresql.ENUM('ACTIVE', 'GRADUATED', 'TRANSFERRED', 'EXPELLED', 'DROPPED_OUT', name='enrollmentstatus')
    enrollment_status_enum.create(op.get_bind())
    
    # 2. Add the column. 
    # Notice we added `server_default='ACTIVE'` so it doesn't crash if you already have students in the DB!
    op.add_column('students', sa.Column('enrollment_status', enrollment_status_enum, nullable=False, server_default='ACTIVE'))


def downgrade() -> None:
    # 1. Drop the column
    op.drop_column('students', 'enrollment_status')
    
    # 2. Explicitly drop the custom ENUM type from PostgreSQL
    enrollment_status_enum = postgresql.ENUM('ACTIVE', 'GRADUATED', 'TRANSFERRED', 'EXPELLED', 'DROPPED_OUT', name='enrollmentstatus')
    enrollment_status_enum.drop(op.get_bind())