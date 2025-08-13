from app.infra.settings import get_settings


def generate_product_links(product: dict) -> str:
    """Генерирует строку с Markdown-ссылками на маркетплейсы."""
    settings = get_settings()
    links = []

    # Используем список маркетплейсов из конфига, чтобы сохранить порядок
    for marketplace_name in settings.app.marketplaces:
        if marketplace_name in product.get("links", {}):
            url = product["links"][marketplace_name]
            links.append(f'<a href="{url}">{marketplace_name}</a>')

    return " | ".join(links)

