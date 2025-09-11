"""
Сервис для очистки текста от спецсимволов и форматирования
Удаляет markdown, нормализует кавычки, пробелы и переводы строк
"""

import re


class TextSanitizer:
    """Класс для очистки и нормализации текста"""

    def __init__(self):
        # Регулярные выражения для очистки
        self.markdown_patterns = [
            (r"\*\*\*(.*?)\*\*\*", r"\1"),  # ***bold italic***
            (r"\*\*(.*?)\*\*", r"\1"),  # **bold**
            (r"\*(.*?)\*", r"\1"),  # *italic*
            (r"```(.*?)```", r"\1"),  # ```code blocks```
            (r"`(.*?)`", r"\1"),  # `inline code`
            (r"#+\s+", ""),  # Headers # ##
            (r"^\s*[-*+]\s+", "• "),  # List markers to bullets
            (r"^\s*\d+\.\s+", "• "),  # Numbered lists to bullets
        ]

        # Нормализация кавычек
        self.quote_patterns = [
            (r'["""]', '"'),  # Нормализовать двойные кавычки
            (r"[" "]", "'"),  # Нормализовать одинарные кавычки
        ]

        # Очистка лишних символов
        self.cleanup_patterns = [
            (r"\n{3,}", "\n\n"),  # Не более 2 переводов строки
            (r"\s{2,}", " "),  # Не более 1 пробела подряд
            (r"[>»]", ""),  # Удалить стрелки цитат
            (r"\[\]", ""),  # Удалить пустые скобки
            (r"\(\)", ""),  # Удалить пустые скобки
        ]

        # Компилируем паттерны для производительности
        self._compiled_markdown = [
            (re.compile(p, re.MULTILINE), r) for p, r in self.markdown_patterns
        ]
        self._compiled_quotes = [(re.compile(p), r) for p, r in self.quote_patterns]
        self._compiled_cleanup = [(re.compile(p), r) for p, r in self.cleanup_patterns]

    def sanitize(self, text: str) -> str:
        """
        Полная очистка текста от спецсимволов и форматирования

        Args:
            text: Исходный текст

        Returns:
            Очищенный текст
        """
        if not text:
            return ""

        # Удаляем markdown
        for pattern, replacement in self._compiled_markdown:
            text = pattern.sub(replacement, text)

        # Нормализуем кавычки
        for pattern, replacement in self._compiled_quotes:
            text = pattern.sub(replacement, text)

        # Очищаем лишние символы
        for pattern, replacement in self._compiled_cleanup:
            text = pattern.sub(replacement, text)

        # Финальная очистка
        text = text.strip()

        return text

    def sanitize_message(self, text: str) -> str:
        """
        Специальная очистка для сообщений бота
        Более мягкая, сохраняет полезное форматирование

        Args:
            text: Исходный текст

        Returns:
            Очищенное сообщение
        """
        if not text:
            return ""

        # Удаляем только проблемные символы
        text = re.sub(r"\*\*\*|\*\*|\*|```|`|#+\s+", "", text)  # Markdown
        text = re.sub(r"[>»\[\]\(\)]", "", text)  # Скобки и стрелки
        text = re.sub(r"\n{3,}", "\n\n", text)  # Переводы строк
        text = re.sub(r"\s{2,}", " ", text)  # Пробелы

        return text.strip()

    def normalize_spacing(self, text: str) -> str:
        """
        Нормализует пробелы и отступы

        Args:
            text: Исходный текст

        Returns:
            Текст с нормализованными пробелами
        """
        # Заменяем табы на пробелы
        text = text.expandtabs(4)

        # Нормализуем пробелы
        text = re.sub(r"\s+", " ", text)

        # Восстанавливаем переводы строк после пунктуации
        text = re.sub(r"([.!?])\s*([А-ЯA-Z])", r"\1\n\2", text)

        return text.strip()


# Глобальный экземпляр
_sanitizer = None


def get_text_sanitizer() -> TextSanitizer:
    """Получить глобальный экземпляр TextSanitizer"""
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = TextSanitizer()
    return _sanitizer


def sanitize_text(text: str) -> str:
    """Удобная функция для быстрой очистки текста"""
    return get_text_sanitizer().sanitize(text)


def sanitize_message(text: str) -> str:
    """Удобная функция для очистки сообщений бота"""
    return get_text_sanitizer().sanitize_message(text)


# Декоратор для автоматической очистки ответов
def sanitized_response(func):
    """
    Декоратор для автоматической очистки текста в ответах бота

    Использование:
    @sanitized_response
    async def my_handler(message: Message):
        return "Текст с **markdown** и лишними символами"
    """

    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        if isinstance(result, str):
            return sanitize_message(result)
        return result

    return wrapper
