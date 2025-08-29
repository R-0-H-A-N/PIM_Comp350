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


def delete_article(particle_id: int):
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

def edit_particle(username: str, password: str, particle_id: str, new_title: str = None, new_content: str = None) -> bool:
    """
    This function allows for the updating of particles, such as saving new changes to the title or content.
    Only the owner of the particle (authenticated by username and password) can edit it.

    Args:
        username (str): The username of the user attempting to edit the particle.
        password (str): The password of the user (for authentication).
        particle_id (str): The ID of the particle to edit.
        new_title (str, optional): The new title for the particle.
        new_content (str, optional): The new content for the particle.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    import sqlite3
    from backend import auth

    # Authenticate user
    if not auth.login(username, password):
        return False

    # Only update if at least one field is provided
    if new_title is None and new_content is None:
        return False

    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()

    # Build the update query dynamically
    fields = []
    values = []
    if new_title is not None:
        fields.append("title = ?")
        values.append(new_title)
    if new_content is not None:
        fields.append("content = ?")
        values.append(new_content)
    values.extend([username, particle_id])

    query = f"UPDATE particles SET {', '.join(fields)} WHERE username = ? AND article_id = ?"
    cursor.execute(query, tuple(values))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    
    return updated

def particle_views_count(particle_id: str):
    """
    This functions is somewhat of a counter for the number of times a particle has been viewed.
    # TODO: Maybe make a feature where the most viewed particles are showed higher up on the list when searching for particles. Or make more viewed particles more favoured for instant searches regardless of similarity.
    # TODO: Maybe add a weight system to the particles that weighs between similarity and popularity
    """
    pass