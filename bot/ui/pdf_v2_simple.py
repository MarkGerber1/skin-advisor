"""
📄 PDF v2 Simple - Упрощенный, но рабочий PDF генератор
Простая структура: Резюме → Продукты → Таблица
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from fpdf import FPDF
import re


class SimplePDFGenerator:
    """Упрощенный PDF генератор с гарантированной работоспособностью"""

    def __init__(self):
        # Настройки
        self.font_size_title = 16
        self.font_size_section = 12
        self.font_size_text = 10

        # Отступы (безопасные значения)
        self.margin = 20
        self.line_height = 6

        # Emoji mapping
        self.emoji_map = {
            "🎨": "[ПАЛИТРА]",
            "🧴": "[УХОД]",
            "✨": "*",
            "🌸": "[ВЕСНА]",
            "🌊": "[ЛЕТО]",
            "🍂": "[ОСЕНЬ]",
            "❄️": "[ЗИМА]",
            "💄": "[МАКИЯЖ]",
            "👁️": "[ГЛАЗА]",
            "💡": "!",
            "🔥": "*",
            "❌": "X",
            "✅": "OK",
        }

    def _clean_text(self, text: str) -> str:
        """Очистка текста для PDF"""
        if not text:
            return ""

        # Заменяем emoji
        for emoji, replacement in self.emoji_map.items():
            text = text.replace(emoji, replacement)

        # Удаляем markdown
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"\*(.*?)\*", r"\1", text)

        # Удаляем unicode
        text = re.sub(r"[^\x00-\x7F\u0400-\u04FF]+", "", text)

        return text.strip()

    def generate_pdf(self, uid: int, snapshot: Dict[str, Any]) -> str:
        """Генерирует PDF отчет"""
        try:
            # Создаем директорию
            user_dir = Path("data") / "reports" / str(uid)
            user_dir.mkdir(parents=True, exist_ok=True)

            pdf_path = user_dir / "last_v2_simple.pdf"

            # Создаем PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_margins(self.margin, self.margin, self.margin)

            # Настройка шрифта
            try:
                # Ищем DejaVu шрифт
                font_paths = [
                    # Docker системные пути (новые)
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts-dejavu-core/DejaVuSans.ttf",
                    "/usr/share/fonts-dejavu/DejaVuSans.ttf",
                    # Docker системные пути (альтернативные)
                    "/usr/share/fonts/TTF/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf",
                    # Локальные пути
                    "assets/fonts/DejaVuSans.ttf",
                    os.path.join(
                        os.path.dirname(__file__), "..", "..", "assets", "fonts", "DejaVuSans.ttf"
                    ),
                    # Системные пути Windows
                    "C:/Windows/Fonts/DejaVuSans.ttf",
                    # Резервные пути
                    ".skin-advisor/assets/DejaVuSans.ttf",
                ]

                font_found = False
                noto_found = False

                # Ищем DejaVu
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdf.add_font("DejaVu", "", font_path)
                            pdf.set_font("DejaVu", size=self.font_size_text)
                            font_found = True
                            print(f"✅ Simple PDF: Using DejaVu font from: {font_path}")
                            break
                        except Exception as e:
                            print(f"⚠️ Simple PDF: Failed to load DejaVu from {font_path}: {e}")

                # Если DejaVu не найден, пробуем Noto Sans
                if not font_found:
                    noto_paths = [
                        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                        "/usr/share/fonts/noto/NotoSans-Regular.ttf",
                        "/usr/share/fonts/opentype/noto/NotoSans-Regular.ttf",
                        "assets/fonts/NotoSans-Regular.ttf",
                        os.path.join(
                            os.path.dirname(__file__),
                            "..",
                            "..",
                            "assets",
                            "fonts",
                            "NotoSans-Regular.ttf",
                        ),
                    ]

                    for noto_path in noto_paths:
                        if os.path.exists(noto_path):
                            try:
                                pdf.add_font("NotoSans", "", noto_path)
                                pdf.set_font("NotoSans", size=self.font_size_text)
                                noto_found = True
                                print(f"✅ Simple PDF: Using Noto Sans font from: {noto_path}")
                                break
                            except Exception as e:
                                print(f"⚠️ Simple PDF: Failed to load Noto from {noto_path}: {e}")

                # Выбираем шрифт
                if font_found:
                    pdf.set_font("DejaVu", size=self.font_size_text)
                elif noto_found:
                    pdf.set_font("NotoSans", size=self.font_size_text)
                else:
                    pdf.set_font("Arial", size=self.font_size_text)
                    print("⚠️ Simple PDF: Using Arial fallback (limited Cyrillic support)")

            except Exception as e:
                print(f"⚠️ Simple PDF: Font error: {e}, using Arial")
                pdf.set_font("Arial", size=self.font_size_text)

            # Данные
            report_type = snapshot.get("type", "report")
            profile = snapshot.get("profile", {})
            result = snapshot.get("result", {})

            # 1. ЗАГОЛОВОК
            pdf.set_font_size(self.font_size_title)
            title_map = {
                "detailed_palette": "ОТЧЕТ ПО ЦВЕТОТИПУ",
                "palette": "ОТЧЕТ ПО ПАЛИТРЕ",
                "detailed_skincare": "ПОРТРЕТ ЛИЦА",
                "skincare": "УХОД ЗА КОЖЕЙ",
            }
            title = self._clean_text(title_map.get(report_type, "ПЕРСОНАЛЬНЫЙ ОТЧЕТ"))

            # Используем multi_cell для безопасности
            pdf.multi_cell(0, 10, title, align="C")
            pdf.ln(10)

            # 2. РЕЗЮМЕ
            pdf.set_font_size(self.font_size_section)
            pdf.multi_cell(0, 8, "1. РЕЗЮМЕ АНАЛИЗА")
            pdf.ln(5)

            pdf.set_font_size(self.font_size_text)

            # Собираем информацию о профиле
            summary_parts = []

            if profile.get("undertone"):
                summary_parts.append(f"Подтон лица: {profile['undertone']}")

            if profile.get("season"):
                season_names = {
                    "spring": "Яркая Весна",
                    "summer": "Мягкое Лето",
                    "autumn": "Глубокая Осень",
                    "winter": "Холодная Зима",
                }
                summary_parts.append(
                    f"Цветотип: {season_names.get(profile['season'], profile['season'])}"
                )

            if profile.get("contrast"):
                summary_parts.append(f"Контрастность: {profile['contrast']}")

            if profile.get("skin_type"):
                summary_parts.append(f"Тип лица: {profile['skin_type']}")

            if profile.get("concerns"):
                concerns = ", ".join(profile["concerns"])
                summary_parts.append(f"Проблемы: {concerns}")

            if summary_parts:
                summary_text = self._clean_text(". ".join(summary_parts) + ".")
                pdf.multi_cell(0, self.line_height, summary_text)
                pdf.ln(5)

            # 3. РЕКОМЕНДАЦИИ ПО МАКИЯЖУ
            if "makeup" in result and result["makeup"]:
                pdf.set_font_size(self.font_size_section)
                pdf.multi_cell(0, 8, "2. РЕКОМЕНДАЦИИ ПО МАКИЯЖУ")
                pdf.ln(5)

                pdf.set_font_size(self.font_size_text)

                product_count = 0
                for section_name, products in result["makeup"].items():
                    if products:
                        section_title = {
                            "base": "Базовый макияж",
                            "face": "Скульптурирование",
                            "eyes": "Макияж глаз",
                            "lips": "Макияж губ",
                        }.get(section_name, section_name.title())

                        pdf.multi_cell(
                            0, self.line_height, f"2.{product_count + 1}. {section_title}:"
                        )
                        pdf.ln(2)

                        for product in products[:2]:  # Максимум 2 продукта на секцию
                            product_name = self._clean_text(product.get("name", "Продукт"))
                            brand = self._clean_text(product.get("brand", ""))

                            if brand:
                                product_text = f"• {brand} - {product_name}"
                            else:
                                product_text = f"• {product_name}"

                            # Цена
                            price = product.get("price")
                            if price:
                                currency = product.get("price_currency", "RUB")
                                product_text += f" ({price} {currency})"

                            # Статус
                            if not product.get("in_stock", True):
                                product_text += " [НЕТ В НАЛИЧИИ]"

                            pdf.multi_cell(0, self.line_height, product_text)

                            # Объяснение
                            explain = product.get("explain", "")
                            if explain:
                                explain_text = f"  Почему подходит: {self._clean_text(explain)}"
                                pdf.multi_cell(0, self.line_height, explain_text)

                            pdf.ln(2)

                        product_count += 1

                pdf.ln(5)

            # 4. ПРОГРАММА УХОДА
            if "skincare" in result and result["skincare"]:
                pdf.set_font_size(self.font_size_section)
                pdf.multi_cell(0, 8, "3. ПРОГРАММА УХОДА ЗА КОЖЕЙ")
                pdf.ln(5)

                pdf.set_font_size(self.font_size_text)

                routine_names = {
                    "AM": "Утренний уход",
                    "PM": "Вечерний уход",
                    "weekly": "Еженедельный уход",
                }

                routine_count = 1
                for routine_type, products in result["skincare"].items():
                    if products:
                        routine_title = routine_names.get(routine_type, routine_type)
                        pdf.multi_cell(0, self.line_height, f"3.{routine_count}. {routine_title}:")
                        pdf.ln(2)

                        for product in products[:3]:  # Максимум 3 продукта на routine
                            product_name = self._clean_text(product.get("name", "Средство"))
                            brand = self._clean_text(product.get("brand", ""))

                            if brand:
                                product_text = f"• {brand} - {product_name}"
                            else:
                                product_text = f"• {product_name}"

                            # Активные компоненты
                            actives = product.get("actives", [])
                            if actives:
                                product_text += f" (активы: {', '.join(actives)})"

                            pdf.multi_cell(0, self.line_height, product_text)

                            # Эффект
                            explain = product.get("explain", "")
                            if explain:
                                explain_text = f"  Эффект: {self._clean_text(explain)}"
                                pdf.multi_cell(0, self.line_height, explain_text)

                            pdf.ln(2)

                        routine_count += 1

                pdf.ln(5)

            # 5. СТАТИСТИКА
            pdf.set_font_size(self.font_size_section)
            pdf.multi_cell(0, 8, "4. СТАТИСТИКА РЕКОМЕНДАЦИЙ")
            pdf.ln(5)

            pdf.set_font_size(self.font_size_text)

            stats = []
            if "makeup" in result:
                makeup_count = sum(len(products) for products in result["makeup"].values())
                stats.append(f"Продуктов макияжа: {makeup_count}")

            if "skincare" in result:
                skincare_count = sum(len(products) for products in result["skincare"].values())
                stats.append(f"Средств ухода: {skincare_count}")

            # Подсчет товаров в наличии
            total_products = 0
            in_stock_products = 0

            for category in ["makeup", "skincare"]:
                if category in result:
                    for section, products in result[category].items():
                        for product in products:
                            total_products += 1
                            if product.get("in_stock", True):
                                in_stock_products += 1

            if total_products > 0:
                in_stock_percent = (in_stock_products / total_products) * 100
                stats.append(
                    f"В наличии: {in_stock_products}/{total_products} ({in_stock_percent:.0f}%)"
                )

            for stat in stats:
                pdf.multi_cell(0, self.line_height, f"• {stat}")

            # Сохранение
            pdf.output(str(pdf_path))
            print(f"✅ Generated simple PDF v2 for user {uid}: {pdf_path}")

            return str(pdf_path)

        except Exception as e:
            print(f"❌ Error generating simple PDF for user {uid}: {e}")
            return ""


def generate_simple_pdf_report(uid: int, snapshot: Dict[str, Any]) -> str:
    """Основная функция для генерации упрощенного PDF"""
    generator = SimplePDFGenerator()
    return generator.generate_pdf(uid, snapshot)


if __name__ == "__main__":
    # Тест простого PDF генератора
    print("📄 SIMPLE PDF V2 GENERATOR TEST")
    print("=" * 50)

    # Тестовые данные
    test_snapshot = {
        "type": "detailed_palette",
        "profile": {
            "user_id": 12345,
            "undertone": "warm",
            "season": "autumn",
            "contrast": "medium",
            "skin_type": "dry",
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
                        "explain": "идеально подходит для вашего теплого подтона",
                    }
                ],
                "face": [
                    {
                        "name": "Warm Blush",
                        "brand": "Test Brand",
                        "category": "blush",
                        "price": 800,
                        "in_stock": True,
                        "explain": "подчеркнет естественный румянец",
                    }
                ],
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
                        "explain": "мягко очищает сухую кожу",
                    }
                ]
            },
        },
    }

    # Генерируем тестовый PDF
    generator = SimplePDFGenerator()
    pdf_path = generator.generate_pdf(999, test_snapshot)

    if pdf_path and os.path.exists(pdf_path):
        file_size = os.path.getsize(pdf_path)
        print(f"✅ Test PDF generated: {pdf_path}")
        print(f"📊 File size: {file_size} bytes")
        print("✅ Simple PDF v2 generator working correctly!")
    else:
        print("❌ Simple PDF generation failed")
