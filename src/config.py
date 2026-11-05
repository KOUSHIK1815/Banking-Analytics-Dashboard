"""
Banking Portfolio Analytics — Project Configuration
Centralizes file paths, data dictionaries, and analytical thresholds.
"""

from pathlib import Path

# Project Roots
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "datasets"
PROCESSED_DATA_DIR = BASE_DIR / "data_processed"

# Source File Paths
RAW_FACT_PATH = BASE_DIR / "Banking.csv"
RELATIONSHIPS_LOOKUP_PATH = DATA_DIR / "banking-relationships.csv"
GENDER_LOOKUP_PATH = DATA_DIR / "gender.csv"
ADVISORS_LOOKUP_PATH = DATA_DIR / "investment-advisors.csv"

# Generated Output Paths
PROCESSED_FACT_PATH = PROCESSED_DATA_DIR / "banking_clients_processed.csv"
ETL_SUMMARY_PATH = PROCESSED_DATA_DIR / "etl_summary.json"
SQLITE_DB_PATH = PROCESSED_DATA_DIR / "banking.db"

# Analytical Bins & Categories
INCOME_BINS = [0, 100_000, 300_000, float("inf")]
INCOME_LABELS = ["Low", "Mid", "High"]

FEE_STRUCTURE_RATES = {
    "High": 0.05,
    "Mid": 0.03,
    "Low": 0.01
}

DATE_FORMAT = "%d-%m-%Y"
