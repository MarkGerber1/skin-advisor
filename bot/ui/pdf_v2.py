"""
📄 PDF v2 Report Generator - Профессиональные отчеты с правильной структурой
Структура: Резюме → 15 декор (оттенок/почему/как) → 7 уход → сводная таблица
"""

import os
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from fpdf import FPDF
import re

class StructuredPDFGenerator:
    """Генератор структурированных PDF отчетов v2"""
    
    def __init__(self):
        # Настройки PDF
        self.font_size_title = 18
        self.font_size_section = 14
        self.font_size_text = 11
        self.font_size_small = 9
        
        # Цвета (RGB)
        self.color_header = (41, 128, 185)      # Синий
        self.color_section = (52, 73, 94)      # Темно-серый 
        self.color_text = (44, 62, 80)         # Черный
        self.color_accent = (231, 76, 60)      # Красный для акцентов
        
        # Отступы (уменьшены для предотвращения проблем с пространством)
        self.margin_left = 15
        self.margin_top = 15
        self.margin_right = 15
        
        # Emoji mapping для PDF
        self.emoji_map = {
            '🎨': '[ПАЛИТРА]', '🧴': '[УХОД]', '✨': '*', '🌸': '[ВЕСНА]',
            '🌊': '[ЛЕТО]', '🍂': '[ОСЕНЬ]', '❄️': '[ЗИМА]', '💄': '[МАКИЯЖ]',
            '👁️': '[ГЛАЗА]', '💡': '!', '🏠': '[МЕНЮ]', '📄': '[ОТЧЕТ]',
            '🛍️': '[ТОВАРЫ]', '🔥': '*', '⚠️': '!', '❌': 'X', '✅': 'OK',
            '💰': '[ЦЕНА]', '🎯': '[ЦЕЛЬ]', '📊': '[ДАННЫЕ]', '🔗': '[ССЫЛКА]'
        }
    
    def _setup_pdf(self) -> FPDF:
        """Настройка PDF документа"""
        pdf = FPDF(unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(self.margin_left, self.margin_top, self.margin_right)
        
        # Настройка шрифта
        try:
            # Попытка загрузить DejaVu шрифт
            font_paths = [
                ".skin-advisor/assets/DejaVuSans.ttf",
                "assets/fonts/DejaVuSans.ttf",
                os.path.join(os.path.dirname(__file__), "..", "..", ".skin-advisor", "assets", "DejaVuSans.ttf"),
            ]
            
            font_found = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdf.add_font("DejaVu", "", font_path)
                    pdf.add_font("DejaVu", "B", font_path)  # Bold variant
                    font_found = True
                    print(f"✅ PDF v2: Using DejaVu font from: {font_path}")
                    break
            
            if not font_found:
                print("⚠️ PDF v2: DejaVu font not found, using Arial")
                pdf.set_font("Arial", size=self.font_size_text)
            else:
                pdf.set_font("DejaVu", size=self.font_size_text)
                
        except Exception as e:
            print(f"⚠️ PDF v2: Font setup error: {e}, using Arial")
            pdf.set_font("Arial", size=self.font_size_text)
        
        return pdf
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста для PDF"""
        if not text:
            return ""
        
        # Удаляем markdown
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold** -> bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic* -> italic
        
        # Заменяем emoji
        for emoji, replacement in self.emoji_map.items():
            text = text.replace(emoji, replacement)
        
        # Удаляем оставшиеся unicode символы
        text = re.sub(r'[^\x00-\x7F\u0400-\u04FF]+', '', text)
        
        return text.strip()
    
    def _add_header(self, pdf: FPDF, title: str):
        """Добавляет заголовок отчета"""
        pdf.set_font_size(self.font_size_title)
        pdf.set_text_color(*self.color_header)
        
        clean_title = self._clean_text(title)
        pdf.cell(0, 12, clean_title, align='C')
        pdf.ln()
        pdf.ln(5)
        
        # Линия под заголовком
        pdf.set_draw_color(*self.color_header)
        pdf.line(self.margin_left, pdf.get_y(), 210 - self.margin_right, pdf.get_y())
        pdf.ln(8)
    
    def _add_section_header(self, pdf: FPDF, section_title: str):
        """Добавляет заголовок секции"""
        # Проверяем не нужна ли новая страница
        if pdf.get_y() > 250:
            pdf.add_page()
        
        pdf.set_font_size(self.font_size_section)
        pdf.set_text_color(*self.color_section)
        
        clean_title = self._clean_text(section_title)
        pdf.cell(0, 8, clean_title)
        pdf.ln()
        pdf.ln(3)
    
    def _add_text_block(self, pdf: FPDF, text: str, indent: int = 0):
        """Добавляет блок текста с переносами"""
        if not text:
            return
        
        pdf.set_font_size(self.font_size_text)
        pdf.set_text_color(*self.color_text)
        
        clean_text = self._clean_text(text)
        
        # Разбиваем на абзацы
        paragraphs = clean_text.split('\n')
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Проверяем не нужна ли новая страница
                if pdf.get_y() > 250:
                    pdf.add_page()
                
                # Отступ для подпунктов
                if indent > 0:
                    pdf.set_x(self.margin_left + indent)
                
                # Многострочный текст с переносами
                pdf.multi_cell(0, 5, paragraph.strip())
                pdf.ln(2)
    
    def _add_product_card(self, pdf: FPDF, product: Dict[str, Any], category: str):
        """Добавляет карточку продукта"""
        if pdf.get_y() > 240:
            pdf.add_page()
        
        # Заголовок продукта
        pdf.set_font_size(self.font_size_text)
        pdf.set_text_color(*self.color_accent)
        
        product_name = self._clean_text(product.get('name', 'Продукт'))
        brand = self._clean_text(product.get('brand', ''))
        
        title = f"{brand} - {product_name}" if brand else product_name
        pdf.cell(0, 6, title, ln=True)
        
        # Информация о продукте
        pdf.set_font_size(self.font_size_small)
        pdf.set_text_color(*self.color_text)
        
        # Цена
        price = product.get('price')
        currency = product.get('price_currency', 'RUB')
        if price:
            pdf.cell(0, 4, f"Цена: {price} {currency}", ln=True)
        
        # Объяснение почему подходит
        explain = product.get('explain', '')
        if explain:
            explain_text = f"Почему подходит: {self._clean_text(explain)}"
            pdf.multi_cell(0, 4, explain_text)
        
        # Как использовать (для макияжа)
        if category in ['foundation', 'concealer', 'powder', 'blush', 'bronzer', 'highlighter']:
            usage_tips = self._get_usage_tips(category)
            if usage_tips:
                pdf.set_font_size(self.font_size_small - 1)
                pdf.multi_cell(0, 4, f"Как наносить: {usage_tips}")
        
        # Статус в наличии
        in_stock = product.get('in_stock', False)
        status_text = "В наличии" if in_stock else "Нет в наличии"
        pdf.set_text_color(*self.color_accent if not in_stock else (46, 125, 50))
        pdf.cell(0, 4, f"Статус: {status_text}", ln=True)
        
        pdf.ln(3)
    
    def _get_usage_tips(self, category: str) -> str:
        """Получает советы по нанесению для категории"""
        tips = {
            'foundation': 'наносите от центра лица к краям, растушевывая спонжем',
            'concealer': 'точечно на проблемные зоны, растушуйте пальцами',
            'powder': 'закрепите тональную основу пушистой кистью',
            'blush': 'на яблочки щек, растушуйте к вискам',
            'bronzer': 'на выступающие части лица (лоб, нос, скулы)',
            'highlighter': 'на скулы, спинку носа, под бровь',
            'eyeshadow': 'начните со светлых оттенков, темные - в складку века',
            'eyeliner': 'проведите линию близко к ресницам',
            'mascara': 'прокрашивайте от корней к кончикам зигзагообразными движениями',
            'lipstick': 'используйте карандаш для контура, затем помаду'
        }
        return tips.get(category, '')
    
    def _add_summary_table(self, pdf: FPDF, profile: Dict[str, Any], products_summary: Dict[str, int]):
        """Добавляет сводную таблицу рекомендаций"""
        self._add_section_header(pdf, "СВОДНАЯ ТАБЛИЦА РЕКОМЕНДАЦИЙ")
        
        # Информация о пользователе
        pdf.set_font_size(self.font_size_text)
        pdf.set_text_color(*self.color_text)
        
        summary_data = [
            ("Подтон кожи", profile.get('undertone', 'Не определен')),
            ("Сезон", profile.get('season', 'Не определен')),
            ("Контрастность", profile.get('contrast', 'Не определена')),
            ("Тип кожи", profile.get('skin_type', 'Не определен')),
        ]
        
        if profile.get('concerns'):
            concerns = ', '.join(profile.get('concerns', []))
            summary_data.append(("Проблемы кожи", concerns))
        
        # Таблица характеристик
        for label, value in summary_data:
            pdf.cell(60, 6, f"{label}:", border=1)
            pdf.cell(0, 6, self._clean_text(str(value)), border=1)
            pdf.ln()
        
        pdf.ln(5)
        
        # Статистика по продуктам
        if products_summary:
            pdf.cell(0, 6, "СТАТИСТИКА РЕКОМЕНДАЦИЙ:")
            pdf.ln()
            pdf.ln(2)
            
            for category, count in products_summary.items():
                pdf.cell(80, 5, f"{category.title()}:", border=1)
                pdf.cell(0, 5, f"{count} продуктов", border=1)
                pdf.ln()
    
    def generate_structured_pdf(self, uid: int, snapshot: Dict[str, Any]) -> str:
        """Генерирует структурированный PDF отчет"""
        try:
            # Создаем директорию
            user_dir = Path("data") / "reports" / str(uid)
            user_dir.mkdir(parents=True, exist_ok=True)
            
            pdf_path = user_dir / "last_v2.pdf"
            
            # Настройка PDF
            pdf = self._setup_pdf()
            
            # Данные из snapshot
            report_type = snapshot.get('type', 'report')
            profile = snapshot.get('profile', {})
            result = snapshot.get('result', {})
            
            # Заголовок
            title_map = {
                'detailed_palette': 'ОТЧЕТ ПО ЦВЕТОТИПУ И ПАЛИТРЕ',
                'palette': 'ОТЧЕТ ПО ПАЛИТРЕ',
                'detailed_skincare': 'ОТЧЕТ ПО ДИАГНОСТИКЕ КОЖИ',
                'skincare': 'ОТЧЕТ ПО УХОДУ ЗА КОЖЕЙ'
            }
            
            title = title_map.get(report_type, 'ПЕРСОНАЛЬНЫЙ ОТЧЕТ')
            self._add_header(pdf, title)
            
            # 1. РЕЗЮМЕ
            self._add_section_header(pdf, "1. РЕЗЮМЕ АНАЛИЗА")
            self._add_summary_section(pdf, profile, report_type)
            
            # 2. МАКИЯЖ (15 категорий)
            if 'makeup' in result:
                self._add_section_header(pdf, "2. РЕКОМЕНДАЦИИ ПО МАКИЯЖУ")
                self._add_makeup_section(pdf, result['makeup'])
            
            # 3. УХОД (7 шагов)  
            if 'skincare' in result:
                self._add_section_header(pdf, "3. ПРОГРАММА УХОДА ЗА КОЖЕЙ")
                self._add_skincare_section(pdf, result['skincare'])
            
            # 4. СВОДНАЯ ТАБЛИЦА
            products_summary = self._calculate_products_summary(result)
            self._add_summary_table(pdf, profile, products_summary)
            
            # Сохранение
            pdf.output(str(pdf_path))
            print(f"✅ Generated structured PDF v2 for user {uid}: {pdf_path}")
            
            return str(pdf_path)
            
        except Exception as e:
            print(f"❌ Error generating structured PDF for user {uid}: {e}")
            return ""
    
    def _add_summary_section(self, pdf: FPDF, profile: Dict[str, Any], report_type: str):
        """Добавляет секцию резюме"""
        summary_parts = []
        
        # Основные характеристики
        undertone = profile.get('undertone', '')
        season = profile.get('season', '')
        contrast = profile.get('contrast', '')
        skin_type = profile.get('skin_type', '')
        
        if undertone:
            summary_parts.append(f"Ваш подтон кожи: {undertone}")
        
        if season:
            season_names = {
                'spring': 'Яркая Весна', 'summer': 'Мягкое Лето',
                'autumn': 'Глубокая Осень', 'winter': 'Холодная Зима'
            }
            summary_parts.append(f"Цветотип: {season_names.get(season, season)}")
        
        if contrast:
            summary_parts.append(f"Контрастность: {contrast}")
        
        if skin_type:
            summary_parts.append(f"Тип кожи: {skin_type}")
        
        # Проблемы кожи
        concerns = profile.get('concerns', [])
        if concerns:
            summary_parts.append(f"Основные проблемы: {', '.join(concerns)}")
        
        # Объединяем в текст
        summary_text = '. '.join(summary_parts) + '.'
        
        if summary_text.strip() != '.':
            self._add_text_block(pdf, summary_text)
        
        # Дополнительная информация по типу отчета
        if report_type in ['detailed_palette', 'palette']:
            recommendation = (
                "На основе анализа вашего цветотипа подобраны оттенки, которые "
                "подчеркнут вашу естественную красоту и создадут гармоничный образ."
            )
            self._add_text_block(pdf, recommendation)
        
        elif report_type in ['detailed_skincare', 'skincare']:
            recommendation = (
                "Программа ухода составлена с учетом особенностей вашей кожи "
                "для достижения здорового и сияющего вида."
            )
            self._add_text_block(pdf, recommendation)
    
    def _add_makeup_section(self, pdf: FPDF, makeup_data: Dict[str, List]):
        """Добавляет секцию макияжа"""
        
        section_order = ['base', 'face', 'eyes', 'lips']
        section_names = {
            'base': 'Базовый макияж',
            'face': 'Скульптурирование лица', 
            'eyes': 'Макияж глаз',
            'lips': 'Макияж губ'
        }
        
        for section in section_order:
            if section in makeup_data and makeup_data[section]:
                # Подзаголовок
                pdf.set_font_size(self.font_size_text)
                pdf.set_text_color(*self.color_section)
                pdf.cell(0, 6, f"2.{section_order.index(section) + 1}. {section_names[section]}")
                pdf.ln()
                pdf.ln(2)
                
                # Продукты в секции
                for product in makeup_data[section][:3]:  # Максимум 3 продукта на секцию
                    category = product.get('category', section)
                    self._add_product_card(pdf, product, category)
    
    def _add_skincare_section(self, pdf: FPDF, skincare_data: Dict[str, List]):
        """Добавляет секцию ухода"""
        
        # Утренний уход
        if 'AM' in skincare_data and skincare_data['AM']:
            pdf.set_font_size(self.font_size_text)
            pdf.set_text_color(*self.color_section)
            pdf.cell(0, 6, "3.1. Утренний уход")
            pdf.ln()
            pdf.ln(2)
            
            for product in skincare_data['AM']:
                self._add_skincare_product_card(pdf, product, 'AM')
        
        # Вечерний уход
        if 'PM' in skincare_data and skincare_data['PM']:
            pdf.set_font_size(self.font_size_text)
            pdf.set_text_color(*self.color_section)
            pdf.cell(0, 6, "3.2. Вечерний уход")
            pdf.ln()
            pdf.ln(2)
            
            for product in skincare_data['PM']:
                self._add_skincare_product_card(pdf, product, 'PM')
        
        # Еженедельный уход
        if 'weekly' in skincare_data and skincare_data['weekly']:
            pdf.set_font_size(self.font_size_text)
            pdf.set_text_color(*self.color_section)
            pdf.cell(0, 6, "3.3. Еженедельный уход")
            pdf.ln()
            pdf.ln(2)
            
            for product in skincare_data['weekly']:
                self._add_skincare_product_card(pdf, product, 'weekly')
    
    def _add_skincare_product_card(self, pdf: FPDF, product: Dict[str, Any], routine_type: str):
        """Добавляет карточку средства ухода"""
        if pdf.get_y() > 240:
            pdf.add_page()
        
        # Название продукта
        pdf.set_font_size(self.font_size_text)
        pdf.set_text_color(*self.color_accent)
        
        product_name = self._clean_text(product.get('name', 'Средство'))
        brand = self._clean_text(product.get('brand', ''))
        
        title = f"{brand} - {product_name}" if brand else product_name
        pdf.cell(0, 6, title, ln=True)
        
        # Категория и применение
        category = product.get('category', '')
        if category:
            frequency = self._get_skincare_frequency(category, routine_type)
            pdf.set_font_size(self.font_size_small)
            pdf.set_text_color(*self.color_text)
            pdf.cell(0, 4, f"Применение: {frequency}")
            pdf.ln()
        
        # Активные компоненты
        actives = product.get('actives', [])
        if actives:
            actives_text = f"Активные компоненты: {', '.join(actives)}"
            pdf.multi_cell(0, 4, self._clean_text(actives_text))
        
        # Объяснение
        explain = product.get('explain', '')
        if explain:
            explain_text = f"Эффект: {self._clean_text(explain)}"
            pdf.multi_cell(0, 4, explain_text)
        
        # Цена и наличие
        price = product.get('price')
        if price:
            currency = product.get('price_currency', 'RUB')
            pdf.cell(0, 4, f"Цена: {price} {currency}", ln=True)
        
        in_stock = product.get('in_stock', False)
        status_text = "В наличии" if in_stock else "Нет в наличии"
        pdf.set_text_color(*self.color_accent if not in_stock else (46, 125, 50))
        pdf.cell(0, 4, f"Статус: {status_text}", ln=True)
        
        pdf.ln(3)
    
    def _get_skincare_frequency(self, category: str, routine_type: str) -> str:
        """Получает частоту применения средства"""
        frequency_map = {
            'cleanser': {'AM': 'утром', 'PM': 'вечером', 'weekly': '2-3 раза в неделю'},
            'toner': {'AM': 'утром после очищения', 'PM': 'вечером после очищения', 'weekly': 'по необходимости'},
            'serum': {'AM': 'утром под крем', 'PM': 'вечером под крем', 'weekly': '2-3 раза в неделю'},
            'moisturizer': {'AM': 'утром', 'PM': 'вечером', 'weekly': 'ежедневно'},
            'spf': {'AM': 'утром последним слоем', 'PM': 'не применять', 'weekly': 'ежедневно утром'},
            'exfoliant': {'AM': 'не применять', 'PM': '2-3 раза в неделю', 'weekly': '1-2 раза в неделю'},
            'mask': {'AM': 'не применять', 'PM': '1-2 раза в неделю', 'weekly': '1 раз в неделю'}
        }
        
        return frequency_map.get(category, {}).get(routine_type, 'по инструкции')
    
    def _calculate_products_summary(self, result: Dict[str, Any]) -> Dict[str, int]:
        """Подсчитывает статистику по продуктам"""
        summary = {}
        
        # Подсчет макияжа
        if 'makeup' in result:
            makeup_count = 0
            for section, products in result['makeup'].items():
                makeup_count += len(products)
            summary['макияж'] = makeup_count
        
        # Подсчет ухода
        if 'skincare' in result:
            skincare_count = 0
            for routine, products in result['skincare'].items():
                skincare_count += len(products)
            summary['уход'] = skincare_count
        
        return summary


# Глобальный экземпляр генератора
_pdf_generator = None

def get_pdf_generator() -> StructuredPDFGenerator:
    """Получить глобальный экземпляр PDF генератора"""
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = StructuredPDFGenerator()
    return _pdf_generator


def generate_structured_pdf_report(uid: int, snapshot: Dict[str, Any]) -> str:
    """Основная функция для генерации структурированного PDF"""
    generator = get_pdf_generator()
    return generator.generate_structured_pdf(uid, snapshot)


if __name__ == "__main__":
    # Тест PDF генератора v2
    print("📄 PDF V2 GENERATOR TEST")
    print("=" * 40)
    
    # Тестовые данные
    test_snapshot = {
        "type": "detailed_palette",
        "profile": {
            "user_id": 12345,
            "undertone": "warm",
            "season": "autumn", 
            "contrast": "medium",
            "skin_type": "dry"
        },
        "result": {
            "makeup": {
                "base": [
                    {
                        "name": "Perfect Foundation",
                        "brand": "Test Brand",
                        "category": "foundation",
                        "price": 1500,
                        "price_currency": "RUB",
                        "in_stock": True,
                        "explain": "идеально подходит для вашего теплого подтона"
                    }
                ],
                "face": [
                    {
                        "name": "Warm Blush",
                        "brand": "Test Brand",
                        "category": "blush", 
                        "price": 800,
                        "in_stock": True,
                        "explain": "подчеркнет естественный румянец"
                    }
                ]
            },
            "skincare": {
                "AM": [
                    {
                        "name": "Gentle Cleanser",
                        "brand": "Test Brand",
                        "category": "cleanser",
                        "price": 1200,
                        "in_stock": True,
                        "actives": ["гиалуроновая кислота"],
                        "explain": "мягко очищает сухую кожу"
                    }
                ]
            }
        }
    }
    
    # Генерируем тестовый PDF
    generator = StructuredPDFGenerator()
    pdf_path = generator.generate_structured_pdf(999, test_snapshot)
    
    if pdf_path:
        print(f"✅ Test PDF generated: {pdf_path}")
        
        # Проверяем что файл создался
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"📊 File size: {file_size} bytes")
            print("✅ PDF v2 generator working correctly!")
        else:
            print("❌ PDF file not found")
    else:
        print("❌ PDF generation failed")
