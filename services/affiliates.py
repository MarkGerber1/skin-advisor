"""
Affiliate Links Service
Генерация партнерских ссылок с приоритетом источников
"""

import urllib.parse
from typing import Dict, List, Optional, Any

# Try to import config, fallback to mock if not available
try:
    from config.env import get_settings
    _settings_available = True
except ImportError:
    print("⚠️ Config module not available, using mock settings")
    get_settings = None
    _settings_available = False

class AffiliateService:
    """Сервис для работы с партнерскими ссылками"""

    def __init__(self):
        if _settings_available and get_settings is not None:
            try:
                self.settings = get_settings()
                print("✅ AffiliateService: Settings loaded successfully")
            except Exception as e:
                print(f"⚠️ AffiliateService: Could not load settings: {e}, using defaults")
                self.settings = None
        else:
            print("⚠️ AffiliateService: Settings module not available, using defaults")
            self.settings = None

        # Use default values if settings not available
        if self.settings is None:
            self.settings = type('MockSettings', (), {
                'affiliate_tag': 'skincare_bot',
                'partner_code': 'aff_skincare_bot'
            })()

        # Конфигурация партнерских параметров для разных источников
        self.affiliate_configs = {
            'goldapple': {
                'aff_param': 'partner',
                'campaign_param': 'utm_campaign',
                'source_param': 'utm_source',
                'medium_param': 'utm_medium',
                'partner_code': getattr(self.settings, 'affiliate_tag', 'skincare_bot'),
                'priority': 1
            },
            'ru_official': {
                'aff_param': 'affiliate',
                'campaign_param': 'campaign',
                'source_param': 'source',
                'medium_param': 'medium',
                'partner_code': getattr(self.settings, 'partner_code', 'aff_skincare_bot'),
                'priority': 2
            },
            'ru_marketplace': {
                'aff_param': 'partner',
                'campaign_param': 'campaign',
                'source_param': 'ref',
                'medium_param': 'medium',
                'partner_code': getattr(self.settings, 'affiliate_tag', 'skincare_bot'),
                'priority': 3
            },
            'intl_authorized': {
                'aff_param': 'aff',
                'campaign_param': 'campaign',
                'source_param': 'source',
                'medium_param': 'medium',
                'partner_code': getattr(self.settings, 'partner_code', 'aff_skincare_bot'),
                'priority': 4
            },
            'default': {
                'aff_param': 'partner',
                'campaign_param': 'utm_campaign',
                'source_param': 'utm_source',
                'medium_param': 'utm_medium',
                'partner_code': getattr(self.settings, 'affiliate_tag', 'skincare_bot'),
                'priority': 5
            }
        }

    def build_ref_link(self, product: Dict[str, Any], campaign: str = "recommendation") -> Optional[str]:
        """Создать партнерскую ссылку для продукта с приоритетом источников

        Приоритеты:
        1. Gold Apple (RU официальный)
        2. RU официальные магазины (LETO, RIVE GAUCHE, SEPHORA)
        3. RU маркетплейсы (Wildberries, Ozon, Yandex Market)
        4. Международные (Sephora US, Amazon)
        5. Default

        Args:
            product: Словарь с данными продукта
            campaign: Кампания для UTM меток

        Returns:
            Партнерская ссылка или None если не удалось создать
        """
        try:
            product_id = product.get('id', 'unknown')
            print(f"🔗 Building affiliate link for product {product_id}")

            # 1. Если уже есть ref_link в продукте, используем его (высший приоритет)
            if product.get('ref_link'):
                print(f"✅ Using existing ref_link for {product_id}")
                return product['ref_link']

            # 2. Получаем оригинальную ссылку
            original_link = product.get('link') or product.get('url')
            if not original_link:
                print(f"⚠️ No link found for product {product_id}")
                return None

            # 3. Определяем источник по ссылке
            source = self._detect_source(product)
            print(f"🔍 Detected source for {product_id}: {source}")

            # 4. Приоритизация источников
            if source == 'goldapple':
                config_key = 'goldapple'
            elif source == 'ru_official':
                config_key = 'ru_official'
            elif source == 'ru_marketplace':
                config_key = 'ru_marketplace'
            elif source == 'intl_authorized':
                config_key = 'intl_authorized'
            else:
                config_key = 'default'

            # 5. Проверяем конфигурацию
            if not self.affiliate_configs or config_key not in self.affiliate_configs:
                print(f"⚠️ No affiliate config for {config_key}, returning original link")
                return original_link

            # 6. Генерируем партнерскую ссылку
            affiliate_url = self._add_affiliate_params(original_link, config_key, campaign)
            print(f"✅ Generated affiliate link for {product_id}: {affiliate_url[:60]}...")
            print(f"🔗 affiliate_link_built: product={product_id}, source={config_key}, priority={self.affiliate_configs[config_key]['priority']}")

            return affiliate_url

        except Exception as e:
            print(f"❌ Error building affiliate link for product {product.get('id', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
            # Возвращаем оригинальную ссылку в случае ошибки
            return product.get('link') or product.get('url')

    def _detect_source(self, product: Dict[str, Any]) -> Optional[str]:
        """Определить источник продукта с приоритетом"""
        # Проверяем по ссылке (высший приоритет)
        link = product.get('link') or product.get('url', '')
        if link:
            link_lower = link.lower()

            # Gold Apple - высший приоритет
            if 'goldapple' in link_lower:
                return 'goldapple'

            # RU официальные магазины
            if any(domain in link_lower for domain in ['letu.ru', 'rive-gauche.ru', 'sephora.ru']):
                return 'ru_official'

            # RU маркетплейсы
            if any(domain in link_lower for domain in ['wildberries.ru', 'ozon.ru', 'yandex.market.ru', 'market.yandex.ru']):
                return 'ru_marketplace'

            # Международные
            if any(domain in link_lower for domain in ['amazon.com', 'sephora.com', 'ulta.com']):
                return 'intl_authorized'

        # Проверяем по названию/бренду (если не нашли по ссылке)
        brand = product.get('brand', '').lower()
        name = product.get('name', '').lower()

        # Gold Apple
        if 'goldapple' in brand or 'goldapple' in name:
            return 'goldapple'

        # RU маркетплейсы
        if any(x in brand or x in name for x in ['wildberries', 'ozon', 'marketplace', 'яндекс']):
            return 'ru_marketplace'

        # Официальные магазины
        if any(x in brand or x in name for x in ['official', 'brand', 'официальный']):
            return 'ru_official'

        return None

    def _add_affiliate_params(self, url: str, source: str, campaign: str) -> str:
        """Добавить партнерские параметры к URL"""
        if not url or not source:
            print(f"⚠️ Invalid parameters for affiliate: url={bool(url)}, source={source}")
            return url

        config = self.affiliate_configs.get(source)
        if not config:
            print(f"⚠️ No config found for source: {source}")
            return url

        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)

            # Безопасное добавление партнерских параметров
            aff_param = config.get('aff_param')
            partner_code = config.get('partner_code')
            if aff_param and partner_code:
                params[aff_param] = [partner_code]

            source_param = config.get('source_param')
            if source_param:
                params[source_param] = [source]

            medium_param = config.get('medium_param')
            if medium_param:
                params[medium_param] = ['affiliate']

            campaign_param = config.get('campaign_param')
            if campaign_param:
                params[campaign_param] = [campaign]

            # Реконструируем URL
            new_query = urllib.parse.urlencode(params, doseq=True)
            new_url = parsed._replace(query=new_query).geturl()

            return new_url

        except Exception as e:
            print(f"❌ Error adding affiliate params to {url}: {e}")
            import traceback
            traceback.print_exc()
            return url

    def get_source_priority(self, source: str) -> int:
        """Получить приоритет источника (меньше = выше приоритет)"""
        config = self.affiliate_configs.get(source)
        return config.get('priority', 999) if config else 999

    def sort_by_priority(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Отсортировать продукты по приоритету источников"""
        def get_priority(product):
            source = self._detect_source(product)
            return self.get_source_priority(source)

        return sorted(products, key=get_priority)


# Глобальный экземпляр
_affiliate_service = None

def get_affiliate_service() -> AffiliateService:
    """Получить глобальный экземпляр AffiliateService"""
    global _affiliate_service
    if _affiliate_service is None:
        _affiliate_service = AffiliateService()
    return _affiliate_service

def build_affiliate_link_safe(product_link: str | None, cfg: dict | None) -> str | None:
    """Безопасная функция для генерации партнерской ссылки с фолбэком"""
    if not product_link:
        return None

    if not cfg:
        return product_link  # Фолбэк к оригинальной ссылке

    try:
        # Попытка определить источник и добавить параметры
        service = get_affiliate_service()
        source = service._detect_source({"link": product_link})

        if not source or source not in service.affiliate_configs:
            return product_link  # Фолбэк к оригинальной ссылке

        affiliate_url = service._add_affiliate_params(product_link, source, "recommendation")
        return affiliate_url

    except Exception as e:
        print(f"⚠️ Error building affiliate link: {e}")
        return product_link  # Фолбэк к оригинальной ссылке


def build_ref_link(product: Dict[str, Any], campaign: str = "recommendation") -> Optional[str]:
    """Удобная функция для генерации партнерской ссылки"""
    try:
        service = get_affiliate_service()
        result = service.build_ref_link(product, campaign)

        # Если результат None, используем фолбэк
        if result is None:
            product_link = product.get('link') or product.get('url')
            if product_link:
                return product_link

        return result

    except Exception as e:
        print(f"⚠️ Error in build_ref_link: {e}")
        # Фолбэк к оригинальной ссылке
        return product.get('link') or product.get('url')
