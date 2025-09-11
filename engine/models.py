from __future__ import annotations

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


# Engine v2 Types
class Undertone(str, Enum):
    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


class Fitzpatrick(str, Enum):
    I = "I"
    II = "II"
    III = "III"
    IV = "IV"
    V = "V"
    VI = "VI"


class SkinType(str, Enum):
    DRY = "dry"
    NORMAL = "normal"
    COMBO = "combo"
    OILY = "oily"


class Sensitivity(str, Enum):
    LOW = "low"
    MID = "mid"
    HIGH = "high"


class Contrast(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EyeColor(str, Enum):
    BROWN = "brown"
    GREEN = "green"
    BLUE = "blue"
    GRAY = "gray"
    HAZEL = "hazel"
    OTHER = "other"


class Sex(str, Enum):
    FEMALE = "female"
    MALE = "male"
    OTHER = "other"


class ClimateProfile(BaseModel):
    humidity: Literal["low", "medium", "high", "unknown"] = "unknown"
    uv_index: Optional[float] = Field(None, ge=0, le=15)


class UserProfile(BaseModel):
    """Engine v2 User Profile with extended schemas"""

    # Basic info
    user_id: int
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    sex: Optional[Sex] = None
    pregnant_or_lactating: Optional[bool] = None

    # Sensitivity & Allergies
    sensitivity: Optional[Sensitivity] = None
    allergies: List[str] = Field(default_factory=list)  # fragrance, alcohol_denat, e.oils
    triggers: List[str] = Field(default_factory=list)  # heat, sweat, stress
    climate_profile: Optional[ClimateProfile] = None

    # Skin (Fitzpatrick + Baumann + Traditional)
    fitzpatrick: Optional[Fitzpatrick] = None
    baumann: Optional[str] = Field(None, pattern=r"^[OD][SR][PN][WT]$")  # 16 types
    skin_type: Optional[SkinType] = None
    dehydrated: Optional[bool] = None
    concerns: List[str] = Field(default_factory=list)  # blackheads, acne, pigmentation, etc.
    uses_retinoids: Optional[bool] = None

    # Color Palette
    undertone: Optional[Undertone] = Undertone.UNKNOWN
    season: Optional[Season] = None
    season_alt: Optional[Season] = None
    contrast: Optional[Contrast] = None
    hair_color: Optional[str] = None
    brow_color: Optional[str] = None
    eye_color: Optional[EyeColor] = None


class Product(BaseModel):
    """Engine v2 Product with extended properties"""

    # Core identification
    key: str = Field(..., alias="id")  # Backward compatibility
    title: str = Field(..., alias="name")  # Backward compatibility
    brand: str
    category: str  # DecorCategory | CareCategory
    subcategory: Optional[str] = None

    # Pricing & Availability
    price: Optional[float] = Field(None, ge=0)
    display_price: Optional[str] = None
    in_stock: bool = False
    buy_url: Optional[str] = None
    source: Optional[Literal["gp", "gp_like", "wb", "ozon"]] = None

    # Visual & Meta
    image_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    allergenic_flags: List[str] = Field(default_factory=list)

    # Formula & Properties
    actives: List[str] = Field(default_factory=list)
    ph_range: Optional[str] = None
    texture: Optional[str] = None
    finish: Optional[str] = None
    spf: Optional[int] = None
    volume_ml: Optional[float] = None
    weight_g: Optional[float] = None

    # Color properties (for makeup)
    shade_name: Optional[str] = None
    undertone_match: Optional[Undertone] = None
    coverage: Optional[Literal["light", "medium", "full"]] = None

    # Legacy compatibility
    id: Optional[str] = Field(None, alias="key")
    name: Optional[str] = Field(None, alias="title")
    link: Optional[str] = Field(None, alias="buy_url")


class CartItem(BaseModel):
    """Shopping cart item"""

    product_key: str
    quantity: int = 1
    added_at: Optional[str] = None


class RoutineStep(BaseModel):
    """Single step in skincare routine"""

    order: int
    product_key: str
    instructions: Optional[str] = None
    frequency: Optional[str] = None  # daily, 2-3x/week, etc.


class Routine(BaseModel):
    """Complete skincare routine"""

    name: str
    type: Literal["AM", "PM", "weekly", "SOS"]
    steps: List[RoutineStep] = Field(default_factory=list)
    notes: Optional[str] = None


class ReportData(BaseModel):
    """Data for PDF report generation"""

    user_profile: UserProfile
    skincare_products: List[Product] = Field(default_factory=list)
    makeup_products: List[Product] = Field(default_factory=list)
    routines: List[Routine] = Field(default_factory=list)
    recommendations_text: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


# Legacy type aliases for backward compatibility
Shade = Dict[str, Any]  # Simplified for now
DecorCategory = str
CareCategory = str
