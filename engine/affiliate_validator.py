"""
🔗 Affiliate Validator - Проверка партнерских ссылок и монетизации
Обеспечивает 100% покрытие всех buy_url партнерскими метками
"""

import urllib.parse
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from config.env import get_settings

@dataclass
class AffiliateCheckResult:
    """Результат проверки партнерской ссылки"""
    original_url: str
    affiliate_url: Optional[str]
    has_affiliate: bool
    affiliate_tag: Optional[str]
    is_valid: bool
    issues: List[str]

class AffiliateValidator:
    """Валидатор партнерских ссылок для монетизации"""
    
    def __init__(self):
        self.settings = get_settings()
        self.expected_affiliate_tag = self.settings.partner_code
        
        # Список партнерских параметров для проверки
        self.affiliate_params = [
            'aff', 'affiliate', 'partner', 'ref', 'utm_source', 
            'utm_campaign', 'tag', 'aff_id', 'partner_id'
        ]
    
    def validate_url(self, original_url: str, affiliate_url: Optional[str]) -> AffiliateCheckResult:
        """Проверяет корректность партнерской ссылки"""
        
        issues = []
        has_affiliate = False
        affiliate_tag = None
        is_valid = True
        
        if not original_url:
            issues.append("Отсутствует оригинальная ссылка")
            is_valid = False
        
        if not affiliate_url:
            issues.append("Отсутствует партнерская ссылка")
            is_valid = False
            return AffiliateCheckResult(
                original_url=original_url or "",
                affiliate_url=None,
                has_affiliate=False,
                affiliate_tag=None,
                is_valid=False,
                issues=issues
            )
        
        # Парсим URL и параметры
        try:
            parsed = urllib.parse.urlparse(affiliate_url)
            params = urllib.parse.parse_qs(parsed.query)
            
            # Проверяем наличие партнерских параметров
            for param_name in self.affiliate_params:
                if param_name in params:
                    has_affiliate = True
                    affiliate_tag = params[param_name][0] if params[param_name] else None
                    break
            
            if not has_affiliate:
                issues.append("Партнерский параметр не найден")
                is_valid = False
            
            # Проверяем корректность тега
            if affiliate_tag and affiliate_tag != self.expected_affiliate_tag:
                issues.append(f"Неожиданный affiliate tag: {affiliate_tag} (ожидался: {self.expected_affiliate_tag})")
                # Не критично, может быть разные теги для разных источников
            
            # Проверяем что ссылка не битая
            if not parsed.netloc:
                issues.append("Некорректный домен в партнерской ссылке")
                is_valid = False
                
        except Exception as e:
            issues.append(f"Ошибка парсинга URL: {e}")
            is_valid = False
        
        return AffiliateCheckResult(
            original_url=original_url,
            affiliate_url=affiliate_url,
            has_affiliate=has_affiliate,
            affiliate_tag=affiliate_tag,
            is_valid=is_valid,
            issues=issues
        )
    
    def validate_product_dict(self, product_dict: Dict[str, Any]) -> AffiliateCheckResult:
        """Проверяет партнерскую ссылку в словаре продукта"""
        
        original_link = product_dict.get('link')
        affiliate_link = product_dict.get('ref_link')
        
        return self.validate_url(original_link, affiliate_link)
    
    def validate_selection_results(self, selection_results: Dict[str, Any]) -> Dict[str, List[AffiliateCheckResult]]:
        """Проверяет все партнерские ссылки в результатах подбора"""
        
        validation_results = {}
        
        # Проверяем skincare секции
        if 'skincare' in selection_results:
            skincare_results = []
            for category, products in selection_results['skincare'].items():
                for product in products:
                    result = self.validate_product_dict(product)
                    result.product_id = product.get('id', 'unknown')
                    result.category = category
                    skincare_results.append(result)
            validation_results['skincare'] = skincare_results
        
        # Проверяем makeup секции
        if 'makeup' in selection_results:
            makeup_results = []
            for section, products in selection_results['makeup'].items():
                for product in products:
                    result = self.validate_product_dict(product)
                    result.product_id = product.get('id', 'unknown')
                    result.section = section
                    makeup_results.append(result)
            validation_results['makeup'] = makeup_results
        
        return validation_results
    
    def get_monetization_report(self, validation_results: Dict[str, List[AffiliateCheckResult]]) -> Dict[str, Any]:
        """Генерирует отчет о монетизации"""
        
        total_products = 0
        valid_affiliates = 0
        missing_affiliates = 0
        broken_links = 0
        
        issues_summary = []
        
        for category, results in validation_results.items():
            for result in results:
                total_products += 1
                
                if result.is_valid and result.has_affiliate:
                    valid_affiliates += 1
                elif not result.has_affiliate:
                    missing_affiliates += 1
                    issues_summary.append(f"{category}: {getattr(result, 'product_id', 'unknown')} - нет affiliate")
                else:
                    broken_links += 1
                    issues_summary.append(f"{category}: {getattr(result, 'product_id', 'unknown')} - битая ссылка")
        
        monetization_rate = (valid_affiliates / total_products * 100) if total_products > 0 else 0
        
        return {
            "total_products": total_products,
            "valid_affiliates": valid_affiliates,
            "missing_affiliates": missing_affiliates,
            "broken_links": broken_links,
            "monetization_rate": monetization_rate,
            "issues": issues_summary[:10],  # Top 10 issues
            "status": "PASS" if monetization_rate >= 95 else "FAIL",
            "expected_affiliate_tag": self.expected_affiliate_tag
        }
    
    def standardize_affiliate_configs(self) -> Dict[str, str]:
        """Возвращает стандартизированные конфигурации для всех handlers"""
        
        return {
            "PARTNER_CODE": self.settings.partner_code,
            "AFFILIATE_TAG": self.settings.affiliate_tag,
            "REDIRECT_BASE": self.settings.redirect_base,
            "recommendation": "Использовать get_settings().partner_code во всех handlers"
        }


def run_affiliate_validation_test():
    """Запускает полную проверку партнерских ссылок"""
    
    print("🔗 AFFILIATE VALIDATION TEST")
    print("=" * 50)
    
    validator = AffiliateValidator()
    
    # Тест 1: Проверка функции _with_affiliate
    print("\n1. Testing _with_affiliate function:")
    from engine.selector import _with_affiliate
    
    test_cases = [
        ("https://example.com/product", "TEST123", None),
        ("https://shop.com/item?existing=param", "TEST123", None),
        ("https://example.com/product", "TEST123", "https://redirect.com"),
    ]
    
    for original, partner, redirect in test_cases:
        result = _with_affiliate(original, partner, redirect)
        validation = validator.validate_url(original, result)
        
        status = "✅" if validation.is_valid and validation.has_affiliate else "❌"
        print(f"  {status} {result}")
    
    # Тест 2: Проверка конфигурации
    print(f"\n2. Configuration check:")
    config = validator.standardize_affiliate_configs()
    print(f"  Partner code: {config['PARTNER_CODE']}")
    print(f"  Affiliate tag: {config['AFFILIATE_TAG']}")
    print(f"  Redirect base: {config['REDIRECT_BASE']}")
    
    # Тест 3: Генерация тестовых данных
    print(f"\n3. Testing with selector:")
    try:
        from engine.selector import SelectorV2
        from engine.models import UserProfile
        from engine.catalog_store import CatalogStore
        
        # Загружаем каталог
        catalog_store = CatalogStore()
        catalog = catalog_store.get_catalog()
        
        if catalog:
            selector = SelectorV2()
            profile = UserProfile(
                user_id=12345,
                undertone="warm",
                season="autumn",
                contrast="medium",
                skin_type="dry",
                concerns=[]
            )
            
            # Генерируем подбор
            results = selector.select_products_v2(
                profile=profile,
                catalog=catalog[:10],  # Тестируем первые 10 продуктов
                partner_code=validator.expected_affiliate_tag,
                redirect_base=validator.settings.redirect_base
            )
            
            # Проверяем результаты
            validation_results = validator.validate_selection_results(results)
            report = validator.get_monetization_report(validation_results)
            
            print(f"  Total products: {report['total_products']}")
            print(f"  Monetization rate: {report['monetization_rate']:.1f}%")
            print(f"  Status: {report['status']}")
            
            if report['issues']:
                print(f"  Issues found: {len(report['issues'])}")
                for issue in report['issues'][:3]:
                    print(f"    - {issue}")
        else:
            print("  ⚠️ No catalog loaded, skipping selector test")
            
    except Exception as e:
        print(f"  ❌ Selector test failed: {e}")
    
    print(f"\n🎯 VALIDATION COMPLETE")
    return validator


if __name__ == "__main__":
    validator = run_affiliate_validation_test()
    
    # Дополнительный тест конкретного URL
    print(f"\n🔧 MANUAL URL TEST:")
    test_url = "https://example.com/product"
    affiliate_url = validator.validate_url(test_url, test_url + "?aff=" + validator.expected_affiliate_tag)
    
    print(f"Original: {test_url}")
    print(f"Affiliate: {affiliate_url.affiliate_url}")
    print(f"Valid: {affiliate_url.is_valid}")
    print(f"Has affiliate: {affiliate_url.has_affiliate}")
    if affiliate_url.issues:
        print(f"Issues: {affiliate_url.issues}")

