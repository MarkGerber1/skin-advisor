from bot.ui.report_builder import (
    build_palette_report,
    build_skincare_report,
    render_report_telegram,
    render_report_pdf,
)


def test_build_and_render_palette():
    blocks = build_palette_report({"season": "spring", "undertone": "warm"}, {"products": []})
    text, kb = render_report_telegram(blocks)
    assert "Отчёт по цветотипу" in text
    assert any("Что купить" in line for line in text.splitlines())
    snap = render_report_pdf(blocks)
    assert "result" in snap


def test_build_and_render_skincare():
    blocks = build_skincare_report({"skin_type": "oily"}, {"products": []})
    text, kb = render_report_telegram(blocks)
    assert "Отчёт по уходу" in text
    assert any("Рекомендации" in line for line in text.splitlines())
    snap = render_report_pdf(blocks)
    assert "profile" in snap


