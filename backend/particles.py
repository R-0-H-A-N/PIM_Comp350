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

    return [{'particle_id': row[0], 'title': row[1], 'content': row[2]} for row in rows]

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


def delete_article(particle_id):
    """
    Delete article by article_id. Returns True if deleted, False otherwise.
    
    SIGNATURE
    ---------
        (str) -> bool    
    """
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM particles WHERE article_id = ?", (particle_id,))
    conn.commit()
    deleted = cursor.rowcount > 0

    conn.close()

    return deleted

def edit_particle(username, password, particle_id):
    """
    This funciton allows for the updating of particles. Such as saving new changes to the title or content
    # TODO: Write this function.
    """
    pass

def particle_views_count(particle_id):
    """
    This functions is somewhat of a counter for the number of times a particle has been viewed.
    # TODO: Maybe make a feature where the most viewed particles are showed higher up on the list when searching for particles. Or make more viewed particles more favoured for instant searches regardless of similarity.
    # TODO: Maybe add a weight system to the particles that weighs between similarity and popularity
    """
    pass