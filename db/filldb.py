import mysql.connector
import json

def create_table(cursor):
    """Создает таблицу для хранения данных из JSON."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            topic_id INT,
            title TEXT,
            publication_date VARCHAR(255),
            link TEXT,
            content TEXT,
            summarized_text TEXT,
            source VARCHAR(255)
        )
    """)
    print("Таблица создана.")

def drop_table(cursor):
    """Удаляет таблицу, если она существует."""
    cursor.execute("DROP TABLE IF EXISTS articles")
    print("Таблица удалена.")

def insert_data(cursor, data):
    """Заполняет таблицу данными из JSON."""
    query = """
        INSERT INTO articles (topic_id, title, publication_date, link, content, summarized_text, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    for article in data:
        cursor.execute(query, (
            article.get("topic_id"),
            article.get("title"),
            article.get("publication_date"),
            article.get("link"),
            article.get("content"),
            article.get("summarized_text"),
            article.get("source")
        ))
    print("Данные вставлены.")

def load_json_to_db(json_file, db_config):
    """Загружает данные из JSON-файла в базу данных."""
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        drop_table(cursor)
        create_table(cursor)
        insert_data(cursor, data)
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Ошибка при работе с MySQL: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        print("Соединение закрыто.")

def main():
    # Конфигурация подключения к базе данных
    db_config = {
        'host': 'localhost',  # Замените на адрес вашего сервера
        'user': 'admin',       # Ваш пользователь MySQL
        'password': 'admin',  # Ваш пароль MySQL
        'database': 'post_factory'  # Имя вашей базы данных
    }

    json_file = "merged_themes.json"  # Путь к JSON-файлу

    load_json_to_db(json_file, db_config)

if __name__ == "__main__":
    main()
