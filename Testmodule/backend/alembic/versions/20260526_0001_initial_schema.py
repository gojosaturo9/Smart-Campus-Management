"""initial schema

Revision ID: 20260526_0001
Revises:
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa

revision = "20260526_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("file_type", sa.String(length=50), nullable=True),
        sa.Column("document_hash", sa.String(length=255), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_hash"),
    )
    op.create_index("idx_documents_id", "documents", ["id"])

    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("chapter_title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("chapter_hash", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chapter_hash"),
    )
    op.create_index("idx_chapters_document_id", "chapters", ["document_id"])

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=True),
        sa.Column("question_text", sa.Text(), nullable=True),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("question_type", sa.String(length=100), nullable=True),
        sa.Column("difficulty", sa.String(length=50), nullable=True),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_questions_chapter_id", "questions", ["chapter_id"])


def downgrade():
    op.drop_index("idx_questions_chapter_id", table_name="questions")
    op.drop_table("questions")
    op.drop_index("idx_chapters_document_id", table_name="chapters")
    op.drop_table("chapters")
    op.drop_index("idx_documents_id", table_name="documents")
    op.drop_table("documents")
