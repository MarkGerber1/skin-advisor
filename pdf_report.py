from pathlib import Path
from typing import Dict, Any
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _register_font() -> str:
    """Register a Unicode TTF font if available. Returns font name to use."""
    font_name = "Arial"
    # Common Windows font path
    win_font = os.path.join(
        os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf"
    )
    if os.path.exists(win_font):
        try:
            pdfmetrics.registerFont(TTFont(font_name, win_font))
            return font_name
        except Exception:
            pass
    # Fallback to built-in Helvetica (may not display Cyrillic, but will not crash)
    return "Helvetica"


async def build_pdf(
    user_profile: Dict[str, Any], rec: Dict[str, Any], out_path: str
) -> str:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    font = _register_font()
    c = canvas.Canvas(str(p), pagesize=A4)
    width, height = A4

    c.setFont(font, 14)
    c.drawString(40, height - 60, "Персональный план ухода")

    c.setFont(font, 11)
    skin_type = str(user_profile.get("skin_type", ""))
    concerns = user_profile.get("concerns") or []
    concerns_text = (
        ", ".join(map(str, concerns))
        if isinstance(concerns, (list, tuple))
        else str(concerns)
    )
    text = c.beginText(40, height - 90)
    text.textLine(f"Тип кожи: {skin_type}")
    text.textLine(f"Проблемы: {concerns_text}")
    c.drawText(text)

    def section(title: str, y: int) -> int:
        c.setFont(font, 12)
        c.drawString(40, y, title)
        return y - 16

    y = height - 130
    y = section("AM", y)
    c.setFont(font, 10)
    for pid in rec.get("routines", {}).get("am", []):
        prod = next((p for p in rec.get("products", []) if p.get("id") == pid), None)
        if prod:
            c.drawString(
                50,
                y,
                f"- {prod.get('name','')} ({prod.get('brand','')}) — {prod.get('usage','')}",
            )
            y -= 14

    y = section("PM", y)
    c.setFont(font, 10)
    for pid in rec.get("routines", {}).get("pm", []):
        prod = next((p for p in rec.get("products", []) if p.get("id") == pid), None)
        if prod:
            c.drawString(
                50,
                y,
                f"- {prod.get('name','')} ({prod.get('brand','')}) — {prod.get('usage','')}",
            )
            y -= 14

    y = section("Weekly", y)
    c.setFont(font, 10)
    for pid in rec.get("routines", {}).get("weekly", []):
        prod = next((p for p in rec.get("products", []) if p.get("id") == pid), None)
        if prod:
            c.drawString(
                50,
                y,
                f"- {prod.get('name','')} ({prod.get('brand','')}) — {prod.get('usage','')}",
            )
            y -= 14

    c.showPage()
    c.save()
    return str(p)
