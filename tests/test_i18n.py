import pytest
from web.i18n import (
    EN,
    FR,
    TRANSLATIONS,
    LangCode,
    Translations,
    get_product_names,
    get_translation,
)


class TestGetTranslation:
    def test_english_default(self):
        t = get_translation("en")
        assert t.app_name == "MeatPrice Tracker"
        assert t.nav_home == "Home"
        assert t.home_hero_title == "Find the Best Meat Prices in Montreal"

    def test_french(self):
        t = get_translation("fr")
        assert t.app_name == "SuiviPrix Viandes"
        assert t.nav_home == "Accueil"
        assert t.home_hero_title == "Trouvez les Meilleurs Prix de Viande à Montréal"

    def test_invalid_falls_back_to_english(self):
        t = get_translation("pt")  # type: ignore
        assert t.app_name == "MeatPrice Tracker"


class TestTranslationsDataclass:
    def test_get_method(self):
        t = EN
        assert t.get("app_name") == "MeatPrice Tracker"
        assert t.get("nonexistent") == "nonexistent"


class TestProductNames:
    def test_english_names(self):
        names = get_product_names("en")
        assert names["chicken_breast"] == "Chicken Breast"
        assert names["picanha"] == "Picanha (Top Sirloin Cap)"
        assert names["filet_mignon"] == "Filet Mignon"

    def test_french_names(self):
        names = get_product_names("fr")
        assert names["chicken_breast"] == "Poitrine de poulet"
        assert names["picanha"] == "Picanha (Couverture de surlonge)"
        assert names["filet_mignon"] == "Filet mignon"

    def test_defaults_to_english(self):
        names = get_product_names("pt")  # type: ignore
        assert names["chicken_breast"] == "Chicken Breast"


class TestTranslationsKeys:
    def test_all_keys_match_between_en_and_fr(self):
        en_keys = {k for k in dir(EN) if not k.startswith("_") and k != "get"}
        fr_keys = {k for k in dir(FR) if not k.startswith("_") and k != "get"}
        assert en_keys == fr_keys

    def test_both_in_registry(self):
        assert TRANSLATIONS["en"] is EN
        assert TRANSLATIONS["fr"] is FR
