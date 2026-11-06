"""Work out what changed between two snapshots of the register."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Changes:
    added: pd.DataFrame
    removed: pd.DataFrame
    moved: pd.DataFrame


def compare_snapshots(old: pd.DataFrame, new: pd.DataFrame) -> Changes:
    """Compare two cleaned snapshots.

    A sponsor is 'added' if its key is only in the new file, and 'removed' if
    its key is only in the old file. If the same company and route appears in
    both lists with a different town, it is reported as 'moved' instead, so a
    company that changed address does not look like a removal plus an addition.
    """
    only_new = new[~new["key"].isin(old["key"])]
    only_old = old[~old["key"].isin(new["key"])]

    def company_route(df: pd.DataFrame) -> pd.Series:
        return df["name_key"] + "|" + df["route"].str.upper()

    new_ids = company_route(only_new)
    old_ids = company_route(only_old)
    moved_ids = set(new_ids) & set(old_ids)

    moved_from = only_old[old_ids.isin(moved_ids)].rename(
        columns={"town": "old_town", "county": "old_county"}
    )
    moved_to = only_new[new_ids.isin(moved_ids)].rename(
        columns={"town": "new_town", "county": "new_county"}
    )
    moved = moved_from[["name", "name_key", "route", "old_town"]].merge(
        moved_to[["name_key", "route", "new_town"]],
        on=["name_key", "route"],
    )
    moved = moved.drop_duplicates(subset=["name_key", "route", "old_town", "new_town"])

    added = only_new[~new_ids.isin(moved_ids)]
    removed = only_old[~old_ids.isin(moved_ids)]

    return Changes(
        added=added.sort_values("name").reset_index(drop=True),
        removed=removed.sort_values("name").reset_index(drop=True),
        moved=moved.sort_values("name").reset_index(drop=True),
    )