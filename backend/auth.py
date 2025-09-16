"""
This file deals with all auth related functions
"""

import sqlite3
import bcrypt
import secrets
import hashlib
import time
from pathlib import Path
from typing import Optional

DB_PATH = "db/pim.db"
SESSION_EXPIRY = 120 * 60  # 120 minutes

# HELPER FUNCTIONS
def hash_password(password: str) -> str:
    """Generate a salted bcrypt hash for the given password"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash"""
    # hashed is stored as decoded string; bcrypt expects bytes
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def hash_token(token: str) -> str:
    """Hash session token with SHA256 before storing in DB"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


#AUTH FUNCTIONS
def login(username: str, password: str) -> Optional[str]:
    """
    Verify username and password.
    If successful, create a new session and return session token (raw).
    Returns None on failure.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, password FROM auth WHERE username = ?", (username,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    user_id, hashed_pw = row
    if verify_password(password, hashed_pw):
        # Create a new session token
        token = secrets.token_hex(32)
        hashed = hash_token(token)
        expiry = int(time.time()) + SESSION_EXPIRY

        cursor.execute(
            "INSERT INTO sessions (user_id, token, expiry) VALUES (?, ?, ?)",
            (user_id, hashed, expiry),
        )
        conn.commit()
        conn.close()
        return token  # return raw token to user (hashed version is in DB)
    else:
        conn.close()
        return None


def validate_session(token: str) -> Optional[int]:
    """Check if a given session token is valid and not expired. Returns user_id or None."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    hashed = hash_token(token)
    cursor.execute("SELECT user_id, expiry FROM sessions WHERE token = ?", (hashed,))
    row = cursor.fetchone()

    conn.close()
    if row and row[1] > int(time.time()):
        return row[0]  # return user_id
    return None


def add_new_user(
    username: str, password: str, admin_key: Optional[str] = None, master_admin_key: Optional[str] = None
) -> bool:
    """
    Add a new user. Backwards compatible:
      - main.py calls add_new_user(username, password)
      - if admin_key and master_admin_key are provided, will validate them
        (useful if you want to require an admin key for user creation).
    Returns True on success, False if username already exists or admin key mismatch.
    """
    # If master_admin_key provided, require admin_key to match
    if master_admin_key is not None and admin_key != master_admin_key:
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    hashed_pw = hash_password(password)

    try:
        cursor.execute("INSERT INTO auth (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()

    return success


def delete_user(username: str, password: str) -> bool:
    """
    Delete a user (verify password before deleting).
    Returns True if deleted, False otherwise.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT password FROM auth WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row and verify_password(password, row[0]):
        cursor.execute("DELETE FROM auth WHERE username = ?", (username,))
        conn.commit()
        deleted = cursor.rowcount > 0
    else:
        deleted = False

    conn.close()
    return deleted


def change_password(username: str, old_password: str, new_password: str) -> bool:
    """
    Change password (must provide old password).
    Returns True if changed, False otherwise.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT password FROM auth WHERE username = ?", (username,))
    row = cursor.fetchone()

    if row and verify_password(old_password, row[0]):
        new_hashed = hash_password(new_password)
        cursor.execute("UPDATE auth SET password = ? WHERE username = ?", (new_hashed, username))
        conn.commit()
        updated = cursor.rowcount > 0
    else:
        updated = False

    conn.close()
    return updated


def reset_passwd(username: str, new_password: str) -> bool:
    """
    Reset password without needing the old password (useful for admin resets).
    Returns True if updated, False if user not found.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM auth WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    new_hashed = hash_password(new_password)
    cursor.execute("UPDATE auth SET password = ? WHERE username = ?", (new_hashed, username))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def get_user_details(username: str):
    """
    Return user details (excluding password).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM auth WHERE username = ?", (username,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return {"id": row[0], "username": row[1]}
    return None
