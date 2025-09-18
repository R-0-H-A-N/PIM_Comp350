"""
This file handles all operations on particles
"""

import sqlite3
import auth

def view_articles(username: str):
    """
    Return all articles of a user as a list of dictionaries.

    PARAMETERS
    ----------
        :username: String for the username of the user
    
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

def search_article(username: str, search_term: str):
    """
    Return articles of a user where the title or content matches the search term.

    PARAMETERS
    ----------
        :username: String for the username of the user
        :search_term: String term given by the user when searching for a particular article
    
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

    PARAMETERS
    ----------
        :particle_id: Integer id of the particle assigned to the specific particle
    
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

    PARAMETERS
    ----------
        :username: String for the username of the user
        :password: String password for the username provided
        :particle_id: Integer id of the particle assigned to the specific particle
        :new_title: Optional string for updating the title of the particle 
        :new_content: Optional string for updating the content of the particle

    SIGNATURE
    ---------
        (str, str, str, str, str) -> bool
    """

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

def particle_views_count(particle_id):
    """
    This function increments and returns the number of times a particle has been viewed.

    PARAMETERS
    ----------
        :particle_id: Integer id of the particle assigned to the specific particle

    SIGNATURE
    ---------
        (int) -> int
    """
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(particles)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'views' not in columns:
        cursor.execute("ALTER TABLE particles ADD COLUMN views INTEGER DEFAULT 0")
        conn.commit()
    cursor.execute("UPDATE particles SET views = COALESCE(views, 0) + 1 WHERE article_id = ?", (particle_id,))
    conn.commit()
    cursor.execute("SELECT views FROM particles WHERE article_id = ?", (particle_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def create_article(username: str, title: str, content: str):
    """
    This function creates a new article for a user.

    PARAMETERS
    ----------
        :username: String for the username of the user
        :title: String title of the article
        :content: String content of the article

    SIGNATURE
    ---------
        (str, str, str) -> int or None
    """
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO particles (username, title, content) VALUES (?, ?, ?)", 
                      (username, title, content))
        conn.commit()
        article_id = cursor.lastrowid
        return article_id
    except Exception as e:
        print(f"Error creating article: {e}")
        return None
    finally:
        conn.close()


def particles_view_adder(particle_id):
    """
    This function adds a view to a particle.

    PARAMETERS
    ----------
        :particle_id: Integer id of the particle assigned to the specific particle

    SIGNATURE
    ---------
        (int) -> None
    """
    conn = sqlite3.connect('db/pim.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE particles SET views = COALESCE(views, 0) + 1 WHERE article_id = ?", (particle_id,))
    conn.commit()
    conn.close()