import mysql.connector
from passlib.context import CryptContext
from db.database import get_db_connection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Хеширует пароль."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Проверяет пароль."""
    return pwd_context.verify(plain_password, password_hash)

def get_user_by_email(email: str):
    """Получает пользователя из базы данных по email."""
    connection = get_db_connection()
    if not connection:
        print("Database connection failed.")
        return None

    cursor = connection.cursor(dictionary=True)
    try:
        query = "SELECT * FROM users WHERE email = %s OR username = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        if result:
            return {
                "id": result['id'],
                "email": result['email'],
                "password_hash": result['password_hash']
            }
        else:
            return None
    finally:
        cursor.close()
        connection.close()

def create_user(email: str, password: str, username: str) -> bool:
    """Создаёт нового пользователя в базе данных."""
    hashed_password = get_password_hash(password)
    connection = get_db_connection()
    if not connection:
        print("Database connection failed.")
        return False

    cursor = connection.cursor()
    try:
        # Добавлен параметр username
        query = "INSERT INTO users (email, password_hash, username) VALUES (%s, %s, %s)"
        cursor.execute(query, (email, hashed_password, username))
        connection.commit()
        return True
    except mysql.connector.Error as error:
        print(f"Database error: {error}")
        return False
    finally:
        cursor.close()
        connection.close()


def create_user_in_db(email: str, password: str, username: str) -> bool:
    """Создаёт нового пользователя в базе данных."""
    password_hash = get_password_hash(password)
    connection = get_db_connection()
    if not connection:
        print("Database connection failed.")
        return False

    cursor = connection.cursor()
    try:
        query = "INSERT INTO users (email, password_hash, username) VALUES (%s, %s, %s)"
        cursor.execute(query, (email, password_hash, username))
        connection.commit()
        return True
    except mysql.connector.Error as error:
        print(f"Database error: {error}")
        return False
    finally:
        cursor.close()
        connection.close()
