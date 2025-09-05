"""
This file deals with all auth related functions
"""

import sqlite3

def login(username: str, password: str):  
    # TODO: Add hashing to the passwords for more security
    # TODO: Add hashed session cookies for the user to have persistant sessions (expiry: 120 mins)
    """
    This function takes care of login verification of users. It takes the input from the form in the frontend and checks if the user exists in the database

    PARAMETERS
    ----------
        :username: String for the username of the user
        :password: String password for the username provided

    SIGNATURE
    ---------
        (str, str) -> bool
    """
    # Connect to the SQLite database
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()

    # Query to check if username and password match
    cursor.execute("SELECT 1 FROM auth WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()

    # Close the connection
    conn.close()

    # Return True if the user exists, else False
    return result is not None

def add_new_user(username: str, password: str):   # TODO: Add a extra layer of security to only allow certain users to make new users. Like an admin key that can be passed to this function that enables the add funciton for the user
    """
    This function adds a new user to the database

    PARAMETERS
    ----------
        :username: String for the username of the user
        :password: String password for the username provided

    SIGNATURE
    ---------
        (str, str) -> bool
    """
    # Connect to the SQLite database
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()

    try:
        # Insert the new user
        cursor.execute("INSERT INTO auth (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # This occurs if the username already exists (due to UNIQUE constraint)
        success = False
    finally:
        conn.close()

    return success

def delete_user(username: str, password: str):    # This function also takes password to ensure that the user that is being deleted actually is authorised to do so
    """
    This function deletes a user from the database

    PARAMETERS
    ----------
        :username: String for the username of the user
        :password: String password for the username provided

    SIGNATURE
    ---------
        (str, str) -> bool
    """
    # Connect to the SQLite database
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()

    # Execute delete command
    cursor.execute("DELETE FROM auth WHERE username = ? and password = ?", (username, password))
    conn.commit()

    # Check if any row was deleted
    deleted = cursor.rowcount > 0

    conn.close()

    return deleted

def change_password(username: str, new_password: str):
    """
    This function allows a user to reset their password given that they know their old password

    PARAMETERS
    ----------
        :username: String for the username of the user
        :new_password: String password for the username provided

    SIGNATURE
    ---------
        (str, str) -> bool
    """
    # Connect to the SQLite database
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()

    # Update the password for the given username
    cursor.execute("UPDATE auth SET password = ? WHERE username = ?", (new_password, username))
    conn.commit()

    # Check if any row was updated
    updated = cursor.rowcount > 0

    conn.close()

    return updated


def get_user_details(username: str):
    """
    This function just returns details on the user such as user id and password. 
    # TODO: Add that hashing mentioned before

    PARAMETERS
    ----------
        :username: String for the username of the user

    SIGNATURE
    ---------
        (str, str) -> dict
    """
    # Connect to the SQLite database
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()

    # Query to get user details except password
    cursor.execute("SELECT id, username, password FROM auth WHERE username = ?", (username,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return {'id': row[0], 'username': row[1], 'password': row[2]}
    else:
        return None
