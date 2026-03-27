"""
conftest.py — makes pytest find the scraper module from any working directory.
"""
import sys
from pathlib import Path

# Add the project root to sys.path so `import scraper` works inside tests/
sys.path.insert(0, str(Path(__file__).parent.parent))
