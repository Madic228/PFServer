import mysql.connector
from mysql.connector import connection

def get_db_connection():
    """
    Устанавливает соединение с базой данных MySQL.
    """
    return mysql.connector.connect(
        host="localhost",
        user="admin",
        password="madicpas123",
        database="post_factory"
    )
