"""
Services package for the skincare chatbot.

This package contains various service modules for business logic:
- cart_service: Shopping cart management
"""

__version__ = "1.0.0"

# Import unified cart store
try:
    from .cart_store import get_cart_store, CartStore, CartItem
    CART_SERVICE_AVAILABLE = True
    print("[OK] Unified CartStore loaded")
except ImportError as e:
    print(f"[WARNING] services.cart_store not available: {e}")
    CART_SERVICE_AVAILABLE = False
    # Define stubs for missing functions
    def get_cart_store():
        return None
    class CartStore:
        pass
    class CartItem:
        pass

# Import affiliate service
try:
    from .affiliates import get_affiliate_service, build_ref_link, AffiliateService
    AFFILIATE_SERVICE_AVAILABLE = True
    print("[OK] Affiliate service loaded")
except ImportError as e:
    print(f"[WARNING] services.affiliates not available: {e}")
    AFFILIATE_SERVICE_AVAILABLE = False
    # Define stubs for missing functions
    def get_affiliate_service():
        return None
    def build_ref_link(product, campaign="recommendation"):
        return product.get('link') or product.get('url')
    class AffiliateService:
        pass

