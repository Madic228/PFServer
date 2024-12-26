import mysql.connector
from passlib.context import CryptContext
from db.database import get_db_connection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(email: str):
    connection = get_db_connection()
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

def create_user(email, password):
    hashed_password = get_password_hash(password)
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = "INSERT INTO users (email, password_hash) VALUES (%s, %s)"
        cursor.execute(query, (email, hashed_password))
        connection.commit()
        return True
    except mysql.connector.Error as error:
        print(error)
        return False
    finally:
        cursor.close()
        connection.close()