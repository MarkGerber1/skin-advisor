"""
Services package for the skincare chatbot.

This package contains various service modules for business logic:
- cart_service: Shopping cart management
"""

__version__ = "1.0.0"

# Import cart service functions
try:
    from .cart_service import get_cart_service, CartServiceError, CartErrorCode
    CART_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ services.cart_service not available: {e}")
    CART_SERVICE_AVAILABLE = False
    # Define stubs for missing functions
    def get_cart_service():
        return None
    class CartServiceError(Exception):
        pass
    class CartErrorCode:
        pass

