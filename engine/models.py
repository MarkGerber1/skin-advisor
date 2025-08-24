from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, HttpUrl


Undertone = Literal["cool", "warm", "neutral", "olive"]
Finish = Literal["matte", "natural", "dewy", "satin", "shimmer"]


class Shade(BaseModel):
    name: str
    code: Optional[str] = None
    undertone: Optional[Undertone] = None
    color_family: Optional[str] = None


class Product(BaseModel):
    id: str
    brand: str
    line: Optional[str] = None
    name: str
    category: str
    subcategory: Optional[str] = None
    texture: Optional[str] = None
    finish: Optional[Finish] = None
    shade: Optional[Shade] = None
    volume_ml: Optional[float] = None
    weight_g: Optional[float] = None
    spf: Optional[int] = None
    actives: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    price: Optional[float] = None
    price_currency: Optional[str] = None
    link: Optional[HttpUrl] = None
    in_stock: Optional[bool] = None
    source: Optional[str] = None


class UserProfile(BaseModel):
    # Палитра
    undertone: Optional[Undertone] = None
    season: Optional[str] = None
    season_subtype: Optional[str] = None
    value: Optional[str] = None
    chroma: Optional[str] = None
    contrast: Optional[str] = None
    eye_color: Optional[str] = None
    hair_depth: Optional[str] = None
    # Уход
    skin_type: Optional[Literal["dry", "oily", "combo", "sensitive", "normal"]] = None
    concerns: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)








