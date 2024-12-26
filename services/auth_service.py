import mysql.connector
from passlib.context import CryptContext
from db.database import get_db_connection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Хеширует пароль."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(email: str):
    """Получает пользователя из базы данных по email."""
    connection = get_db_connection()
    if not connection:
        print("Database connection failed.")
        return None

    cursor = connection.cursor(dictionary=True)
    try:
        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        if result:
            return {
                "id": result['id'],
                "email": result['email'],
                "hashed_password": result['hashed_password']
            }
        else:
            return None
    finally:
        cursor.close()
        connection.close()

def create_user(email: str, password: str) -> bool:
    """Создаёт нового пользователя в базе данных."""
    hashed_password = get_password_hash(password)
    connection = get_db_connection()
    if not connection:
        print("Database connection failed.")
        return False

    cursor = connection.cursor()
    try:
        # Проверка на существование пользователя
        existing_user = get_user_by_email(email)
        if existing_user:
            print("User already exists.")
            return False

        query = "INSERT INTO users (email, hashed_password) VALUES (%s, %s)"
        cursor.execute(query, (email, hashed_password))
        connection.commit()
        return True
    except mysql.connector.Error as error:
        print(f"Database error: {error}")
        return False
    finally:
        cursor.close()
        connection.close()

def create_user_in_db(email: str, password: str) -> bool:
    """Создаёт нового пользователя в базе данных."""
    hashed_password = get_password_hash(password)
    connection = get_db_connection()
    if not connection:
        print("Database connection failed.")
        return False

    cursor = connection.cursor()
    try:
        query = "INSERT INTO users (email, hashed_password) VALUES (%s, %s)"
        cursor.execute(query, (email, hashed_password))
        connection.commit()
        return True
    except mysql.connector.Error as error:
        print(f"Database error: {error}")
        return False
    finally:
        cursor.close()
        connection.close()
