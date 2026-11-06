"""Read the Home Office register CSV and turn it into clean, tidy data."""

import re
from pathlib import Path

import pandas as pd

from sponsor_tracker.config import EXPECTED_COLUMNS

_SPACES = re.compile(r"\s+")
_NAME_NOISE = re.compile(r"[^\w\s&]")


def tidy_text(value: object) -> str:
    """Trim a value and collapse repeated spaces. Blank values become ''."""
    if pd.isna(value):
        return ""
    return _SPACES.sub(" ", str(value)).strip()


def name_key(name: str) -> str:
    """Make a name safe to compare: upper case, no punctuation, LTD not LIMITED."""
    cleaned = _NAME_NOISE.sub(" ", name.upper())
    cleaned = _SPACES.sub(" ", cleaned).strip()
    return re.sub(r"\bLIMITED\b", "LTD", cleaned)


def split_type_and_rating(value: str) -> tuple[str, str]:
    """Split 'Worker (A rating)' into ('Worker', 'A rating')."""
    match = re.match(r"^(.*?)\s*\((.*)\)\s*$", value)
    if not match:
        return value, ""
    return match.group(1).strip(), match.group(2).strip()


def read_register(path: Path) -> pd.DataFrame:
    """Read the raw CSV. Fails loudly if the columns are not what we expect."""
    raw = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    raw.columns = [column.strip() for column in raw.columns]

    missing = [c for c in EXPECTED_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"CSV is missing expected columns: {missing}")
    return raw[EXPECTED_COLUMNS]


def clean_register(raw: pd.DataFrame) -> pd.DataFrame:
    """Return one tidy row per sponsor, route and worker type."""
    df = pd.DataFrame()
    df["name"] = raw["Organisation Name"].map(tidy_text)
    df["town"] = raw["Town/City"].map(tidy_text).str.title()
    df["county"] = raw["County"].map(tidy_text).str.title()
    df["route"] = raw["Route"].map(tidy_text)

    type_and_rating = raw["Type & Rating"].map(tidy_text).map(split_type_and_rating)
    df["worker_type"] = type_and_rating.map(lambda pair: pair[0])
    df["rating"] = type_and_rating.map(lambda pair: pair[1])

    df["name_key"] = df["name"].map(name_key)
    df["key"] = (
        df["name_key"]
        + "|"
        + df["town"].str.upper()
        + "|"
        + df["route"].str.upper()
        + "|"
        + df["worker_type"].str.upper()
    )

    df = df[df["name"] != ""]
    return df.drop_duplicates(subset="key").reset_index(drop=True)