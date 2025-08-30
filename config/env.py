"""
🧴 Skin Advisor Bot - Environment Configuration Module

This module handles all environment variables in a centralized way.
All secrets and configuration should be read from ENV variables only.
"""

import os
from typing import List, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file at module import
load_dotenv()


class TelegramConfig(BaseModel):
    """Telegram Bot Configuration"""
    token: str
    webhook_secret: Optional[str] = None
    webhook_base: Optional[str] = None
    webhook_path: str = "/webhook"
    webapp_port: int = 8080


class PartnerConfig(BaseModel):
    """Partner & Affiliate Configuration"""
    affiliate_tag: str = "skincare_bot"
    partner_code: str = "aff_skincare_bot"
    redirect_base: Optional[str] = None
    deeplink_network: Optional[str] = None
    user_discount: float = 0.05
    owner_commission: float = 0.10


class CatalogConfig(BaseModel):
    """Catalog & Data Configuration"""
    catalog_path: str = "assets/fixed_catalog.yaml"
    cache_enabled: bool = True
    only_in_stock: bool = True


class DatabaseConfig(BaseModel):
    """Database Configuration"""
    url: str = "sqlite:///data/bot.db"


class LoggingConfig(BaseModel):
    """Logging Configuration"""
    level: str = "INFO"
    log_file: str = "logs/bot.log"
    catalog_errors_file: str = "logs/catalog_errors.jsonl"


class AnalyticsConfig(BaseModel):
    """Analytics & Metrics Configuration"""
    enabled: bool = True
    ab_testing: bool = True


class DevelopmentConfig(BaseModel):
    """Development Configuration"""
    debug: bool = False
    development_mode: bool = False


class ExternalAPIsConfig(BaseModel):
    """External APIs Configuration"""
    openai_api_key: Optional[str] = None


class AdminConfig(BaseModel):
    """Admin Configuration"""
    admin_ids: List[int] = []
    owner_id: Optional[int] = None


class Settings(BaseSettings):
    """Main Settings Class - Reads from Environment Variables"""
    
    class Config:
        env_prefix = ""
        case_sensitive = False
    
    # Telegram
    bot_token: str
    webhook_secret: Optional[str] = None
    webhook_base: Optional[str] = None
    webhook_path: str = "/webhook"
    webapp_port: int = 8080
    
    # Partner & Affiliate
    affiliate_tag: str = "skincare_bot"
    partner_code: str = "aff_skincare_bot"
    redirect_base: Optional[str] = None
    deeplink_network: Optional[str] = None
    user_discount: float = 0.05
    owner_commission: float = 0.10
    
    # Catalog & Data
    catalog_path: str = "assets/fixed_catalog.yaml"
    
    # Database
    database_url: str = "sqlite:///data/bot.db"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/bot.log"
    
    # Analytics
    analytics_enabled: bool = True
    ab_testing: bool = True
    
    # Development
    debug: bool = False
    development_mode: bool = False
    
    # External APIs
    openai_api_key: Optional[str] = None
    
    # Admin
    admin_ids: str = ""  # Comma-separated IDs
    owner_id: Optional[int] = None
    
    @property
    def telegram(self) -> TelegramConfig:
        """Get Telegram configuration"""
        return TelegramConfig(
            token=self.bot_token,
            webhook_secret=self.webhook_secret,
            webhook_base=self.webhook_base,
            webhook_path=self.webhook_path,
            webapp_port=self.webapp_port
        )
    
    @property
    def partner(self) -> PartnerConfig:
        """Get Partner configuration"""
        return PartnerConfig(
            affiliate_tag=self.affiliate_tag,
            partner_code=self.partner_code,
            redirect_base=self.redirect_base,
            deeplink_network=self.deeplink_network,
            user_discount=self.user_discount,
            owner_commission=self.owner_commission
        )
    
    @property
    def catalog(self) -> CatalogConfig:
        """Get Catalog configuration"""
        return CatalogConfig(
            catalog_path=self.catalog_path
        )
    
    @property
    def database(self) -> DatabaseConfig:
        """Get Database configuration"""
        return DatabaseConfig(url=self.database_url)
    
    @property
    def logging(self) -> LoggingConfig:
        """Get Logging configuration"""
        return LoggingConfig(
            level=self.log_level,
            log_file=self.log_file
        )
    
    @property
    def analytics(self) -> AnalyticsConfig:
        """Get Analytics configuration"""
        return AnalyticsConfig(
            enabled=self.analytics_enabled,
            ab_testing=self.ab_testing
        )
    
    @property
    def development(self) -> DevelopmentConfig:
        """Get Development configuration"""
        return DevelopmentConfig(
            debug=self.debug,
            development_mode=self.development_mode
        )
    
    @property
    def external_apis(self) -> ExternalAPIsConfig:
        """Get External APIs configuration"""
        return ExternalAPIsConfig(
            openai_api_key=self.openai_api_key
        )
    
    @property
    def admin_list(self) -> List[int]:
        """Parse admin IDs from comma-separated string"""
        if not self.admin_ids:
            return []
        try:
            return [int(uid.strip()) for uid in self.admin_ids.split(",") if uid.strip()]
        except ValueError:
            return []


# Global settings instance
def get_settings() -> Settings:
    """Get settings instance (singleton pattern)"""
    try:
        return Settings()
    except Exception as e:
        raise RuntimeError(f"Failed to load environment configuration: {e}")


# Convenience function for backwards compatibility
def load_env():
    """Load and validate environment configuration"""
    settings = get_settings()
    
    # Validate critical settings
    if not settings.bot_token:
        raise ValueError("BOT_TOKEN is required")
    
    # Validate paths exist
    import os
    if not os.path.exists(os.path.dirname(settings.catalog_path)):
        os.makedirs(os.path.dirname(settings.catalog_path), exist_ok=True)
    
    if not os.path.exists(os.path.dirname(settings.log_file)):
        os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    
    return settings


if __name__ == "__main__":
    # Test configuration loading
    try:
        settings = get_settings()
        print("✅ Configuration loaded successfully!")
        print(f"🤖 Bot Token: {'*' * 20}...{settings.bot_token[-4:] if len(settings.bot_token) > 4 else 'NOT_SET'}")
        print(f"📁 Catalog Path: {settings.catalog_path}")
        print(f"🏷️ Affiliate Tag: {settings.affiliate_tag}")
        print(f"💾 Database: {settings.database_url}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")

