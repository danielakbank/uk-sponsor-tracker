import pandas as pd

from sponsor_tracker.cleaning import (
    clean_register,
    name_key,
    split_type_and_rating,
    tidy_text,
)


def make_raw(rows: list[tuple[str, str, str, str, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=["Organisation Name", "Town/City", "County", "Type & Rating", "Route"],
    )


def test_tidy_text_trims_and_collapses_spaces():
    assert tidy_text("  Acme   Care  ") == "Acme Care"


def test_tidy_text_turns_missing_into_empty_string():
    assert tidy_text(float("nan")) == ""


def test_name_key_ignores_case_punctuation_and_limited():
    assert name_key("Acme Care Limited") == name_key("ACME CARE LTD.")


def test_split_type_and_rating():
    assert split_type_and_rating("Worker (A rating)") == ("Worker", "A rating")


def test_split_type_and_rating_without_brackets():
    assert split_type_and_rating("Worker") == ("Worker", "")


def test_clean_register_fixes_town_case_and_drops_duplicates():
    raw = make_raw(
        [
            (" Acme Ltd", "LONDON", "", "Worker (A rating)", "Skilled Worker"),
            ("Acme Ltd", "London", "", "Worker (A rating)", "Skilled Worker"),
        ]
    )
    result = clean_register(raw)
    assert len(result) == 1
    assert result.loc[0, "town"] == "London"
    assert result.loc[0, "rating"] == "A rating"