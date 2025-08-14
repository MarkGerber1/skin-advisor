from app.ui.keyboard import build_main_menu


def test_main_menu_structure():
    kb = build_main_menu()
    assert kb.resize_keyboard is True
    flat = [btn.text for row in kb.keyboard for btn in row]
    assert "🧪 Пройти анкету" in flat and "📄 Мои рекомендации" in flat

