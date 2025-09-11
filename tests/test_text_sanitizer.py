"""
Тесты для TextSanitizer - очистки текста от спецсимволов
"""

import pytest
from services.text_sanitizer import TextSanitizer, sanitize_text, sanitize_message


class TestTextSanitizer:
    """Тесты для TextSanitizer"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.sanitizer = TextSanitizer()

    def test_sanitize_markdown(self):
        """Тест удаления markdown разметки"""
        text = "**Жирный** текст и *курсив* и ```код```"
        result = self.sanitizer.sanitize(text)
        assert result == "Жирный текст и курсив и код"

    def test_sanitize_quotes(self):
        """Тест нормализации кавычек"""
        text = '"Русские" и «кавычки»'
        result = self.sanitizer.sanitize(text)
        assert '"' not in result or result.count('"') == 0
        assert "«" not in result
        assert "»" not in result

    def test_sanitize_whitespace(self):
        """Тест нормализации пробелов"""
        text = "Текст  с    множественными   пробелами"
        result = self.sanitizer.sanitize(text)
        assert "  " not in result

    def test_sanitize_headers(self):
        """Тест удаления заголовков markdown"""
        text = "# Заголовок\n## Подзаголовок\nОбычный текст"
        result = self.sanitizer.sanitize(text)
        assert result == "Заголовок\nПодзаголовок\nОбычный текст"

    def test_sanitize_brackets(self):
        """Тест удаления скобок и стрелочек"""
        text = "Текст > с [разными] (скобками)"
        result = self.sanitizer.sanitize(text)
        assert ">" not in result
        assert "[" not in result
        assert "]" not in result
        assert "(" not in result
        assert ")" not in result

    def test_sanitize_message_mode(self):
        """Тест мягкой очистки для сообщений"""
        text = "**Жирный** текст с ```кодом``` и > цитатой"
        result = self.sanitizer.sanitize_message(text)
        assert result == "Жирный текст с кодом и  цитатой"

    def test_normalize_spacing(self):
        """Тест нормализации отступов"""
        text = "Текст\tс\tтабами\n\n\nИ переносами строк"
        result = self.sanitizer.normalize_spacing(text)
        assert "\t" not in result
        assert "\n\n\n" not in result


class TestSanitizeFunctions:
    """Тесты для удобных функций"""

    def test_sanitize_text_function(self):
        """Тест глобальной функции sanitize_text"""
        result = sanitize_text("**Тест** текста")
        assert result == "Тест текста"

    def test_sanitize_message_function(self):
        """Тест глобальной функции sanitize_message"""
        result = sanitize_message("*Тест* сообщения")
        assert result == "Тест сообщения"


if __name__ == "__main__":
    pytest.main([__file__])
