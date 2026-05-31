# Amazon Product Scraper

A Python bot that scrapes product listings from Amazon across 10 countries and exports the results — title, price, link, and customer rating — to a formatted Excel file with clickable hyperlinks.

---

## Features

- **Multi-country support** — scrape Amazon in 10 countries with a single flag
- **Correct currency per country** — price is automatically formatted with the right symbol and decimal separator
- **Direct URL navigation** — navigates straight to search result pages, avoiding bot-detection triggers from UI interaction
- **Multi-page scraping** — iterates through all result pages automatically (or up to `--max-pages`)
- **Excel export** — saves results to `.xlsx` with clickable product links
- **Anti-bot measures** — randomised delays, user-agent rotation, and WebDriver flag masking
- **Robust waiting** — uses Selenium `WebDriverWait` instead of fixed sleeps
- **External configuration** — behaviour tuned via `config.yaml`, no code changes needed
- **Automated tests** — 23 unit and integration tests with pytest

---

## Supported Countries

| Code | Country | Site | Currency |
|------|---------|------|----------|
| `br` | Brazil | amazon.com.br | R$ |
| `us` | United States | amazon.com | $ |
| `uk` | United Kingdom | amazon.co.uk | GBP |
| `de` | Germany | amazon.de | EUR |
| `fr` | France | amazon.fr | EUR |
| `es` | Spain | amazon.es | EUR |
| `it` | Italy | amazon.it | EUR |
| `ca` | Canada | amazon.ca | CAD |
| `mx` | Mexico | amazon.com.mx | MXN |
| `jp` | Japan | amazon.co.jp | JPY |

---

## Requirements

- Python 3.11+
- Google Chrome installed
- ChromeDriver matching your Chrome version ([download](https://chromedriver.chromium.org/downloads))

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Soares-Matheus/selenium-amazon-scraper.git
cd selenium-amazon-scraper

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Configuration

All behaviour can be tuned in `config.yaml` without touching the code:

```yaml
scraper:
  default_country: br   # country used when --country is not passed
  headless: false       # set to true to run Chrome without a visible window
  max_pages: null       # null = scrape all pages
  timeout: 10           # seconds to wait for page elements
  delay:
    min: 1.5            # minimum pause between pages (seconds)
    max: 3.0            # maximum pause between pages (seconds)
```

> **Note on headless mode:** Amazon actively detects and blocks headless browsers.
> Keep `headless: false` for reliable scraping. Only enable it if you have additional bypass measures in place.

CLI arguments always take priority over `config.yaml` when provided.

---

## Usage

### Basic — interactive prompt
```bash
python scraper.py
# -> Enter search term: Gaming Laptop
```

### With arguments
```bash
# Brazil (default)
python scraper.py --query "notebook gamer"

# United States
python scraper.py --query "gaming laptop" --country us

# France, limit to 3 pages
python scraper.py --query "clavier mecanique" --country fr --max-pages 3

# Show browser window (useful for debugging)
python scraper.py --query "auriculares" --country es --no-headless

# Custom output filename
python scraper.py --query "monitor 4k" --country de --output monitors.xlsx
```

### All options

| Argument | Description | Default |
|---|---|---|
| `--query` | Search term | Prompted if omitted |
| `--country` | Country code (see table above) | from `config.yaml` |
| `--max-pages` | Max result pages to scrape | from `config.yaml` |
| `--no-headless` | Show Chrome browser window | headless default from `config.yaml` |
| `--output` | Output `.xlsx` filename | `<query>_<country>_<timestamp>.xlsx` |

---

## Running Tests

```bash
pytest tests/ -v
```

Expected output:
```
tests/test_scraper.py::TestLoadConfig::test_returns_defaults_when_file_missing  PASSED
tests/test_scraper.py::TestLoadConfig::test_loads_values_from_file              PASSED
tests/test_scraper.py::TestCountries::test_all_countries_have_required_keys     PASSED
tests/test_scraper.py::TestGetPrice::test_formats_price_with_br_currency        PASSED
tests/test_scraper.py::TestGetPrice::test_formats_price_with_us_currency        PASSED
tests/test_scraper.py::TestExportToExcel::test_creates_excel_file               PASSED
23 passed in 1.33s
```

---

## Output

The script generates an Excel file with four columns:

| Title | Price | Link | Rating |
|-------|-------|------|--------|
| Notebook Gamer Dell G15 | R$ 4.299,00 | [Click here](#) | 4.5 |
| Gaming Laptop ASUS ROG | $ 1.299.99 | [Click here](#) | 4.7 |

The filename includes the country code and timestamp to avoid overwriting results:
```
gaming_laptop_us_27-03-2026_10-30-00.xlsx
notebook_gamer_br_27-03-2026_10-31-00.xlsx
```

---

## Project Structure

```
selenium-amazon-scraper/
├── scraper.py          # Main scraper (AmazonScraper class + CLI)
├── config.yaml         # Behaviour settings (no code changes needed)
├── requirements.txt    # Python dependencies
├── tests/
│   ├── conftest.py     # pytest path setup
│   └── test_scraper.py # Unit and integration tests
└── README.md
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| [Selenium 4](https://selenium-python.readthedocs.io/) | Browser automation |
| [pandas](https://pandas.pydata.org/) | Data handling |
| [openpyxl](https://openpyxl.readthedocs.io/) | Excel file creation |
| [PyYAML](https://pyyaml.org/) | Configuration file parsing |
| [pytest](https://pytest.org/) | Automated testing |

---

## Disclaimer

This project is intended for educational and portfolio purposes. Always check a website's Terms of Service and `robots.txt` before scraping.

---

## Related project

This is the **data extraction** side of my Selenium portfolio. The
companion project [form-filler-automation](https://github.com/Soares-Matheus/form-filler-automation)
handles the opposite direction — filling data **into** any web form
via a YAML configuration. Both projects share the same engineering
style: config-driven, anti-detection enabled, `WebDriverWait`-based,
and pytest-tested.
