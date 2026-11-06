import pandas as pd

from sponsor_tracker.cleaning import clean_register
from sponsor_tracker.compare import compare_snapshots


def snapshot(rows: list[tuple[str, str]]) -> pd.DataFrame:
    raw = pd.DataFrame(
        [(name, town, "", "Worker (A rating)", "Skilled Worker") for name, town in rows],
        columns=["Organisation Name", "Town/City", "County", "Type & Rating", "Route"],
    )
    return clean_register(raw)


def test_detects_added_and_removed():
    old = snapshot([("Alpha Ltd", "Leeds"), ("Beta Ltd", "Hull")])
    new = snapshot([("Alpha Ltd", "Leeds"), ("Gamma Ltd", "Bolton")])

    changes = compare_snapshots(old, new)

    assert list(changes.added["name"]) == ["Gamma Ltd"]
    assert list(changes.removed["name"]) == ["Beta Ltd"]
    assert changes.moved.empty


def test_company_in_new_town_is_moved_not_added_and_removed():
    old = snapshot([("Alpha Ltd", "Leeds")])
    new = snapshot([("Alpha Ltd", "Bolton")])

    changes = compare_snapshots(old, new)

    assert changes.added.empty
    assert changes.removed.empty
    assert list(changes.moved["old_town"]) == ["Leeds"]
    assert list(changes.moved["new_town"]) == ["Bolton"]


def test_same_file_twice_has_no_changes():
    data = snapshot([("Alpha Ltd", "Leeds")])
    changes = compare_snapshots(data, data)
    assert changes.added.empty and changes.removed.empty and changes.moved.empty