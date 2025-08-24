- Загружай каталог тремя файлами (см. файл: engine/catalog_loader.py). Ключи нормализуй. Режим: availability_mode=only_in_stock.
- Подбор опирается на 15/7 категорий, приоритет GP→GP-like→WB/Ozon (см. файл: engine/selector.py).
- При ничьей по сезону — выдай две палитры + 2 уточняющих вопроса.
- PDF → RU/Unicode, без URL в теле (см. файл: ui/pdf.py).

