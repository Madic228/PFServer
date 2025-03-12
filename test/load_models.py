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
