import re


def sanitize_message(text: str) -> str:
    """
    Очищает текст от спецсимволов и артефактов ИИ,
    сохраняя Markdown и ссылки.
    """
    if not text:
        return text

    # Удаляем звездочки и решетки (если не в ссылках)
    # Но сохраняем Markdown: **bold**, ## headers
    text = re.sub(r"(?<!\*)\*(?!\*)", "", text)  # Удаляем одиночные *
    text = re.sub(r"(?<!#)#(?![#])", "", text)  # Удаляем # не перед другим #

    # Заменяем длинные тире на обычное
    text = text.replace("—", "-").replace("–", "-")

    # Схлопываем множественные пробелы и переносы
    text = re.sub(r"\n{3,}", "\n\n", text)  # Не более 2 переносов
    text = re.sub(r" {2,}", " ", text)  # Не более 1 пробела

    # Удаляем пустые строки в начале/конце
    text = text.strip()

    # Удаляем артефакты ИИ (примеры)
    text = re.sub(r"<[^>]+>", "", text)  # Удаляем <text>
    text = re.sub(r"\[([^\]]+)\](?!\()", "", text)  # Удаляем [text] не перед (

    return text
