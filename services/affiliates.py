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
            except Exception as e:
                print(f"⚠️ Could not load settings: {e}, using defaults")
                self.settings = None
        else:
            self.settings = None

        # Create mock settings if needed
        if self.settings is None:
            class MockSettings:
                goldapple_partner_code = 'BEAUTYCARE'
                ru_official_partner_code = 'BEAUTYCARE_RU'
                ru_marketplace_partner_code = 'BEAUTYCARE_MP'
                intl_partner_code = 'BEAUTYCARE_INT'
            self.settings = MockSettings()

        # Конфигурация партнерских параметров для разных источников
        self.affiliate_configs = {
            'goldapple': {
                'aff_param': 'partner',
                'campaign_param': 'utm_campaign',
                'source_param': 'utm_source',
                'medium_param': 'utm_medium',
                'partner_code': getattr(self.settings, 'goldapple_partner_code', 'BEAUTYCARE'),
                'priority': 1
            },
            'ru_official': {
                'aff_param': 'affiliate',
                'campaign_param': 'campaign',
                'source_param': 'source',
                'medium_param': 'medium',
                'partner_code': getattr(self.settings, 'ru_official_partner_code', 'BEAUTYCARE_RU'),
                'priority': 2
            },
            'ru_marketplace': {
                'aff_param': 'partner',
                'campaign_param': 'campaign',
                'source_param': 'ref',
                'medium_param': 'medium',
                'partner_code': getattr(self.settings, 'ru_marketplace_partner_code', 'BEAUTYCARE_MP'),
                'priority': 3
            },
            'intl_authorized': {
                'aff_param': 'aff',
                'campaign_param': 'campaign',
                'source_param': 'source',
                'medium_param': 'medium',
                'partner_code': getattr(self.settings, 'intl_partner_code', 'BEAUTYCARE_INT'),
                'priority': 4
            },
            'default': {
                'aff_param': 'partner',
                'campaign_param': 'utm_campaign',
                'source_param': 'utm_source',
                'medium_param': 'utm_medium',
                'partner_code': 'BEAUTYCARE_DEFAULT',
                'priority': 5
            }
        }

    def build_ref_link(self, product: Dict[str, Any], campaign: str = "recommendation") -> Optional[str]:
        """Создать партнерскую ссылку для продукта

        Args:
            product: Словарь с данными продукта
            campaign: Кампания для UTM меток

        Returns:
            Партнерская ссылка или None если не удалось создать
        """
        try:
            # Получаем оригинальную ссылку
            original_link = product.get('link') or product.get('url')
            if not original_link:
                print(f"⚠️ No link found for product {product.get('id', 'unknown')}")
                return None

            # Если уже есть ref_link, используем его
            if product.get('ref_link'):
                return product['ref_link']

            # Определяем источник по ссылке или названию
            source = self._detect_source(product)
            print(f"🔍 Detected source for {product.get('id', 'unknown')}: {source}")

            # Проверяем конфигурацию
            if not self.affiliate_configs:
                print(f"⚠️ No affiliate configs available, returning original link")
                print(f"🔗 affiliate_link_built: product={product.get('id', 'unknown')}, source=None, used_fallback=True")
                return original_link

            # Проверяем источник
            if not source or source not in self.affiliate_configs:
                # Пробуем default конфигурацию
                if 'default' in self.affiliate_configs:
                    source = 'default'
                    print(f"🔄 Using default affiliate config for {product.get('id', 'unknown')}")
                else:
                    print(f"⚠️ No affiliate config for source {source}, returning original link")
                    print(f"🔗 affiliate_link_built: product={product.get('id', 'unknown')}, source={source}, used_fallback=True")
                    return original_link

            # Генерируем партнерскую ссылку
            affiliate_url = self._add_affiliate_params(original_link, source, campaign)
            print(f"✅ Generated affiliate link: {affiliate_url[:50]}...")
            print(f"🔗 affiliate_link_built: product={product.get('id', 'unknown')}, source={source}, used_fallback=False")

            return affiliate_url

        except Exception as e:
            print(f"❌ Error building affiliate link for product {product.get('id', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
            # Возвращаем оригинальную ссылку в случае ошибки
            return product.get('link') or product.get('url')

    def _detect_source(self, product: Dict[str, Any]) -> Optional[str]:
        """Определить источник продукта"""
        # Проверяем по ссылке
        link = product.get('link') or product.get('url', '')
        if link:
            link_lower = link.lower()
            if 'goldapple' in link_lower:
                return 'goldapple'
            elif 'wildberries' in link_lower or 'ozon' in link_lower:
                return 'ru_marketplace'
            elif 'official' in link_lower or 'brand' in link_lower:
                return 'ru_official'
            elif 'sephora' in link_lower or 'amazon' in link_lower:
                return 'intl_authorized'

        # Проверяем по названию/бренду
        brand = product.get('brand', '').lower()
        name = product.get('name', '').lower()

        if 'goldapple' in brand or 'goldapple' in name:
            return 'goldapple'
        elif any(x in brand or x in name for x in ['wildberries', 'ozon', 'marketplace']):
            return 'ru_marketplace'
        elif any(x in brand or x in name for x in ['official', 'brand']):
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
