#!/usr/bin/env python3
"""
Build a reproducible SQLite database from the CSV sources.

Usage:
    python3 scripts/build_sqlite_db.py
    python3 scripts/build_sqlite_db.py --run-queries
    python3 scripts/build_sqlite_db.py --db /tmp/banking.db
"""

from __future__ import annotations

import argparse
import csv
import datetime
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config import (  # noqa: E402
    RAW_FACT_PATH,
    RELATIONSHIPS_LOOKUP_PATH,
    GENDER_LOOKUP_PATH,
    ADVISORS_LOOKUP_PATH,
    SQLITE_DB_PATH,
)

SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"
ANALYTICS_PATH = BASE_DIR / "sql" / "analytics_queries.sql"

# (source column, destination column, caster)
FACT_COLUMNS: Sequence[Tuple[str, str, str]] = (
    ("Client ID", "client_id", "text"),
    ("Name", "client_name", "text"),
    ("Age", "age", "int"),
    ("Location ID", "location_id", "int"),
    ("Joined Bank", "joined_date", "date"),
    ("Banking Contact", "banking_contact", "text"),
    ("Nationality", "nationality", "text"),
    ("Occupation", "occupation", "text"),
    ("Fee Structure", "fee_structure", "text"),
    ("Loyalty Classification", "loyalty_classification", "text"),
    ("Estimated Income", "estimated_income", "float"),
    ("Superannuation Savings", "superannuation_savings", "float"),
    ("Amount of Credit Cards", "credit_cards_count", "int"),
    ("Credit Card Balance", "credit_card_balance", "float"),
    ("Bank Loans", "bank_loans", "float"),
    ("Bank Deposits", "bank_deposits", "float"),
    ("Checking Accounts", "checking_accounts", "float"),
    ("Saving Accounts", "saving_accounts", "float"),
    ("Foreign Currency Account", "foreign_currency_account", "float"),
    ("Business Lending", "business_lending", "float"),
    ("Properties Owned", "properties_owned", "int"),
    ("Risk Weighting", "risk_weighting", "text"),
    ("BRId", "relationship_id", "int"),
    ("GenderId", "gender_id", "int"),
    ("IAId", "advisor_id", "int"),
)

DIMENSIONS = (
    (
        GENDER_LOOKUP_PATH,
        "dim_gender",
        ("gender_id", "gender_name"),
        ("GenderId", "Gender"),
    ),
    (
        RELATIONSHIPS_LOOKUP_PATH,
        "dim_banking_relationships",
        ("relationship_id", "relationship_type"),
        ("BRId", "Banking Relationship"),
    ),
    (
        ADVISORS_LOOKUP_PATH,
        "dim_investment_advisors",
        ("advisor_id", "advisor_name"),
        ("IAId", "Investment Advisor"),
    ),
)


def cast_value(value: str, kind: str):
    """Casts a CSV value to the type expected by SQLite."""
    value = value.strip()
    if kind == "int":
        return int(value)
    if kind == "float":
        return float(value)
    if kind == "date":
        return datetime.datetime.strptime(value, "%d-%m-%Y").strftime("%Y-%m-%d")
    return value


def load_dimensions(conn: sqlite3.Connection) -> Dict[str, int]:
    """Loads the three lookup dimensions and returns row counts."""
    counts = {}
    for path, table, dest_cols, source_cols in DIMENSIONS:
        with open(path, mode="r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        placeholders = ", ".join("?" for _ in dest_cols)
        sql = f"INSERT INTO {table} ({', '.join(dest_cols)}) VALUES ({placeholders})"
        conn.executemany(
            sql,
            [tuple(row[col].strip() for col in source_cols) for row in rows],
        )
        counts[table] = len(rows)
    return counts


def load_fact(conn: sqlite3.Connection) -> int:
    """Loads the fact table from Banking.csv."""
    with open(RAW_FACT_PATH, mode="r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    dest_cols = [dest for _, dest, _ in FACT_COLUMNS]
    placeholders = ", ".join("?" for _ in dest_cols)
    sql = (
        f"INSERT INTO fact_banking_clients ({', '.join(dest_cols)}) "
        f"VALUES ({placeholders})"
    )
    conn.executemany(
        sql,
        [
            tuple(cast_value(row[source], kind) for source, _, kind in FACT_COLUMNS)
            for row in rows
        ],
    )
    return len(rows)


def build_database(db_path: Path) -> Dict[str, int]:
    """Creates the schema, loads all CSVs, and returns table row counts."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        counts = load_dimensions(conn)
        counts["fact_banking_clients"] = load_fact(conn)
        conn.commit()
    finally:
        conn.close()

    return counts


def iter_statements(sql_text: str) -> List[str]:
    """Splits a SQL script into executable statements, preserving comments."""
    statements: List[str] = []
    buffer = ""
    for line in sql_text.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statement = buffer.strip()
            if statement:
                statements.append(statement)
            buffer = ""
    if buffer.strip():
        statements.append(buffer.strip())
    return statements


def run_analytics(db_path: Path) -> None:
    """Executes every analytics query and prints a compact result preview."""
    conn = sqlite3.connect(db_path)
    try:
        for index, statement in enumerate(
            iter_statements(ANALYTICS_PATH.read_text(encoding="utf-8")), start=1
        ):
            cursor = conn.execute(statement)
            rows = cursor.fetchall()
            headers = [description[0] for description in cursor.description or []]
            print(f"\n--- Query {index}: {len(rows)} row(s) ---")
            if headers:
                print(" | ".join(headers))
            for row in rows[:10]:
                print(" | ".join("" if value is None else str(value) for value in row))
            if len(rows) > 10:
                print(f"... {len(rows) - 10} more row(s)")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=SQLITE_DB_PATH,
        help=f"SQLite database output path (default: {SQLITE_DB_PATH})",
    )
    parser.add_argument(
        "--run-queries",
        action="store_true",
        help="Run sql/analytics_queries.sql after loading and print results",
    )
    args = parser.parse_args()

    counts = build_database(args.db)
    print(f"Built {args.db}")
    for table, count in counts.items():
        print(f"  {table}: {count:,} rows")

    if args.run_queries:
        run_analytics(args.db)


if __name__ == "__main__":
    main()
