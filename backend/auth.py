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

def reauthenticate_on_expiry(username: str, get_password_input_func, logout_func, verify_password_func, max_attempts: int = 3) -> bool:
    """
    Prompt the user to re-enter their password when the session expires.
    If the password is entered incorrectly 3 times, log out the session.

    PARAMETERS
    ----------
        :username: String for the username of the user whose session expired
        :get_password_input_func: Callable that prompts the user for their password and returns it as a string
        :logout_func: Callable that logs out the user/session
        :verify_password_func: Callable that takes (username, password) and returns True if valid, else False
        :max_attempts: Integer for maximum number of allowed attempts (default 3)

    SIGNATURE
    ---------
        (str, Callable, Callable, Callable, int) -> bool
    """
    attempts = 0
    while attempts < max_attempts:
        password = get_password_input_func()
        if verify_password_func(username, password):
            return True
        attempts += 1
    # Too many failed attempts, log out
    logout_func(username)
    return False

# HELPER FUNCTIONS
def hash_password(password: str) -> str:
    """
    Generate a salted bcrypt hash for the given password.

    PARAMETERS
    ----------
        :password: String password to hash

    SIGNATURE
    ---------
        (str) -> str
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a bcrypt hash.

    PARAMETERS
    ----------
        :password: String password to verify
        :hashed: String bcrypt hash to check against

    SIGNATURE
    ---------
        (str, str) -> bool
    """
    # hashed is stored as decoded string; bcrypt expects bytes
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def hash_token(token: str) -> str:
    """
    Hash session token with SHA256 before storing in DB.

    PARAMETERS
    ----------
        :token: String session token

    SIGNATURE
    ---------
        (str) -> str
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# AUTH FUNCTIONS
def login(username: str, password: str) -> Optional[str]:
    """
    Verify username and password.
    If successful, create a new session and return session token (raw).
    Returns None on failure.

    PARAMETERS
    ----------
        :username: String username to authenticate
        :password: String password to authenticate

    SIGNATURE
    ---------
        (str, str) -> Optional[str]
    """

    # Checking for format to avoid sql injection
    if not isinstance(username, str) or not username.isalnum() or len(username) > 64:
        return None

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
    """
    Check if a given session token is valid and not expired. Returns user_id or None.

    PARAMETERS
    ----------
        :token: String session token

    SIGNATURE
    ---------
        (str) -> Optional[int]
    """
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

    PARAMETERS
    ----------
        :username: String username for the new user
        :password: String password for the new user
        :admin_key: Optional string admin key for validation
        :master_admin_key: Optional string master admin key for validation

    SIGNATURE
    ---------
        (str, str, Optional[str], Optional[str]) -> bool
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

    PARAMETERS
    ----------
        :username: String username to delete
        :password: String password for verification

    SIGNATURE
    ---------
        (str, str) -> bool
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

    PARAMETERS
    ----------
        :username: String username whose password is to be changed
        :old_password: String current password
        :new_password: String new password

    SIGNATURE
    ---------
        (str, str, str) -> bool
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

    PARAMETERS
    ----------
        :username: String username whose password is to be reset
        :new_password: String new password

    SIGNATURE
    ---------
        (str, str) -> bool
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

    PARAMETERS
    ----------
        :username: String username to fetch details for

    SIGNATURE
    ---------
        (str) -> dict or None
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM auth WHERE username = ?", (username,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return {"id": row[0], "username": row[1]}
    return None
