"""Backfill password hashes for legacy local users.

Revision ID: 20260330_0024
Revises: 20260330_0023
Create Date: 2026-03-30 10:20:00.000000

"""

from __future__ import annotations

import hashlib
import secrets

from alembic import op
import sqlalchemy as sa


revision = "20260330_0024"
down_revision = "20260330_0023"
branch_labels = None
depends_on = None

LEGACY_DEFAULT_PASSWORD = "password123"


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return f"{salt}${digest.hex()}"


def upgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT id
            FROM user_accounts
            WHERE auth_provider = 'internal' AND password_hash IS NULL
            """
        )
    ).fetchall()
    for row in rows:
        connection.execute(
            sa.text(
                """
                UPDATE user_accounts
                SET password_hash = :password_hash
                WHERE id = :user_id
                """
            ),
            {"user_id": row.id, "password_hash": _hash_password(LEGACY_DEFAULT_PASSWORD)},
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE user_accounts
            SET password_hash = NULL
            WHERE auth_provider = 'internal'
            """
        )
    )
