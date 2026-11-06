"""Load one register CSV into the database.

Usage:
    python load.py data/register.csv
    python load.py data/register.csv --date 2026-11-05
"""

import argparse
import logging
import re
import sys
from pathlib import Path

from sponsor_tracker import cleaning, database

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("load")

DATE_IN_NAME = re.compile(r"\d{4}-\d{2}-\d{2}")


def find_date(path: Path, given: str | None) -> str:
    """Use --date if given, otherwise look for YYYY-MM-DD in the file name."""
    if given:
        return given
    match = DATE_IN_NAME.search(path.name)
    if match:
        return match.group(0)
    raise SystemExit("Could not find a date in the file name. Use --date YYYY-MM-DD.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load a sponsor register CSV.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--date", help="Register date, YYYY-MM-DD")
    args = parser.parse_args(argv)

    if not args.csv_path.is_file():
        log.error("File not found: %s", args.csv_path)
        return 1

    register_date = find_date(args.csv_path, args.date)
    hash_value = database.file_hash(args.csv_path)

    connection = database.connect()
    if database.already_loaded(connection, hash_value):
        log.info("This file is already loaded. Nothing to do.")
        return 0

    log.info("Reading %s", args.csv_path.name)
    sponsors = cleaning.clean_register(cleaning.read_register(args.csv_path))

    upload_id = database.save_upload(
        connection, sponsors, args.csv_path.name, hash_value, register_date
    )
    log.info("Saved upload %s with %s sponsors.", upload_id, len(sponsors))
    return 0


if __name__ == "__main__":
    sys.exit(main())