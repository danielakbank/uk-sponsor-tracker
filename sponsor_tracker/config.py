"""Settings shared by the whole project."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "sponsors.db"

EXPECTED_COLUMNS = [
    "Organisation Name",
    "Town/City",
    "County",
    "Type & Rating",
    "Route",
]