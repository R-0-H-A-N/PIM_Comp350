"""
This file handles all operations on particles
"""
# TODO: Populate the particles table in the database with data

import sqlite3

def view_articles(username):
    """
    Return all articles of a user as a list of dictionaries.
    
    SIGNATURE
    ---------
        (str) -> list[dict]
    """
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()
    cursor.execute("SELECT article_id, title, content FROM particles WHERE username = ?", (username,))
    rows = cursor.fetchall()
    conn.close()

    return [{'article_id': row[0], 'title': row[1], 'content': row[2]} for row in rows]

def search_article(username, search_term):
    """
    Return articles of a user where the title or content matches the search term.
    
    SIGNATURE
    ---------
        (str) -> list[dict]
    """
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()
    like_term = f'%{search_term}%'
    cursor.execute("""
        SELECT article_id, title, content FROM particles 
        WHERE username = ? AND (title LIKE ? OR content LIKE ?)
        """, (username, like_term, like_term))
    
    rows = cursor.fetchall()
    conn.close()

    return [{'article_id': row[0], 'title': row[1], 'content': row[2]} for row in rows]


def delete_article(article_id):
    """
    Delete article by article_id. Returns True if deleted, False otherwise.
    
    SIGNATURE
    ---------
        (str) -> bool    
    """
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM particles WHERE article_id = ?", (article_id,))
    conn.commit()
    deleted = cursor.rowcount > 0

    conn.close()

    return deleted
