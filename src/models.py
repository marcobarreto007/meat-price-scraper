from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Store:
    id: str
    name: str
    base_url: str
    scraper_type: str  # 'api' or 'playwright'
    active: bool = True


@dataclass
class StoreBranch:
    store_id: str
    external_id: str
    name: str
    address: str
    postal_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    id: Optional[int] = None


@dataclass
class Product:
    slug: str
    name_en: str
    aliases: dict[str, list[str]] = field(default_factory=dict)
    id: Optional[int] = None


@dataclass
class Price:
    product_slug: str
    store_id: str
    price_cad: float
    unit_price: Optional[float] = None
    unit_type: str = "kg"
    package_size: Optional[str] = None
    brand: Optional[str] = None
    is_on_sale: bool = False
    original_price: Optional[float] = None
    url: Optional[str] = None
    branch_name: Optional[str] = None
    branch_id: Optional[int] = None
    product_name: Optional[str] = None
    scraped_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class ScrapeResult:
    store_id: str
    store_name: str
    prices: list[Price] = field(default_factory=list)
    error: Optional[str] = None
    duration_ms: float = 0.0

    @classmethod
    def empty(cls, store_id: str, store_name: str = "", error: str = "") -> "ScrapeResult":
        return cls(store_id=store_id, store_name=store_name, error=error)
