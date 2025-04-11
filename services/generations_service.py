from db.database import get_db_connection
from datetime import datetime
from typing import List, Dict, Any, Optional

def get_user_generations(user_id: int) -> List[Dict[str, Any]]:
    """
    Получение всех генераций пользователя
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT * FROM user_generations WHERE user_id = %s ORDER BY generation_date DESC",
            (user_id,)
        )
        generations = cursor.fetchall()
        return generations
    except Exception as e:
        print(f"Error retrieving generations: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def create_generation(user_id: int, title: str, content: str) -> Optional[Dict[str, Any]]:
    """
    Создание новой генерации
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "INSERT INTO user_generations (user_id, title, content) VALUES (%s, %s, %s)",
            (user_id, title, content)
        )
        conn.commit()
        
        generation_id = cursor.lastrowid
        cursor.execute("SELECT * FROM user_generations WHERE id = %s", (generation_id,))
        return cursor.fetchone()
    except Exception as e:
        conn.rollback()
        print(f"Error creating generation: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_generation_by_id(generation_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Получение генерации по ID
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT * FROM user_generations WHERE id = %s AND user_id = %s",
            (generation_id, user_id)
        )
        return cursor.fetchone()
    except Exception as e:
        print(f"Error retrieving generation: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_generation_publish_status(generation_id: int, user_id: int, published: bool, 
                                     publication_platform: Optional[str] = None, 
                                     social_network_url: Optional[str] = None) -> bool:
    """
    Обновление статуса публикации генерации
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        publication_date = datetime.now() if published else None
        
        cursor.execute(
            """
            UPDATE user_generations 
            SET published = %s, 
                publication_platform = %s,
                publication_date = %s,
                social_network_url = %s
            WHERE id = %s AND user_id = %s
            """,
            (published, publication_platform, publication_date, social_network_url, generation_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error updating generation publish status: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def delete_generation(generation_id: int, user_id: int) -> bool:
    """
    Удаление генерации
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM user_generations WHERE id = %s AND user_id = %s",
            (generation_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error deleting generation: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def update_generation(generation_id: int, user_id: int, title: str, content: str) -> bool:
    """
    Обновление генерации
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            UPDATE user_generations 
            SET title = %s, content = %s
            WHERE id = %s AND user_id = %s
            """,
            (title, content, generation_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error updating generation: {e}")
        return False
    finally:
        cursor.close()
        conn.close() 