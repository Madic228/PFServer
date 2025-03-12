from transformers import AutoTokenizer, T5ForConditionalGeneration

# Список всех моделей
model_names = [
    "IlyaGusev/rut5_base_sum_gazeta",  # Модель для суммаризации
    # добавьте сюда другие модели, если нужно
]

# Загрузка моделей
tokenizers = {}
models = {}

for model_name in model_names:
    tokenizers[model_name] = AutoTokenizer.from_pretrained(model_name)
    models[model_name] = T5ForConditionalGeneration.from_pretrained(model_name)

print("Модели загружены!")


# Функция для суммаризации текста
def summarize_long_text(text: str, model_name: str):
    tokenizer = tokenizers[model_name]
    model = models[model_name]

    # Разбиваем текст на части, если он слишком длинный
    max_input_length = 512  # Максимальная длина входа для модели (это зависит от модели, может быть меньше)
    tokenized_text = tokenizer(text, return_tensors="pt", truncation=False)
    input_ids = tokenized_text["input_ids"]

    # Если длина текста больше максимума, делим на части
    if len(input_ids[0]) > max_input_length:
        # Разделение текста на части
        num_parts = len(input_ids[0]) // max_input_length + 1
        summaries = []
        for i in range(num_parts):
            # Разделяем на части
            part_ids = input_ids[0][i * max_input_length: (i + 1) * max_input_length]
            summary_ids = model.generate(part_ids.unsqueeze(0), no_repeat_ngram_size=4)[0]
            summary = tokenizer.decode(summary_ids, skip_special_tokens=True)
            summaries.append(summary)
        return " ".join(summaries)

    # Если текст не слишком длинный, суммаризируем его целиком
    summary_ids = model.generate(input_ids, no_repeat_ngram_size=4)[0]
    summary = tokenizer.decode(summary_ids, skip_special_tokens=True)
    return summary


# Пример использования
long_text = """МОСКВА, 27 фев - РИА Новости. Минтранс РФ предлагает внести изменения в законодательство, предусмотрев индексацию на уровень фактической инфляции цены госконтрактов на строительство инфраструктурных объектов, сообщил первый замминистра транспорта РФ Валентин Иванов.
По его словам, одним из крайне важных моментов для всех строителей и инвесторов является справедливое определение цены себестоимости строительства.
Многие инфраструктурные проекты, отметил он, реализуются 3-5 лет, и, фиксируя цену контракта в таком долгом периоде, где-то может получиться "разрыв", например сдвиг сроков.
Позже, отвечая на вопрос РИА Новости, он уточнил, что предложение должно коснуться новых государственных контрактов, которые будут заключаться. "Это требует внесения изменений в 44-й Федеральный закон (закон о контрактной системе в сфере госзакупок - ред.). Мы такую инициативу прорабатываем с остальными ФОИВами, с Минстроем, в том числе, с Минэкономразвития", - сообщил первый замминистра.
Другие детали он не уточнил. "Если в федеральный закон будут поддержаны изменения, там будет определено, на какие контракты… При проработке закона определим, какие именно. Прежде всего, это длинные, крупные, капиталоемкие проекты, которые с длинным сроком реализации", - ответил Иванов."""

summarized_text = summarize_long_text(long_text, "IlyaGusev/rut5_base_sum_gazeta")
print(summarized_text)
