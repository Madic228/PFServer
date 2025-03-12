# services/summarizer_service.py
from transformers import AutoTokenizer, T5ForConditionalGeneration
from db.database import get_db_connection

class SummarizerDB:
    def __init__(self, topic_id):
        self.topic_id = topic_id
        self.tokenizer, self.model = self.init_summarization_model()

    def init_summarization_model(self):
        """Инициализация модели суммаризации."""
        model_name = "IlyaGusev/rut5_base_sum_gazeta"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = T5ForConditionalGeneration.from_pretrained(model_name)
        return tokenizer, model

    def summarize_text(self, text: str) -> str:
        """Суммаризирует текст."""
        input_ids = self.tokenizer(
            [text],
            max_length=600,
            add_special_tokens=True,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )["input_ids"]

        output_ids = self.model.generate(input_ids=input_ids, no_repeat_ngram_size=4)[0]
        return self.tokenizer.decode(output_ids, skip_special_tokens=True)

    def run(self):
        """Запускает суммаризацию для статей с указанным topic_id."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Получаем статьи без суммаризации
            query = """
                SELECT id, content
                FROM articles
                WHERE topic_id = %s AND (summarized_text IS NULL OR summarized_text = '')
            """
            cursor.execute(query, (self.topic_id,))
            articles = cursor.fetchall()

            for article in articles:
                summarized_text = self.summarize_text(article["content"])
                update_query = """
                    UPDATE articles
                    SET summarized_text = %s
                    WHERE id = %s
                """
                cursor.execute(update_query, (summarized_text, article["id"]))

            conn.commit()
            print(f"✅ Суммаризация для topic_id={self.topic_id} завершена.")
        finally:
            cursor.close()
            conn.close()