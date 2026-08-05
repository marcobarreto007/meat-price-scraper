# 🥩 MeatPrice Tracker

**The world's best bilingual meat price aggregator for Montreal, Quebec.**

Find the best prices on chicken breast, picanha, filet mignon and more across all major grocery stores in the Greater Montreal area.

## 🌍 Bilingual (EN/FR)

Fully localized in English and French for all Quebecers.

- **English**: MeatPrice Tracker
- **Français**: SuiviPrix Viandes

## ✨ Features

- **Real-Time Prices** - Always up-to-date from public flyers and store APIs
- **Multi-Store Coverage** - Maxi, Costco, Metro, IGA, Walmart, Provigo, Super C, Adonis, Mayrand
- **Price History** - Track price trends over 7, 30, or 90 days
- **Bilingual Interface** - Switch between English and French instantly
- **Modern Web UI** - Beautiful, responsive design that works on any device
- **REST API** - Full JSON API for developers
- **50km Radius** - Covers the entire Greater Montreal area

## 🚀 Quick Start

### Install Dependencies

```bash
pip install -e ".[dev]"
```

### Run the Web Server

```bash
python -m uvicorn web.server:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in your browser.

### CLI Usage

```bash
# Scrape current prices
python -m src.main scrape

# Filter by product
python -m src.main scrape --products picanha,chicken_breast

# View as JSON
python -m src.main scrape --output json

# Check price history
python -m src.main history --product picanha --days 30
```

## 📊 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Home page (EN/FR based on cookie/header) |
| `GET /products` | Current prices by product |
| `GET /stores` | List of participating stores |
| `GET /history` | Price history tracker |
| `GET /api/products?lang=en\|fr` | Products list (JSON) |
| `GET /api/prices?product=X&lang=en\|fr` | Current prices (JSON) |
| `GET /api/history/{slug}?days=30&lang=en\|fr` | Price history (JSON) |
| `GET /api/stores?lang=en\|fr` | Store list (JSON) |
| `GET /health` | Health check |

## 🏪 Covered Stores

- **Maxi** - Quebec's largest supermarket chain
- **Costco** - Wholesale warehouse club
- **Metro** - Grocery and pharmacy
- **IGA** - Independent grocers
- **Walmart** - Big box retailer
- **Provigo** - Quebec grocery chain
- **Super C** - Discount groceries
- **Adonis** - Mediterranean specialty
- **Mayrand** - Local butcher

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, FastAPI, asyncio, aiohttp
- **Database**: SQLite with aiosqlite
- **Scraping**: Flipp API (public), Playwright (for some stores)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Styling**: Custom CSS with CSS variables
- **i18n**: Built-in translation system

## 📁 Project Structure

```
/workspace
├── src/
│   ├── main.py          # CLI entry point
│   ├── db.py            # Database layer
│   ├── models.py        # Data models
│   ├── products.py      # Product definitions
│   ├── reporter.py      # Output formatting
│   └── scrapers/
│       ├── flipp.py     # Flipp API scraper
│       ├── maxi.py      # Maxi/PC Express
│       └── costco.py    # Costco automation
├── web/
│   ├── server.py        # FastAPI web server
│   ├── i18n.py          # Translations (EN/FR)
│   ├── templates/       # HTML templates
│   └── static/
│       ├── css/         # Stylesheets
│       └── js/          # Client-side JS
├── tests/               # Test suite
└── cache/               # SQLite database & cache
```

## 🎯 Mission

Help everyone in Montreal find the best meat prices, regardless of language. No hidden fees, no subscriptions—just free, open access to grocery price data.

## 📝 License

Open source. Use freely for personal or commercial purposes.

---

**Built with ❤️ for Montreal's foodie community**
