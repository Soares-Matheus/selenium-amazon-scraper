"""
Tests for the Amazon Product Scraper.

Run with:
    pytest tests/ -v
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from selenium.common.exceptions import NoSuchElementException

from scraper import AmazonScraper, COUNTRIES, load_config


def make_card(title="Test Product", offscreen_price="$599.00",
              price_whole="1.299", price_fraction="99",
              asin="B001TEST", rating_text="4.5 out of 5 stars",
              has_offscreen=True, has_whole=True):
    """Build a mock Selenium WebElement that mimics a current Amazon card."""
    card = MagicMock()
    card.get_attribute = MagicMock(
        side_effect=lambda name: asin if name == "data-asin" else None
    )

    def find_element(by, selector):
        el = MagicMock()
        if selector in ("h2 span", "h2", "[data-cy='title-recipe']"):
            if title is None:
                raise NoSuchElementException
            el.text = title
            el.get_attribute = MagicMock(return_value=title)
            return el
        if "a-offscreen" in selector:
            if not has_offscreen:
                raise NoSuchElementException
            el.text = ""  # hidden text — Selenium .text is empty on purpose
            el.get_attribute = MagicMock(return_value=offscreen_price)
            return el
        if "a-price-whole" in selector:
            if not has_whole:
                raise NoSuchElementException
            el.text = price_whole
            return el
        if "a-price-fraction" in selector:
            el.text = price_fraction
            return el
        if ("a-icon-star" in selector or "stars" in selector
                or "estrelas" in selector or "sur 5" in selector
                or "von 5" in selector):
            if rating_text is None:
                raise NoSuchElementException
            el.get_attribute = MagicMock(
                side_effect=lambda n: rating_text if n in ("textContent", "aria-label") else None
            )
            return el
        raise NoSuchElementException

    card.find_element = find_element
    return card


class TestLoadConfig:
    def test_returns_defaults_when_file_missing(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.yaml")
        assert config["scraper"]["default_country"] == "br"
        assert config["scraper"]["headless"] is True
        assert config["scraper"]["timeout"] == 10

    def test_loads_values_from_file(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "scraper:\n  default_country: us\n  headless: false\n  timeout: 20\n"
        )
        config = load_config(config_file)
        assert config["scraper"]["default_country"] == "us"
        assert config["scraper"]["headless"] is False
        assert config["scraper"]["timeout"] == 20

    def test_merges_partial_config_with_defaults(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("scraper:\n  default_country: fr\n")
        config = load_config(config_file)
        assert config["scraper"]["default_country"] == "fr"
        assert config["scraper"]["timeout"] == 10


class TestCountries:
    def test_all_countries_have_required_keys(self):
        for code, data in COUNTRIES.items():
            assert "url" in data, "{} missing 'url'".format(code)
            assert "currency" in data, "{} missing 'currency'".format(code)
            assert "decimal" in data, "{} missing 'decimal'".format(code)

    def test_all_urls_start_with_https(self):
        for code, data in COUNTRIES.items():
            assert data["url"].startswith("https://"), "{} URL is not HTTPS".format(code)

    def test_brazil_config(self):
        assert COUNTRIES["br"]["currency"] == "R$"
        assert COUNTRIES["br"]["decimal"] == ","
        assert "amazon.com.br" in COUNTRIES["br"]["url"]

    def test_us_config(self):
        assert COUNTRIES["us"]["currency"] == "$"
        assert COUNTRIES["us"]["decimal"] == "."
        assert COUNTRIES["us"]["url"] == "https://www.amazon.com"


class TestAmazonScraperInit:
    @patch("scraper.webdriver.Chrome")
    def test_valid_country_initialises_correctly(self, mock_chrome):
        mock_chrome.return_value = MagicMock()
        scraper = AmazonScraper(country="us", headless=True)
        assert scraper.base_url == "https://www.amazon.com"
        assert scraper.currency == "$"
        assert scraper.decimal_sep == "."
        scraper.quit()

    @patch("scraper.webdriver.Chrome")
    def test_invalid_country_raises_value_error(self, mock_chrome):
        mock_chrome.return_value = MagicMock()
        with pytest.raises(ValueError, match="Unsupported country"):
            AmazonScraper(country="xx")

    @patch("scraper.webdriver.Chrome")
    def test_custom_timeout_and_delay_are_stored(self, mock_chrome):
        mock_chrome.return_value = MagicMock()
        scraper = AmazonScraper(timeout=20, delay_min=2.0, delay_max=5.0)
        assert scraper.timeout == 20
        assert scraper.delay_min == 2.0
        assert scraper.delay_max == 5.0
        scraper.quit()


class TestGetTitle:
    def test_extracts_title_from_card(self):
        card = make_card(title="Notebook Gamer")
        assert AmazonScraper._get_title(card) == "Notebook Gamer"

    def test_returns_empty_string_when_not_found(self):
        card = MagicMock()
        card.find_element = MagicMock(side_effect=NoSuchElementException)
        assert AmazonScraper._get_title(card) == ""


class TestGetPrice:
    def test_uses_offscreen_price_when_available(self):
        card = make_card(offscreen_price="$599.00")
        assert AmazonScraper._get_price(card, "$", ".") == "$599.00"

    def test_falls_back_to_whole_and_fraction(self):
        card = make_card(has_offscreen=False, price_whole="4.299", price_fraction="00")
        assert AmazonScraper._get_price(card, "R$", ",") == "R$ 4.299,00"

    def test_returns_no_price_when_not_found(self):
        card = make_card(has_offscreen=False, has_whole=False)
        assert AmazonScraper._get_price(card, "R$", ",") == "No price"


class TestGetLink:
    def test_builds_link_from_asin(self):
        card = make_card(asin="B001TEST")
        result = AmazonScraper._get_link(card, "https://www.amazon.com.br")
        assert result == "https://www.amazon.com.br/dp/B001TEST"

    def test_returns_empty_string_when_no_asin_or_anchor(self):
        card = make_card(asin=None)
        card.find_element = MagicMock(side_effect=NoSuchElementException)
        assert AmazonScraper._get_link(card, "https://www.amazon.com") == ""


class TestGetRating:
    def test_extracts_rating_from_icon_alt(self):
        card = make_card(rating_text="4.5 out of 5 stars")
        assert AmazonScraper._get_rating(card) == "4.5"

    def test_returns_no_rating_when_not_found(self):
        card = make_card(rating_text=None)
        assert AmazonScraper._get_rating(card) == "No rating"


class TestExportToExcel:
    def test_creates_excel_file(self, tmp_path):
        products = [
            {"Title": "Product A", "Price": "R$ 100,00", "Link": "https://amazon.com/a", "Rating": "4.5"},
            {"Title": "Product B", "Price": "R$ 200,00", "Link": "https://amazon.com/b", "Rating": "4.0"},
        ]
        output = str(tmp_path / "test_output.xlsx")
        AmazonScraper.export_to_excel(products, output)
        assert Path(output).exists()

    def test_excel_contains_correct_data(self, tmp_path):
        products = [
            {"Title": "Product A", "Price": "R$ 100,00", "Link": "https://amazon.com/a", "Rating": "4.5"},
        ]
        output = str(tmp_path / "test_output.xlsx")
        AmazonScraper.export_to_excel(products, output)
        df = pd.read_excel(output)
        assert df.iloc[0]["Title"] == "Product A"
        assert df.iloc[0]["Price"] == "R$ 100,00"
        assert str(df.iloc[0]["Rating"]) == "4.5"

    def test_does_not_create_file_when_no_products(self, tmp_path):
        output = str(tmp_path / "empty.xlsx")
        AmazonScraper.export_to_excel([], output)
        assert not Path(output).exists()

    def test_link_column_becomes_click_here(self, tmp_path):
        products = [
            {"Title": "Product A", "Price": "R$ 100,00", "Link": "https://amazon.com/a", "Rating": "4.5"},
        ]
        output = str(tmp_path / "test_output.xlsx")
        AmazonScraper.export_to_excel(products, output)
        df = pd.read_excel(output)
        assert df.iloc[0]["Link"] == "Click here"
