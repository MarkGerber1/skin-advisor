import io
from fpdf import FPDF
from app.infra.settings import get_settings


class PDFReport(FPDF):
    """Класс для создания PDF отчета с кастомным хэдером и футером."""

    def header(self):
        self.set_font('DejaVu', 'B', 15)
        self.cell(0, 10, 'Персональные рекомендации по уходу', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 8)
        settings = get_settings()
        self.cell(0, 10, f'Сформировано ботом {settings.app.bot_name}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('DejaVu', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('DejaVu', '', 10)
        self.multi_cell(0, 5, body)
        self.ln()

    def product_info(self, name, description, links_html):
        self.set_font('DejaVu', 'B', 11)
        self.multi_cell(0, 5, name)
        self.set_font('DejaVu', '', 10)
        self.multi_cell(0, 5, description)

        # FPDF не поддерживает HTML, поэтому просто выводим текст ссылок
        import re
        clean_links = re.sub('<[^<]+?>', '', links_html.replace(' | ', '\n'))
        self.set_font('DejaVu', 'I', 9)
        self.multi_cell(0, 5, f"Ссылки для покупки:\n{clean_links}")
        self.ln(5)


def create_pdf_report(diagnosis_data: dict, recommendations_data: dict) -> bytes:
    """
    Создает PDF-отчет в виде байтовой строки.
    """
    pdf = PDFReport()
    # Добавляем кириллический шрифт. Убедитесь, что файл шрифта доступен.
    try:
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    except RuntimeError:
        # Фоллбэк, если шрифт не найден (будут проблемы с кириллицей)
        pdf.add_font('Arial', '', 'Arial.ttf', uni=True)
        pdf.set_font('Arial', '', 12)

    pdf.set_font('DejaVu', '', 12)
    pdf.add_page()

    # Раздел диагностики
    pdf.chapter_title('✅ Результаты вашей диагностики')
    diag_body = (
        f"Тип кожи: {diagnosis_data.get('skin_type', 'не определен')}\n"
        f"Подтон: {diagnosis_data.get('undertone', 'не определен')}\n"
        f"Состояния: {', '.join(diagnosis_data.get('states', []))}\n\n"
        f"Обоснование:\n"
    )
    for reason in diagnosis_data.get('reasoning', []):
        diag_body += f"- {reason}\n"
    pdf.chapter_body(diag_body)

    # Раздел рекомендаций
    for routine_key, routine_name in [('am', '☀️ Утренний уход (AM)'), ('pm', '🌙 Вечерний уход (PM)'), ('weekly', '✨ Еженедельный уход'), ('makeup', '💄 Макияж')]:
        if routine := recommendations_data.get(routine_key):
            pdf.chapter_title(routine_name)
            for i, step in enumerate(routine):
                product = step['product']
                description = f"{i+1}. {product['purpose'].capitalize()}\nКак использовать: {step['how_to_use']}"
                # Ссылки в PDF пока не делаем кликабельными для простоты
                pdf.product_info(product['name'], description, "Ссылки доступны в боте.")

    # Предосторожности
    if warnings := recommendations_data.get('warnings'):
        pdf.chapter_title('⚠️ Предосторожности')
        pdf.chapter_body("\n".join(f"- {w}" for w in warnings))

    # Дисклеймер
    settings = get_settings()
    pdf.chapter_title('Дисклеймер')
    pdf.chapter_body(settings.app.disclaimer)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return pdf_bytes



