"""
Internationalization (i18n) module for MeatPrice Tracker.
Supports English and French translations.
"""

from dataclasses import dataclass
from typing import Literal

LangCode = Literal["en", "fr"]


@dataclass
class Translations:
    """Translation strings for the application."""
    
    # App info
    app_name: str = "MeatPrice Tracker"
    tagline: str = "Find the best meat prices in Montreal"
    page_title: str = "Home"
    
    # Navigation
    nav_home: str = "Home"
    nav_products: str = "Products"
    nav_stores: str = "Stores"
    nav_history: str = "History"
    
    # Home page
    home_hero_title: str = "Find the Best Meat Prices in Montreal"
    home_hero_subtitle: str = "Compare prices from Maxi, Costco, Metro, IGA, Walmart and more"
    home_cta_button: str = "View Current Deals"
    home_features_title: str = "Why Use MeatPrice Tracker?"
    home_feature_1_title: str = "Real-Time Prices"
    home_feature_1_desc: str = "Always up-to-date prices from all major grocery stores"
    home_feature_2_title: str = "Bilingual"
    home_feature_2_desc: str = "Available in English and French for all Quebecers"
    home_feature_3_title: str = "Price History"
    home_feature_3_desc: str = "Track price trends over time to find the best deals"
    home_feature_4_title: str = "Free & Open"
    home_feature_4_desc: str = "Completely free to use with no hidden fees"
    
    # Products page
    products_title: str = "Meat Products"
    products_subtitle: str = "Current prices for popular cuts"
    product_chicken_breast: str = "Chicken Breast"
    product_picanha: str = "Picanha (Top Sirloin Cap)"
    product_filet_mignon: str = "Filet Mignon"
    product_beef: str = "Beef"
    product_pork: str = "Pork"
    product_lamb: str = "Lamb"
    btn_refresh: str = "Refresh Prices"
    btn_last_updated: str = "Last updated"
    
    # Price table headers
    th_rank: str = "#"
    th_store_product: str = "Store / Product"
    th_price_kg: str = "Price/kg"
    th_price: str = "Price"
    th_sale: str = "Sale"
    sale_yes: str = "YES"
    no_results: str = "No results found"
    
    # Stores page
    stores_title: str = "Participating Stores"
    stores_subtitle: str = "We track prices from these retailers"
    
    # History page
    history_title: str = "Price History"
    history_subtitle: str = "Track price changes over time"
    history_select_product: str = "Select Product"
    history_select_days: str = "Time Period"
    days_7: str = "7 days"
    days_30: str = "30 days"
    days_90: str = "90 days"
    btn_view_history: str = "View History"
    history_date: str = "Date"
    history_store: str = "Store"
    history_product: str = "Product"
    
    # Footer
    footer_tagline: str = "Helping you save on groceries since 2025"
    footer_note: str = "Prices are updated regularly from public flyers and store APIs"
    
    # Common
    loading: str = "Loading..."
    error: str = "Error"
    close: str = "Close"
    search: str = "Search"
    filter: str = "Filter"
    sort_by: str = "Sort by"
    lowest_price: str = "Lowest Price"
    highest_price: str = "Highest Price"
    nearest: str = "Nearest"
    cad_currency: str = "CAD"
    per_kg: str = "/kg"
    each: str = "each"
    
    def get(self, key: str) -> str:
        """Get translation by key dynamically."""
        return getattr(self, key, key)


# English translations
EN = Translations(
    app_name="MeatPrice Tracker",
    tagline="Find the best meat prices in Montreal",
    page_title="Home",
    nav_home="Home",
    nav_products="Products",
    nav_stores="Stores",
    nav_history="History",
    home_hero_title="Find the Best Meat Prices in Montreal",
    home_hero_subtitle="Compare prices from Maxi, Costco, Metro, IGA, Walmart and more",
    home_cta_button="View Current Deals",
    home_features_title="Why Use MeatPrice Tracker?",
    home_feature_1_title="Real-Time Prices",
    home_feature_1_desc="Always up-to-date prices from all major grocery stores",
    home_feature_2_title="Bilingual",
    home_feature_2_desc="Available in English and French for all Quebecers",
    home_feature_3_title="Price History",
    home_feature_3_desc="Track price trends over time to find the best deals",
    home_feature_4_title="Free & Open",
    home_feature_4_desc="Completely free to use with no hidden fees",
    products_title="Meat Products",
    products_subtitle="Current prices for popular cuts",
    product_chicken_breast="Chicken Breast",
    product_picanha="Picanha (Top Sirloin Cap)",
    product_filet_mignon="Filet Mignon",
    product_beef="Beef",
    product_pork="Pork",
    product_lamb="Lamb",
    btn_refresh="Refresh Prices",
    btn_last_updated="Last updated",
    th_rank="#",
    th_store_product="Store / Product",
    th_price_kg="Price/kg",
    th_price="Price",
    th_sale="Sale",
    sale_yes="YES",
    no_results="No results found",
    stores_title="Participating Stores",
    stores_subtitle="We track prices from these retailers",
    history_title="Price History",
    history_subtitle="Track price changes over time",
    history_select_product="Select Product",
    history_select_days="Time Period",
    days_7="7 days",
    days_30="30 days",
    days_90="90 days",
    btn_view_history="View History",
    history_date="Date",
    history_store="Store",
    history_product="Product",
    footer_tagline="Helping you save on groceries since 2025",
    footer_note="Prices are updated regularly from public flyers and store APIs",
    loading="Loading...",
    error="Error",
    close="Close",
    search="Search",
    filter="Filter",
    sort_by="Sort by",
    lowest_price="Lowest Price",
    highest_price="Highest Price",
    nearest="Nearest",
    cad_currency="CAD",
    per_kg="/kg",
    each="each",
)

# French translations
FR = Translations(
    app_name="SuiviPrix Viandes",
    tagline="Trouvez les meilleurs prix de viande à Montréal",
    page_title="Accueil",
    nav_home="Accueil",
    nav_products="Produits",
    nav_stores="Magasins",
    nav_history="Historique",
    home_hero_title="Trouvez les Meilleurs Prix de Viande à Montréal",
    home_hero_subtitle="Comparez les prix de Maxi, Costco, Metro, IGA, Walmart et plus",
    home_cta_button="Voir les Offres",
    home_features_title="Pourquoi Utiliser SuiviPrix Viandes?",
    home_feature_1_title="Prix en Temps Réel",
    home_feature_1_desc="Prix toujours à jour de tous les grands épiciers",
    home_feature_2_title="Bilingue",
    home_feature_2_desc="Disponible en anglais et français pour tous les Québécois",
    home_feature_3_title="Historique des Prix",
    home_feature_3_desc="Suivez l'évolution des prix pour trouver les meilleures offres",
    home_feature_4_title="Gratuit & Ouvert",
    home_feature_4_desc="Complètement gratuit sans frais cachés",
    products_title="Produits de Viande",
    products_subtitle="Prix actuels pour les coupes populaires",
    product_chicken_breast="Poitrine de Poulet",
    product_picanha="Picanha (Couverture de Bifteck)",
    product_filet_mignon="Filet Mignon",
    product_beef="Boeuf",
    product_pork="Porc",
    product_lamb="Agneau",
    btn_refresh="Actualiser les Prix",
    btn_last_updated="Dernière mise à jour",
    th_rank="#",
    th_store_product="Magasin / Produit",
    th_price_kg="Prix/kg",
    th_price="Prix",
    th_sale="Solde",
    sale_yes="OUI",
    no_results="Aucun résultat trouvé",
    stores_title="Magasins Participants",
    stores_subtitle="Nous suivons les prix de ces détaillants",
    history_title="Historique des Prix",
    history_subtitle="Suivez l'évolution des prix dans le temps",
    history_select_product="Sélectionner un Produit",
    history_select_days="Période",
    days_7="7 jours",
    days_30="30 jours",
    days_90="90 jours",
    btn_view_history="Voir l'Historique",
    history_date="Date",
    history_store="Magasin",
    history_product="Produit",
    footer_tagline="Vous aide à économiser sur l'épicerie depuis 2025",
    footer_note="Les prix sont mis à jour régulièrement à partir des circulaires et API publiques",
    loading="Chargement...",
    error="Erreur",
    close="Fermer",
    search="Rechercher",
    filter="Filtrer",
    sort_by="Trier par",
    lowest_price="Prix le plus bas",
    highest_price="Prix le plus élevé",
    nearest="Plus proche",
    cad_currency="CAD",
    per_kg="/kg",
    each="chacun",
)

TRANSLATIONS: dict[LangCode, Translations] = {
    "en": EN,
    "fr": FR,
}


def get_translation(lang: LangCode = "en") -> Translations:
    """Get translations for the specified language."""
    return TRANSLATIONS.get(lang, EN)


def get_product_names(lang: LangCode = "en") -> dict[str, str]:
    """Get product name mappings for the specified language."""
    if lang == "fr":
        return {
            "chicken_breast": "Poitrine de poulet",
            "picanha": "Picanha (Couverture de surlonge)",
            "filet_mignon": "Filet mignon",
            "beef": "Boeuf",
            "pork": "Porc",
            "lamb": "Agneau",
        }
    else:
        return {
            "chicken_breast": "Chicken Breast",
            "picanha": "Picanha (Top Sirloin Cap)",
            "filet_mignon": "Filet Mignon",
            "beef": "Beef",
            "pork": "Pork",
            "lamb": "Lamb",
        }
