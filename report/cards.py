#!/usr/bin/env python3
"""
Генерация визуальных карточек результатов для Telegram и PDF
Использует SVG для векторной графики и Pillow для растровых изображений
"""

import os
import io
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import base64

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("⚠️ Pillow not available, PNG generation disabled")

try:
    import cairosvg
    CAIRO_AVAILABLE = True
except ImportError:
    CAIRO_AVAILABLE = False
    print("⚠️ CairoSVG not available, SVG to PNG conversion disabled")

from engine.models import UserProfile, Season, Undertone


@dataclass
class CardConfig:
    """Конфигурация карточки"""
    width: int = 800
    height: int = 600
    background_color: str = "#FFFFFF"
    primary_color: str = "#C26A8D"
    secondary_color: str = "#F4DCE4"
    accent_color: str = "#C9B7FF"
    text_color: str = "#121212"
    muted_color: str = "#6B6B6B"
    font_family: str = "Arial"
    font_size_title: int = 32
    font_size_subtitle: int = 24
    font_size_body: int = 18
    font_size_caption: int = 14


class VisualCardGenerator:
    """Генератор визуальных карточек результатов"""

    def __init__(self):
        self.config = CardConfig()
        self._ensure_output_dirs()

    def _ensure_output_dirs(self):
        """Создание необходимых директорий"""
        os.makedirs("output/cards", exist_ok=True)

    def _get_user_output_dir(self, user_id: int) -> str:
        """Получение директории для пользователя"""
        date_str = datetime.now().strftime("%Y%m%d")
        user_dir = f"output/cards/{user_id}/{date_str}"
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    def _create_svg_template(self, title: str, subtitle: str = "") -> str:
        """Создание базового SVG шаблона"""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{self.config.width}" height="{self.config.height}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="100%" height="100%" fill="{self.config.background_color}"/>

  <!-- Header gradient -->
  <defs>
    <linearGradient id="headerGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{self.config.primary_color};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{self.config.accent_color};stop-opacity:1" />
    </linearGradient>
  </defs>

  <!-- Header -->
  <rect x="0" y="0" width="100%" height="120" fill="url(#headerGradient)"/>
  <text x="50%" y="50" font-family="{self.config.font_family}" font-size="{self.config.font_size_title}"
        fill="white" text-anchor="middle" dominant-baseline="middle" font-weight="bold">{title}</text>

  <!-- Subtitle -->
  {f'<text x="50%" y="90" font-family="{self.config.font_family}" font-size="{self.config.font_size_subtitle}" fill="white" text-anchor="middle" opacity="0.9">{subtitle}</text>' if subtitle else ''}
</svg>'''

    def generate_makeup_card(self, profile: UserProfile, result_data: Dict) -> Dict[str, str]:
        """
        Генерация карточки для результатов теста "Тон&Сияние"

        Args:
            profile: Профиль пользователя
            result_data: Данные результата теста

        Returns:
            Dict с путями к SVG и PNG файлам
        """
        season_names = {
            Season.SPRING: "🌸 Яркая Весна",
            Season.SUMMER: "🌊 Мягкое Лето",
            Season.AUTUMN: "🍂 Глубокая Осень",
            Season.WINTER: "❄️ Холодная Зима"
        }

        undertone_names = {
            Undertone.WARM: "Теплый",
            Undertone.COOL: "Холодный",
            Undertone.NEUTRAL: "Нейтральный"
        }

        season = season_names.get(profile.season, "Не определен")
        undertone = undertone_names.get(profile.undertone, "Не определен")

        # Создание SVG
        svg_content = self._create_svg_template("Ваш цветотип", season)

        # Добавление информации о подтоне
        svg_content += f'''
  <!-- Undertone info -->
  <text x="50" y="160" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}" font-weight="bold">Подтон кожи: {undertone}</text>

  <!-- Palette visualization -->
  <text x="50" y="200" font-family="{self.config.font_family}" font-size="{self.config.font_size_subtitle}"
        fill="{self.config.primary_color}" font-weight="bold">Рекомендуемая палитра:</text>

  <!-- Color swatches -->
  <rect x="50" y="220" width="80" height="80" fill="{self.config.primary_color}" rx="8"/>
  <text x="90" y="270" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}"
        fill="{self.config.text_color}" text-anchor="middle">Основной</text>

  <rect x="150" y="220" width="80" height="80" fill="{self.config.secondary_color}" rx="8"/>
  <text x="190" y="270" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}"
        fill="{self.config.text_color}" text-anchor="middle">Второстепенный</text>

  <rect x="250" y="220" width="80" height="80" fill="{self.config.accent_color}" rx="8"/>
  <text x="290" y="270" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}"
        fill="{self.config.text_color}" text-anchor="middle">Акцент</text>

  <!-- Makeup recommendations -->
  <text x="50" y="320" font-family="{self.config.font_family}" font-size="{self.config.font_size_subtitle}"
        fill="{self.config.primary_color}" font-weight="bold">Рекомендации по макияжу:</text>

  <text x="50" y="350" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}">• Тон: {self._get_foundation_recommendation(profile)}</text>
  <text x="50" y="375" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}">• Румяна: {self._get_blush_recommendation(profile)}</text>
  <text x="50" y="400" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}">• Тени: {self._get_eyeshadow_recommendation(profile)}</text>
  <text x="50" y="425" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}">• Помада: {self._get_lipstick_recommendation(profile)}</text>

  <!-- Footer -->
  <text x="50" y="480" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}"
        fill="{self.config.muted_color}">Beauty Care • Персонализированные рекомендации</text>
  <text x="50" y="500" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}"
        fill="{self.config.muted_color}">Используйте /theme для переключения тем</text>

</svg>'''

        # Сохранение файлов
        user_id = getattr(profile, 'user_id', 0)
        output_dir = self._get_user_output_dir(user_id)

        svg_path = f"{output_dir}/makeup_card.svg"
        png_path = f"{output_dir}/makeup_card.png"

        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        # Конвертация SVG в PNG если возможно
        if CAIRO_AVAILABLE and PILLOW_AVAILABLE:
            try:
                cairosvg.svg2png(bytestring=svg_content.encode('utf-8'),
                                write_to=png_path,
                                output_width=self.config.width,
                                output_height=self.config.height)
            except Exception as e:
                print(f"❌ Error converting SVG to PNG: {e}")

        return {
            'svg': svg_path,
            'png': png_path if os.path.exists(png_path) else None
        }

    def generate_skincare_card(self, profile: UserProfile, result_data: Dict) -> Dict[str, str]:
        """
        Генерация карточки для результатов теста "Портрет лица"
        """
        # Определение типа кожи на основе данных
        skin_type = result_data.get('skin_type', 'Не определен')
        concerns = result_data.get('concerns', [])
        sensitivity = result_data.get('sensitivity', 'normal')

        # Создание SVG
        svg_content = self._create_svg_template("Ваш тип кожи", skin_type)

        # Добавление информации о состоянии кожи
        svg_content += f'''
  <!-- Skin analysis -->
  <text x="50" y="160" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}" font-weight="bold">Анализ кожи:</text>

  <text x="70" y="185" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.muted_color}">• Тип: {skin_type}</text>
  <text x="70" y="210" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.muted_color}">• Чувствительность: {sensitivity}</text>
  <text x="70" y="235" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.muted_color}">• Проблемы: {", ".join(concerns) if concerns else "Нет"}</text>

  <!-- Care routine -->
  <text x="50" y="280" font-family="{self.config.font_family}" font-size="{self.config.font_size_subtitle}"
        fill="{self.config.primary_color}" font-weight="bold">Рекомендуемый уход:</text>

  <text x="50" y="310" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}" font-weight="bold">Утренний ритуал:</text>
  <text x="70" y="335" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}">• Очищение: {self._get_cleansing_recommendation(skin_type)}</text>
  <text x="70" y="360" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}">• Увлажнение: {self._get_moisturizing_recommendation(skin_type)}</text>
  <text x="70" y="385" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}">• SPF: Обязательно, минимум SPF 30</text>

  <text x="50" y="420" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}" font-weight="bold">Вечерний ритуал:</text>
  <text x="70" y="445" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}">• Демакияж: {self._get_removal_recommendation(skin_type)}</text>
  <text x="70" y="470" font-family="{self.config.font_family}" font-size="{self.config.font_size_body}"
        fill="{self.config.text_color}">• Уход: {self._get_night_care_recommendation(skin_type)}</text>

  <!-- Footer -->
  <text x="50" y="520" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}"
        fill="{self.config.muted_color}">Beauty Care • Персонализированный уход</text>
  <text x="50" y="540" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}"
        fill="{self.config.muted_color}">Результаты основаны на вашем профиле</text>

</svg>'''

        # Сохранение файлов
        user_id = getattr(profile, 'user_id', 0)
        output_dir = self._get_user_output_dir(user_id)

        svg_path = f"{output_dir}/skincare_card.svg"
        png_path = f"{output_dir}/skincare_card.png"

        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        # Конвертация SVG в PNG если возможно
        if CAIRO_AVAILABLE and PILLOW_AVAILABLE:
            try:
                cairosvg.svg2png(bytestring=svg_content.encode('utf-8'),
                                write_to=png_path,
                                output_width=self.config.width,
                                output_height=self.config.height)
            except Exception as e:
                print(f"❌ Error converting SVG to PNG: {e}")

        return {
            'svg': svg_path,
            'png': png_path if os.path.exists(png_path) else None
        }

    def generate_radial_chart(self, data: Dict[str, float], title: str) -> str:
        """
        Генерация радиальной диаграммы для PDF
        """
        if not data:
            return ""

        # Улучшенная SVG радиальная диаграмма
        center_x, center_y = 200, 200
        radius = 150

        svg = f'''<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="chartBg" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:{self.config.secondary_color};stop-opacity:0.3" />
      <stop offset="100%" style="stop-color:{self.config.background_color};stop-opacity:0.1" />
    </radialGradient>
  </defs>

  <!-- Background circle -->
  <circle cx="{center_x}" cy="{center_y}" r="{radius}" fill="url(#chartBg)" stroke="{self.config.border}" stroke-width="2"/>

  <!-- Title -->
  <text x="200" y="30" text-anchor="middle" font-family="{self.config.font_family}"
        font-size="{self.config.font_size_subtitle}" fill="{self.config.primary_color}" font-weight="bold">{title}</text>'''

        # Круги для шкалы (5 уровней)
        for i in range(1, 6):
            r = radius * i / 5
            opacity = 0.1 + (i * 0.15)
            svg += f'<circle cx="{center_x}" cy="{center_y}" r="{r}" fill="none" stroke="{self.config.muted_color}" stroke-width="1" opacity="{opacity}"/>'

            # Метки шкалы
            if i < 5:
                label = f"{i*20}%"
                svg += f'<text x="{center_x}" y="{center_y - r - 5}" text-anchor="middle" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}" fill="{self.config.muted_color}">{label}</text>'

        # Радиальные линии и данные
        angle_step = 360 / len(data)
        colors = [self.config.primary_color, self.config.accent_color, self.config.secondary_color]

        for i, (label, value) in enumerate(data.items()):
            angle = (i * angle_step - 90) * 3.14159 / 180  # в радианы
            color = colors[i % len(colors)]

            # Нормализуем значение к радиусу
            normalized_radius = radius * min(value / 100, 1.0)

            x2 = center_x + normalized_radius * (1 if i % 2 == 0 else -1)
            y2 = center_y + normalized_radius * (1 if i % 2 == 0 else -1)

            # Основная линия
            svg += f'<line x1="{center_x}" y1="{center_y}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3" stroke-linecap="round"/>'

            # Точка на конце линии
            svg += f'<circle cx="{x2}" cy="{y2}" r="4" fill="{color}" stroke="white" stroke-width="2"/>'

            # Метка
            label_radius = radius + 40
            label_x = center_x + label_radius * (1 if i % 2 == 0 else -1)
            label_y = center_y + label_radius * (1 if i % 2 == 0 else -1)
            svg += f'<text x="{label_x}" y="{label_y}" text-anchor="middle" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}" fill="{self.config.text_color}" font-weight="bold">{label}</text>'

            # Значение рядом с точкой
            value_x = x2 + 10 * (1 if i % 2 == 0 else -1)
            value_y = y2 - 10
            svg += f'<text x="{value_x}" y="{value_y}" text-anchor="middle" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}" fill="{color}" font-weight="bold">{int(value)}%</text>'

        svg += '</svg>'
        return svg

    def generate_bar_chart(self, data: Dict[str, float], title: str, ylabel: str = "Значение") -> str:
        """
        Генерация столбчатой диаграммы для PDF
        """
        if not data:
            return ""

        # SVG столбчатая диаграмма
        width, height = 400, 300
        chart_width, chart_height = 350, 200
        left_margin, top_margin = 40, 60

        svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <!-- Title -->
  <text x="{width//2}" y="25" text-anchor="middle" font-family="{self.config.font_family}"
        font-size="{self.config.font_size_subtitle}" fill="{self.config.primary_color}" font-weight="bold">{title}</text>

  <!-- Y-axis label -->
  <text x="15" y="{height//2}" text-anchor="middle" font-family="{self.config.font_family}"
        font-size="{self.config.font_size_caption}" fill="{self.config.muted_color}" transform="rotate(-90,15,{height//2})">{ylabel}</text>'''

        # Сетка и оси
        max_value = max(data.values()) if data else 100
        bar_width = chart_width / len(data) * 0.8
        bar_spacing = chart_width / len(data) * 0.2

        # Горизонтальные линии сетки
        for i in range(0, 6):
            y = top_margin + chart_height - (chart_height * i / 5)
            value = max_value * i / 5
            svg += f'<line x1="{left_margin}" y1="{y}" x2="{left_margin + chart_width}" y2="{y}" stroke="{self.config.muted_color}" stroke-width="1" opacity="0.3"/>'
            svg += f'<text x="{left_margin - 5}" y="{y + 3}" text-anchor="end" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}" fill="{self.config.muted_color}">{int(value)}</text>'

        # Столбцы
        colors = [self.config.primary_color, self.config.accent_color, self.config.secondary_color]
        for i, (label, value) in enumerate(data.items()):
            bar_height = (value / max_value) * chart_height
            bar_x = left_margin + i * (bar_width + bar_spacing)
            bar_y = top_margin + chart_height - bar_height

            color = colors[i % len(colors)]

            # Столбец
            svg += f'<rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="3"/>'

            # Значение над столбцом
            svg += f'<text x="{bar_x + bar_width/2}" y="{bar_y - 5}" text-anchor="middle" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}" fill="{color}" font-weight="bold">{int(value)}</text>'

            # Метка оси X
            svg += f'<text x="{bar_x + bar_width/2}" y="{top_margin + chart_height + 15}" text-anchor="middle" font-family="{self.config.font_family}" font-size="{self.config.font_size_caption}" fill="{self.config.text_color}">{label}</text>'

        svg += '</svg>'
        return svg

    def _get_foundation_recommendation(self, profile: UserProfile) -> str:
        """Рекомендации по тону на основе профиля"""
        if profile.undertone == Undertone.WARM:
            return "Теплые бежевые тона с золотистым подтоном"
        elif profile.undertone == Undertone.COOL:
            return "Холодные розовые тона с голубым подтоном"
        else:
            return "Нейтральные натуральные тона"

    def _get_blush_recommendation(self, profile: UserProfile) -> str:
        """Рекомендации по румянам"""
        if profile.season == Season.SPRING:
            return "Персиковые и абрикосовые оттенки"
        elif profile.season == Season.SUMMER:
            return "Нежно-розовые пастельные тона"
        elif profile.season == Season.AUTUMN:
            return "Терракотовые и бронзовые оттенки"
        elif profile.season == Season.WINTER:
            return "Ярко-розовые и малиновые тона"
        else:
            return "Натуральные бежевые оттенки"

    def _get_eyeshadow_recommendation(self, profile: UserProfile) -> str:
        """Рекомендации по теням"""
        if profile.season == Season.SPRING:
            return "Золотистые, персиковые и лавандовые тона"
        elif profile.season == Season.SUMMER:
            return "Пастельные голубые, розовые и серые"
        elif profile.season == Season.AUTUMN:
            return "Теплые коричневые, медные и фиолетовые"
        elif profile.season == Season.WINTER:
            return "Драматичные черные, серебряные и синие"
        else:
            return "Натуральные бежевые и коричневые тона"

    def _get_lipstick_recommendation(self, profile: UserProfile) -> str:
        """Рекомендации по помаде"""
        if profile.season == Season.SPRING:
            return "Нежные коралловые и персиковые тона"
        elif profile.season == Season.SUMMER:
            return "Розовые нюдовые и пастельные оттенки"
        elif profile.season == Season.AUTUMN:
            return "Бордовые, винные и шоколадные тона"
        elif profile.season == Season.WINTER:
            return "Красные, бордовые и сливовые оттенки"
        else:
            return "Натуральные бежевые нюдовые тона"

    def _get_cleansing_recommendation(self, skin_type: str) -> str:
        """Рекомендации по очищению"""
        if skin_type.lower() in ['жирная', 'комбинированная']:
            return "Гели и пенки для глубокого очищения"
        elif skin_type.lower() in ['сухая', 'чувствительная']:
            return "Мягкие кремы и молочко для деликатного очищения"
        else:
            return "Баланс между очищением и увлажнением"

    def _get_moisturizing_recommendation(self, skin_type: str) -> str:
        """Рекомендации по увлажнению"""
        if skin_type.lower() in ['сухая']:
            return "Плотные кремы с маслами и гиалуроновой кислотой"
        elif skin_type.lower() in ['жирная']:
            return "Легкие гели и флюиды без масел"
        elif skin_type.lower() == 'комбинированная':
            return "Легкие кремы для T-зоны, плотные для щек"
        else:
            return "Универсальные увлажняющие кремы"

    def _get_removal_recommendation(self, skin_type: str) -> str:
        """Рекомендации по снятию макияжа"""
        if skin_type.lower() in ['чувствительная']:
            return "Мягкие мицеллярные воды и кремы"
        else:
            return "Двухфазные средства или гидрофильные масла"

    def _get_night_care_recommendation(self, skin_type: str) -> str:
        """Рекомендации по вечернему уходу"""
        if skin_type.lower() in ['сухая']:
            return "Питательные кремы с ретинолом и маслами"
        elif skin_type.lower() in ['жирная']:
            return "Легкие сыворотки с салициловой кислотой"
        else:
            return "Регенерирующие кремы и маски"


# Глобальная функция для удобства использования
def generate_visual_cards(user_id: int, test_type: str, profile: UserProfile, result_data: Dict) -> Dict[str, str]:
    """
    Удобная функция для генерации визуальных карточек

    Args:
        user_id: ID пользователя
        test_type: Тип теста ('makeup' или 'skincare')
        profile: Профиль пользователя
        result_data: Данные результата

    Returns:
        Dict с путями к файлам
    """
    generator = VisualCardGenerator()

    if test_type == 'makeup':
        return generator.generate_makeup_card(profile, result_data)
    elif test_type == 'skincare':
        return generator.generate_skincare_card(profile, result_data)
    else:
        raise ValueError(f"Unsupported test type: {test_type}")


if __name__ == "__main__":
    # Пример использования
    print("🎨 Visual Card Generator")
    print("Использование: python report/cards.py")
    print("Генерирует визуальные карточки результатов тестов")
