from __future__ import annotations

from bot.ui.render import render_skincare_report, render_makeup_report


def test_render_skincare_min():
    text, kb = render_skincare_report({"skincare": {"AM": [], "PM": [], "weekly": []}})
    assert "Персональный уход" in text
    assert kb is not None


def test_render_makeup_min():
    text, kb = render_makeup_report({"makeup": {"face": [], "brows": [], "eyes": [], "lips": []}})
    assert "Макияж" in text
    assert kb is not None


