"""
FastAPI web server for MeatPrice Tracker.
Provides REST API and serves the bilingual web interface.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.db import get_db, init_db, get_price_history, get_latest_prices
from src.products import PRODUCTS_SEED
from web.i18n import get_translation, get_product_names, LangCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
WEB_DIR = BASE_DIR / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

# Templates and static files
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting MeatPrice Tracker API...")
    db = await get_db()
    await init_db(db)
    await db.close()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down MeatPrice Tracker API...")


app = FastAPI(
    title="MeatPrice Tracker API",
    description="Bilingual (EN/FR) meat price comparison API for Montreal",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Helper functions
def get_lang_from_request(request: Request) -> LangCode:
    """Extract language preference from request (cookie, header, or default)."""
    lang_cookie = request.cookies.get("lang")
    if lang_cookie in ("en", "fr"):
        return lang_cookie

    accept_lang = request.headers.get("accept-language", "")
    if "fr" in accept_lang.lower():
        return "fr"

    return "en"


# Routes - Pages
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Home page."""
    lang = get_lang_from_request(request)
    t = get_translation(lang)
    
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "t": t,
            "current_lang": lang,
            "page": "home",
        }
    )


@app.get("/products", response_class=HTMLResponse)
async def products_page(request: Request):
    """Products page with current prices."""
    lang = get_lang_from_request(request)
    t = get_translation(lang)
    product_names = get_product_names(lang)
    
    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={
            "t": t,
            "current_lang": lang,
            "page": "products",
            "product_names": product_names,
        }
    )


@app.get("/stores", response_class=HTMLResponse)
async def stores_page(request: Request):
    """Stores page."""
    lang = get_lang_from_request(request)
    t = get_translation(lang)
    
    return templates.TemplateResponse(
        request=request,
        name="stores.html",
        context={
            "t": t,
            "current_lang": lang,
            "page": "stores",
        }
    )


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """Price history page."""
    lang = get_lang_from_request(request)
    t = get_translation(lang)
    product_names = get_product_names(lang)
    
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "t": t,
            "current_lang": lang,
            "page": "history",
            "product_names": product_names,
        }
    )


# API Routes
@app.get("/api/products")
async def api_get_products(lang: Annotated[LangCode, Query()] = "en"):
    """Get list of tracked products."""
    product_names = get_product_names(lang)
    return {
        "products": [
            {
                "slug": p["slug"],
                "name": product_names.get(p["slug"], p["slug"]),
            }
            for p in PRODUCTS_SEED
        ]
    }


@app.get("/api/prices")
async def api_get_prices(
    product: Annotated[str | None, Query()] = None,
    store: Annotated[str | None, Query()] = None,
    lang: Annotated[LangCode, Query()] = "en",
):
    """Get current prices, optionally filtered by product and store."""
    db = await get_db()
    try:
        prices = await get_latest_prices(
            db,
            product_slug=product,
            store_id=store,
            max_age_hours=72,
        )
        
        product_names = get_product_names(lang)
        
        # Format response
        formatted = []
        for p in prices:
            formatted.append({
                "id": p["id"],
                "product_slug": p["product_slug"],
                "product_name": product_names.get(p["product_slug"], p.get("product_name", "")),
                "store_id": p["store_id"],
                "store_name": p.get("store_name", ""),
                "price_cad": p["price_cad"],
                "unit_price": p.get("unit_price"),
                "unit_type": p.get("unit_type", "kg"),
                "package_size": p.get("package_size"),
                "brand": p.get("brand"),
                "is_on_sale": bool(p.get("is_on_sale", False)),
                "original_price": p.get("original_price"),
                "url": p.get("url"),
                "scraped_at": p.get("scraped_at"),
            })
        
        return {"prices": formatted, "count": len(formatted)}
    finally:
        await db.close()


@app.get("/api/history/{product_slug}")
async def api_get_history(
    product_slug: str,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    lang: Annotated[LangCode, Query()] = "en",
):
    """Get price history for a specific product."""
    db = await get_db()
    try:
        prices = await get_price_history(db, product_slug, days=days)
        
        product_names = get_product_names(lang)
        
        formatted = []
        for p in prices:
            formatted.append({
                "id": p["id"],
                "product_slug": p["product_slug"],
                "product_name": product_names.get(p["product_slug"], p.get("product_name", "")),
                "store_id": p["store_id"],
                "store_name": p.get("store_name", ""),
                "price_cad": p["price_cad"],
                "unit_price": p.get("unit_price"),
                "is_on_sale": bool(p.get("is_on_sale", False)),
                "scraped_at": p.get("scraped_at"),
            })
        
        return {
            "product_slug": product_slug,
            "product_name": product_names.get(product_slug, product_slug),
            "days": days,
            "prices": formatted,
            "count": len(formatted),
        }
    finally:
        await db.close()


@app.get("/api/stores")
async def api_get_stores(lang: Annotated[LangCode, Query()] = "en"):
    """Get list of participating stores."""
    stores = [
        {"id": "maxi", "name": "Maxi" if lang == "en" else "Maxi"},
        {"id": "costco", "name": "Costco"},
        {"id": "metro", "name": "Metro"},
        {"id": "iga", "name": "IGA"},
        {"id": "walmart", "name": "Walmart"},
        {"id": "provigo", "name": "Provigo"},
        {"id": "super_c", "name": "Super C"},
        {"id": "adonis", "name": "Adonis"},
        {"id": "mayrand", "name": "Mayrand"},
    ]
    return {"stores": stores}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
