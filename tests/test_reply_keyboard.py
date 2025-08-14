from app.ui.keyboard import build_main_menu


def test_reply_keyboard_layout():
    kb = build_main_menu()
    assert hasattr(kb, "keyboard") and len(kb.keyboard) >= 2
    flat = [btn.text for row in kb.keyboard for btn in row]
    assert "🧪 Пройти анкету" in flat

