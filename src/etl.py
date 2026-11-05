"""
Banking Portfolio Analytics — ETL & Data Transformation Pipeline
Handles ingestion, data cleaning, relational enrichment, derived metrics,
and writes a reproducible processed dataset plus an ETL summary.
"""

import csv
import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.config import (
    RAW_FACT_PATH,
    RELATIONSHIPS_LOOKUP_PATH,
    GENDER_LOOKUP_PATH,
    ADVISORS_LOOKUP_PATH,
    PROCESSED_DATA_DIR,
    PROCESSED_FACT_PATH,
    ETL_SUMMARY_PATH,
    INCOME_BINS,
    INCOME_LABELS,
    FEE_STRUCTURE_RATES,
    DATE_FORMAT,
)


def load_lookup(path: Path, key_col: str, val_col: str) -> Dict[str, str]:
    """Loads a key-value dimension lookup table from CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Lookup file not found: {path}")
    lookup = {}
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lookup[row[key_col].strip()] = row[val_col].strip()
    return lookup


def assign_income_band(income: float) -> str:
    """Classifies income into Low, Mid, or High based on business thresholds."""
    if income <= INCOME_BINS[1]:
        return INCOME_LABELS[0]
    elif income <= INCOME_BINS[2]:
        return INCOME_LABELS[1]
    return INCOME_LABELS[2]


def transform_record(
    raw: Dict[str, str],
    gender_map: Dict[str, str],
    relationship_map: Dict[str, str],
    advisor_map: Dict[str, str],
    ref_date: Optional[datetime.date] = None
) -> Dict:
    """Cleans, casts, enriches, and computes derived analytical features for a single record."""
    if ref_date is None:
        ref_date = datetime.date.today()

    # Dates
    joined_date = datetime.datetime.strptime(raw["Joined Bank"].strip(), DATE_FORMAT).date()
    engagement_days = max(0, (ref_date - joined_date).days)

    # Financial Floats
    income = float(raw["Estimated Income"])
    bank_deposits = float(raw["Bank Deposits"])
    saving_accounts = float(raw["Saving Accounts"])
    checking_accounts = float(raw["Checking Accounts"])
    foreign_currency = float(raw["Foreign Currency Account"])
    bank_loans = float(raw["Bank Loans"])
    business_lending = float(raw["Business Lending"])
    cc_balance = float(raw["Credit Card Balance"])

    # Derived Metrics
    total_deposits = round(bank_deposits + saving_accounts + checking_accounts + foreign_currency, 2)
    total_loans = round(bank_loans + business_lending + cc_balance, 2)
    fee_rate = FEE_STRUCTURE_RATES.get(raw["Fee Structure"].strip(), 0.01)
    total_fees = round(total_loans * fee_rate, 2)
    income_band = assign_income_band(income)

    # Relational Dimensions
    gender = gender_map.get(raw["GenderId"].strip(), "Unknown")
    relationship = relationship_map.get(raw["BRId"].strip(), "Unknown")
    advisor = advisor_map.get(raw["IAId"].strip(), "Unknown")

    transformed = dict(raw)
    transformed.update({
        "Joined Date Clean": joined_date.isoformat(),
        "Engagement Days": engagement_days,
        "Income Band": income_band,
        "Total Deposits": total_deposits,
        "Total Loans": total_loans,
        "Fee Rate": fee_rate,
        "Total Fees": total_fees,
        "Gender": gender,
        "Banking Relationship": relationship,
        "Investment Advisor": advisor,
    })
    return transformed


def write_processed_outputs(processed: List[Dict], summary: Dict) -> None:
    """Writes the processed fact table and ETL summary to data_processed/."""
    if not processed:
        raise ValueError("No processed records to write.")

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(PROCESSED_FACT_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(processed[0].keys()))
        writer.writeheader()
        writer.writerows(processed)

    with open(ETL_SUMMARY_PATH, mode="w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")


def run_pipeline() -> Tuple[List[Dict], Dict]:
    """Executes the full end-to-end data processing workflow."""
    print("Loading dimension lookups...")
    gender_map = load_lookup(GENDER_LOOKUP_PATH, "GenderId", "Gender")
    rel_map = load_lookup(RELATIONSHIPS_LOOKUP_PATH, "BRId", "Banking Relationship")
    adv_map = load_lookup(ADVISORS_LOOKUP_PATH, "IAId", "Investment Advisor")

    print(f"Reading fact dataset from {RAW_FACT_PATH}...")
    with open(RAW_FACT_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    print(f"Transforming {len(raw_rows)} banking records...")
    processed = [
        transform_record(row, gender_map, rel_map, adv_map)
        for row in raw_rows
    ]

    client_ids = [row["Client ID"].strip() for row in processed]
    distinct_clients = len(set(client_ids))

    summary = {
        "total_records": len(processed),
        "distinct_clients": distinct_clients,
        "duplicate_client_records": len(processed) - distinct_clients,
        "total_portfolio_deposits": round(sum(r["Total Deposits"] for r in processed), 2),
        "total_portfolio_loans": round(sum(r["Total Loans"] for r in processed), 2),
        "total_estimated_fees": round(sum(r["Total Fees"] for r in processed), 2),
        "loan_to_deposit_ratio_pct": round(
            sum(r["Total Loans"] for r in processed)
            / sum(r["Total Deposits"] for r in processed) * 100,
            2,
        ),
    }

    write_processed_outputs(processed, summary)

    print(f"ETL complete: {summary['total_records']} records -> {summary['distinct_clients']} distinct clients.")
    print(f"Portfolio Deposits: ${summary['total_portfolio_deposits']:,.2f}")
    print(f"Portfolio Loans:    ${summary['total_portfolio_loans']:,.2f}")
    print(f"Estimated Fees:     ${summary['total_estimated_fees']:,.2f}")
    print(f"Loan-to-Deposit:    {summary['loan_to_deposit_ratio_pct']:.2f}%")
    print(f"Processed data:     {PROCESSED_FACT_PATH}")
    print(f"ETL summary:        {ETL_SUMMARY_PATH}")
    return processed, summary


if __name__ == "__main__":
    run_pipeline()
