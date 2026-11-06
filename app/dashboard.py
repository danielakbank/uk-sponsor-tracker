"""Homepage dashboard."""

import sys
from pathlib import Path

# Lets this file find the sponsor_tracker package when Streamlit runs it.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from sponsor_tracker import database
from sponsor_tracker.compare import compare_snapshots

st.set_page_config(page_title="UK Sponsor Tracker", layout="wide")


@st.cache_data
def get_changes(old_id: int, new_id: int):
    """Compare two snapshots. Cached, so it only runs once per pair of files."""
    connection = database.connect()
    try:
        old = database.get_sponsors(connection, old_id)
        new = database.get_sponsors(connection, new_id)
    finally:
        connection.close()
    return len(new), compare_snapshots(old, new)


st.title("UK Visa Sponsor Tracker")

connection = database.connect()
uploads = database.list_uploads(connection)
connection.close()

if uploads.empty:
    st.info("No data yet. Load a file with load.py.")
    st.stop()

latest = uploads.iloc[0]

if len(uploads) < 2:
    st.subheader(f"Register dated {latest['register_date']}")
    st.metric("Total sponsors", f"{latest['row_count']:,}")
    st.info("Load a second file to see changes")
    st.stop()

previous = uploads.iloc[1]
st.subheader(f"Comparing {previous['register_date']} with {latest['register_date']}")

total, changes = get_changes(int(previous["id"]), int(latest["id"]))

col_total, col_added, col_removed = st.columns(3)
col_total.metric("Total sponsors", f"{total:,}")
col_added.metric("Newly added", f"{len(changes.added):,}")
col_removed.metric("Removed", f"{len(changes.removed):,}")