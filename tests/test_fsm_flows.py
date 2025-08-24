from __future__ import annotations

from bot.handlers.flow_skincare import _parse as skin_parse, _kb_skin_types, _kb_concerns, _kb_confirm
from bot.handlers.flow_palette import _parse as pal_parse, _kb_undertone, _kb_value


def test_skin_parse_pattern():
    prefix, step, field, value = skin_parse("skin:1:type:dry")
    assert prefix == "skin"
    assert step == "1"
    assert field == "type"
    assert value == "dry"


def test_palette_parse_pattern():
    prefix, step, field, value = pal_parse("pal:1:undertone:cool")
    assert prefix == "pal"
    assert step == "1"
    assert field == "undertone"
    assert value == "cool"


def test_skin_kb_types_structure():
    kb = _kb_skin_types()
    datas = [b.callback_data for row in kb.inline_keyboard for b in row]
    assert "skin:1:type:dry" in datas
    assert "skin:1:type:oily" in datas
    assert "skin:1:type:combo" in datas
    assert "skin:1:type:sensitive" in datas
    assert "skin:1:type:normal" in datas


def test_skin_kb_concerns_toggle_and_next():
    kb = _kb_concerns(selected=["acne"])  # acne marked
    datas = [b.callback_data for row in kb.inline_keyboard for b in row]
    assert "skin:2:concern:acne" in datas
    assert "skin:2:next:go" in datas


def test_skin_kb_confirm_enabled_and_disabled():
    kb_disabled = _kb_confirm(False)
    data_disabled = [b.callback_data for row in kb_disabled.inline_keyboard for b in row]
    assert "skin:3:confirm:disabled" in data_disabled
    kb_enabled = _kb_confirm(True)
    data_enabled = [b.callback_data for row in kb_enabled.inline_keyboard for b in row]
    assert "skin:3:confirm:ok" in data_enabled


def test_palette_kb_undertone_and_value():
    u = _kb_undertone()
    datas_u = [b.callback_data for row in u.inline_keyboard for b in row]
    assert "pal:1:undertone:cool" in datas_u
    v = _kb_value()
    datas_v = [b.callback_data for row in v.inline_keyboard for b in row]
    assert "pal:2:value:light" in datas_v
    assert "pal:2:value:medium" in datas_v
    assert "pal:2:value:deep" in datas_v








