import json
from pathlib import Path
from typing import List, Dict, Any

# Путь к каталогу продуктов относительно корня проекта
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTS_PATH = PROJECT_ROOT / "data" / "products.json"

# Инициализация PRODUCTS
with open(PRODUCTS_PATH, 'r', encoding='utf-8') as f:
    PRODUCTS: List[Dict[str, Any]] = json.load(f)


def reload_products() -> int:
    """Перечитывает products.json в память. Возвращает кол-во продуктов."""
    global PRODUCTS
    with open(PRODUCTS_PATH, 'r', encoding='utf-8') as f:
        PRODUCTS = json.load(f)
    return len(PRODUCTS)


def _find_product(category: str, diagnosis: dict, price_tier: str, purpose_keywords: list[str] | None = None, required_actives: list[str] | None = None):
    """
    Ищет наиболее подходящий продукт в каталоге.
    """
    candidates = []
    for product in PRODUCTS:
        if product['category'] != category:
            continue

        # Фильтрация по цене
        if product['price_tier'] != price_tier:
            continue

        # Фильтрация по типу кожи
        is_type_match = diagnosis['skin_type'] in product['skin_type'] or 'любой' in product['skin_type']
        if not is_type_match:
            continue

        # Оценка соответствия
        score = 0
        if purpose_keywords:
            if any(key in product['purpose'] for key in purpose_keywords):
                score += 5

        if required_actives:
            if any(act in product['actives'] for act in required_actives):
                score += 10  # Актив в приоритете

        # Соответствие состояниям кожи
        state_matches = set(diagnosis['states']) & set(product['skin_state'])
        score += len(state_matches)

        if score > 0:
            candidates.append({'product': product, 'score': score})

    if not candidates:
        return None, "К сожалению, продукт не найден. Попробуйте другую ценовую категорию."

    # Возвращаем продукт с наивысшим баллом
    best_match = max(candidates, key=lambda x: x['score'])
    return best_match['product'], None


def get_recommendations(diagnosis: dict, price_tier: str) -> dict:
    """
    Формирует полные рекомендации по уходу и макияжу.
    """
    routines = {
        'am': [],
        'pm': [],
        'weekly': [],
        'makeup': [],
    }
    warnings = []

    # --- AM Routine ---
    # 1. Очищение
    p_clean, _ = _find_product('очищение', diagnosis, price_tier, purpose_keywords=['мягкое', 'очищение'])
    if p_clean:
        routines['am'].append({'product': p_clean, 'how_to_use': 'Используйте для умывания утром.'})

    # 2. Сыворотка (Витамин C или Ниацинамид)
    if 'пигментация' in diagnosis['states'] or 'тусклость' in diagnosis['states']:
        p_serum_am, _ = _find_product('сыворотка', diagnosis, price_tier, required_actives=['витамин C'])
        if p_serum_am:
            routines['am'].append({'product': p_serum_am, 'how_to_use': 'Нанесите на сухую кожу после очищения.'})

    # 3. Увлажнение
    p_moist, _ = _find_product('увлажнение', diagnosis, price_tier, purpose_keywords=['увлажнение', 'крем'])
    if p_moist:
        routines['am'].append({'product': p_moist, 'how_to_use': 'Наносите после сыворотки или на чистую кожу.'})

    # 4. SPF
    p_spf, _ = _find_product('spf', diagnosis, price_tier)
    if p_spf:
        routines['am'].append({'product': p_spf, 'how_to_use': 'Обязательно наносите каждое утро за 20 минут до выхода.'})
    else:
        warnings.append("❗ SPF 50+ обязателен каждое утро! В каталоге не найден подходящий продукт, но его использование критически важно.")

    # --- PM Routine ---
    # 1. Очищение (может быть то же, что и утром)
    if p_clean:
        routines['pm'].append({'product': p_clean, 'how_to_use': 'Используйте для умывания вечером. Если носите макияж - это второй этап после гидрофильного масла/бальзама.'})

    # 2. Актив (Ретиноиды/Кислоты)
    if 'акне' in diagnosis['states'] or 'постакне' in diagnosis['states'] or 'морщины' in diagnosis['states']:
        p_ret, _ = _find_product('актив', diagnosis, price_tier, required_actives=['ретиналь', 'ретинол'])
        if p_ret:
            routines['pm'].append({'product': p_ret, 'how_to_use': 'Наносите на сухую кожу 2-3 раза в неделю, постепенно увеличивая частоту.'})
            warnings.append("⚠️ Начинайте вводить ретиноиды постепенно (2 раза в неделю), следите за реакцией кожи.")
            warnings.append("Не используйте ретиноиды в один вечер с кислотными пилингами.")

    # 3. Увлажнение (вечер)
    p_moist2, _ = _find_product('увлажнение', diagnosis, price_tier, purpose_keywords=['увлажнение', 'крем'])
    if p_moist2:
        routines['pm'].append({'product': p_moist2, 'how_to_use': 'Наносите через 20-30 минут после актива или сразу после очищения в свободные от активов дни.'})

    # --- Weekly Routine ---
    p_weekly, _ = _find_product('маска', diagnosis, price_tier, purpose_keywords=['энзимная', 'кислотная', 'очищающая'])
    if p_weekly:
        routines['weekly'].append({'product': p_weekly, 'how_to_use': 'Используйте 1-2 раза в неделю на очищенную кожу.'})

    # --- Makeup ---
    if diagnosis['skin_type'] in ['жирная', 'комбинированная']:
        p_base, _ = _find_product('тон', diagnosis, price_tier, purpose_keywords=['стойкое', 'матирующее'])
    else:
        p_base, _ = _find_product('тон', diagnosis, price_tier, purpose_keywords=['увлажняющее', 'легкое'])
    if p_base:
        routines['makeup'].append({'product': p_base, 'how_to_use': f"Подходит для вашего типа кожи. Выбирайте оттенок, соответствующий вашему подтону ({diagnosis['undertone']})."})

    p_lips, _ = _find_product('губы', diagnosis, price_tier)
    if p_lips:
        routines['makeup'].append({'product': p_lips, 'how_to_use': f"Подбирайте оттенки из вашей цветовой палитры ({diagnosis['color_palette']})."})

    return {'routines': routines, 'warnings': warnings}
