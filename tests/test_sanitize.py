import os
import pytest

from bot.utils.security import MessageSanitizer


@pytest.fixture(params=["0", "1"])
def sanitizer(request):
    os.environ["STRICT_PLAIN_TEXT"] = request.param
    return MessageSanitizer()


@pytest.mark.parametrize(
    "src, exp_contains",
    [
        ("Hello **World**", "Hello World"),
        ("Альфа — бета – гамма", "Альфа - бета - гамма"),
        ("Ссылка [тут]() текст", "Ссылка  текст"),
        ("Невидимые\u200bсимволы", "Невидимыесимволы"),
        ("Много\n\n\nстрок", "Много\n\nстрок"),
        ("Пробелы    тут", "Пробелы тут"),
    ],
)
def test_sanitize_cases(sanitizer, src, exp_contains):
    out = sanitizer.sanitize(src)
    assert exp_contains in out


from bot.utils.sanitize import sanitize_message


class TestSanitizeMessage:
    """Unit tests for message sanitization"""

    def test_remove_single_asterisks(self):
        """Remove single * but keep ** for bold"""
        input_text = "Hello *world* and **bold** text"
        expected = "Hello world and **bold** text"
        assert sanitize_message(input_text) == expected

    def test_remove_single_hashes(self):
        """Remove single # but keep ### headers"""
        input_text = "# Header\n## Subheader\n#notheader"
        expected = "Header\n## Subheader\nnotheader"
        assert sanitize_message(input_text) == expected

    def test_normalize_dashes(self):
        """Replace long dashes with regular dash"""
        input_text = "Range: 1–10 and — separator"
        expected = "Range: 1-10 and - separator"
        assert sanitize_message(input_text) == expected

    def test_collapse_whitespace(self):
        """Collapse multiple spaces and newlines"""
        input_text = "Text   with    spaces\n\n\n\nMultiple\n\nlines"
        expected = "Text with spaces\n\nMultiple\n\nlines"
        assert sanitize_message(input_text) == expected

    def test_preserve_links(self):
        """Keep markdown links and URLs intact"""
        input_text = "[Link text](https://example.com) and http://site.com"
        expected = "[Link text](https://example.com) and http://site.com"
        assert sanitize_message(input_text) == expected

    def test_remove_brackets_and_angles(self):
        """Remove bracketed and angled artifacts"""
        input_text = "Text [artifact] and <angle> content"
        expected = "Text  and  content"
        assert sanitize_message(input_text) == expected
