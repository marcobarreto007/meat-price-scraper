import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Geo center: Montreal Plateau (H2T 1S8)
CENTER_POSTAL_CODE = os.getenv("CENTER_POSTAL_CODE", "H2T1S8")
CENTER_LAT = float(os.getenv("CENTER_LAT", "45.5225"))
CENTER_LON = float(os.getenv("CENTER_LON", "-73.5940"))
RADIUS_KM = float(os.getenv("RADIUS_KM", "50"))

# Cache
CACHE_DIR = Path(os.getenv("CACHE_DIR", PROJECT_ROOT / "cache"))
DB_PATH = Path(os.getenv("DB_PATH", CACHE_DIR / "prices.db"))

# PC Express (Maxi)
PCEXPRESS_REFRESH_TOKEN = os.getenv("PCEXPRESS_REFRESH_TOKEN", "")
PCEXPRESS_CLIENT_SECRET = os.getenv(
    "PCEXPRESS_CLIENT_SECRET", "C1xujSegT5j3ap3yexJjqhOfELwGKYvz"
)
PCEXPRESS_API_KEY = "C1xujSegT5j3ap3yexJjqhOfELwGKYvz"
PCEXPRESS_API_BASE = "https://api.pcexpress.ca"
PCEXPRESS_TENANT_ID = "ONLINE_GROCERIES"

# Instacart (Costco Same-Day)
INSTACART_BASE = "https://sameday.costco.com"
INSTACART_GRAPHQL = f"{INSTACART_BASE}/graphql"

# Scraper settings
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
CIRCUIT_BREAKER_THRESHOLD = 5
CACHE_TTL_HOURS = 6  # How long cached prices are considered fresh
