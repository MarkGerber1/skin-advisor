import json
from app.infra.links import generate_product_links
from app.infra.settings import get_settings

with open('app/i18n/ru.json', 'r', encoding='utf-8') as f:
	LEXICON = json.load(f)


def get_welcome_message(user_name: str) -> str:
	"""Форматирует приветственное сообщение."""
	return LEXICON['welcome'].format(user_name=user_name)


def get_help_message() -> str:
	"""Возвращает текст помощи."""
	return LEXICON['help_text']


def get_privacy_message() -> str:
	"""Возвращает политику конфиденциальности."""
	settings = get_settings()
	return LEXICON['privacy_text'].format(
		days=settings.app.data_retention_days,
		url=settings.app.privacy_policy_url
	)


def format_diagnosis_result(result: dict) -> str:
	"""Форматирует результат диагностики для вывода пользователю."""
	states_str = ", ".join(result.get('states', ['не определены']))

	text = (
		f"<b>✅ Ваши результаты диагностики:</b>\n\n"
		f"<b>Тип кожи:</b> {result.get('skin_type', 'не определен').capitalize()}\n"
		f"<b>Состояния:</b> {states_str.capitalize()}\n"
		f"<b>Подтон:</b> {result.get('undertone', 'не определен').capitalize()}\n\n"
		f"<b>Почему мы так решили (основные моменты):</b>\n"
	)
	for reason in result.get('reasoning', [])[:3]:  # Показываем только 3 для краткости
		text += f"• <i>{reason}</i>\n"

	return text


def fmt_rub(v: float) -> str:
	# Форматируем с разделителем тысяч пробелом: 2990 -> '2 990'
	return f"{int(round(v)):,}".replace(",", " ").replace("\xa0", " ") + " ₽"


def render_item_text(item: dict) -> str:
	title = f"{item.get('brand','')} {item.get('name','')}".strip()
	stock = item.get("_stock") or {}
	p = stock.get("price")
	return f"{title}\n≈ {fmt_rub(p)}" if p is not None else f"{title}\nЦена на странице магазина"


def format_recommendations(recs: dict) -> str:
	"""Форматирует рекомендации для вывода пользователю."""
	settings = get_settings()
	text = ""

	routines = recs.get('routines', {})

	# Словарь для красивых заголовков
	titles = {
		'am': '☀️ <b>Утренний уход (AM)</b>',
		'pm': '🌙 <b>Вечерний уход (PM)</b>',
		'weekly': '✨ <b>Еженедельный уход (1-2 раза в неделю)</b>',
		'makeup': '💄 <b>Рекомендации по макияжу</b>'
	}

	for key, title in titles.items():
		if routine_steps := routines.get(key):
			text += f"{title}\n"
			for i, step in enumerate(routine_steps):
				product = step['product']
				how_to_use = step['how_to_use']
				links = generate_product_links(product)

				# Новая строка с ценой
				stock = product.get('_stock') or {}
				p = stock.get('price')
				price_line = f"≈ {fmt_rub(p)}" if p is not None else "Цена на странице магазина"

				text += (
					f"<b>{i+1}. {product['name']} ({product['brand']})</b>\n"
					f"<i>Назначение:</i> {product['purpose']}\n"
					f"<i>Как использовать:</i> {how_to_use}\n"
					f"{price_line}\n"
					f"{'🛒 ' + links if links else ''}\n\n"
				)
			text += "\n"

	if warnings := recs.get('warnings'):
		text += "⚠️ <b>Важные предосторожности:</b>\n"
		for warning in warnings:
			text += f"• <i>{warning}</i>\n"
		text += "\n"

	text += f"\n{settings.app.disclaimer}"

	return text


