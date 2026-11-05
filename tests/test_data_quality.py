"""
Banking Portfolio Analytics — Automated Data Quality & Verification Tests
Runs with Python standard unittest or pytest:
    python3 -m unittest discover tests
    pytest
"""

import csv
import unittest
from collections import Counter

from src.config import (
    RAW_FACT_PATH,
    RELATIONSHIPS_LOOKUP_PATH,
    GENDER_LOOKUP_PATH,
    ADVISORS_LOOKUP_PATH,
    FEE_STRUCTURE_RATES,
)
from src.etl import assign_income_band, load_lookup


class TestDataQuality(unittest.TestCase):
    """Rigorous data validation verifying integrity across all repository data files."""

    @classmethod
    def setUpClass(cls):
        """Loads all CSV datasets into memory once for the test suite."""
        # 1. Dimension Lookups
        cls.gender_map = load_lookup(GENDER_LOOKUP_PATH, "GenderId", "Gender")
        cls.rel_map = load_lookup(RELATIONSHIPS_LOOKUP_PATH, "BRId", "Banking Relationship")
        cls.adv_map = load_lookup(ADVISORS_LOOKUP_PATH, "IAId", "Investment Advisor")

        # 2. Fact Table
        with open(RAW_FACT_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cls.fact_rows = list(reader)

    def test_file_existence_and_non_empty(self):
        """Verify all critical data files exist and have content."""
        paths = [
            RAW_FACT_PATH,
            RELATIONSHIPS_LOOKUP_PATH,
            GENDER_LOOKUP_PATH,
            ADVISORS_LOOKUP_PATH,
        ]
        for path in paths:
            self.assertTrue(path.exists(), f"File does not exist: {path}")
            self.assertGreater(path.stat().st_size, 0, f"File is empty: {path}")

    def test_no_utf8_bom(self):
        """Verify no CSV file contains a UTF-8 Byte Order Mark header corruption."""
        paths = [
            RAW_FACT_PATH,
            RELATIONSHIPS_LOOKUP_PATH,
            GENDER_LOOKUP_PATH,
            ADVISORS_LOOKUP_PATH,
        ]
        for path in paths:
            with open(path, "rb") as f:
                header_bytes = f.read(3)
                self.assertNotEqual(
                    header_bytes,
                    b"\xef\xbb\xbf",
                    f"File {path.name} contains UTF-8 BOM!"
                )

    def test_fact_record_count_and_columns(self):
        """Verify fact dataset contains exactly 3,000 rows and 25 required columns."""
        self.assertEqual(len(self.fact_rows), 3000, "Fact table row count != 3000")
        expected_cols = {
            "Client ID", "Name", "Age", "Location ID", "Joined Bank", "Banking Contact",
            "Nationality", "Occupation", "Fee Structure", "Loyalty Classification",
            "Estimated Income", "Superannuation Savings", "Amount of Credit Cards",
            "Credit Card Balance", "Bank Loans", "Bank Deposits", "Checking Accounts",
            "Saving Accounts", "Foreign Currency Account", "Business Lending",
            "Properties Owned", "Risk Weighting", "BRId", "GenderId", "IAId"
        }
        actual_cols = set(self.fact_rows[0].keys())
        self.assertEqual(expected_cols, actual_cols, "Column mismatch in fact table")

    def test_client_id_collisions_are_documented(self):
        """Verify the known 2,940-distinct-client / 3,000-record grain is stable."""
        counts = Counter(row["Client ID"].strip() for row in self.fact_rows)
        self.assertEqual(len(counts), 2940, "Distinct client ID count changed")
        duplicated_ids = [client_id for client_id, count in counts.items() if count > 1]
        self.assertEqual(len(duplicated_ids), 59, "Duplicated client ID count changed")
        self.assertEqual(
            sum(count - 1 for count in counts.values() if count > 1),
            60,
            "Extra duplicate records changed",
        )

    def test_no_null_or_blank_values(self):
        """Verify complete data completeness (zero nulls or blanks in raw dataset)."""
        for i, row in enumerate(self.fact_rows, 1):
            for col, val in row.items():
                self.assertIsNotNone(val, f"Null value at row {i}, column {col}")
                self.assertNotEqual(val.strip(), "", f"Blank value at row {i}, column {col}")

    def test_referential_integrity(self):
        """Verify foreign keys join cleanly against dimensional lookups."""
        for i, row in enumerate(self.fact_rows, 1):
            gid = row["GenderId"].strip()
            brid = row["BRId"].strip()
            iaid = row["IAId"].strip()

            self.assertIn(gid, self.gender_map, f"Invalid GenderId {gid} at row {i}")
            self.assertIn(brid, self.rel_map, f"Invalid BRId {brid} at row {i}")
            self.assertIn(iaid, self.adv_map, f"Invalid IAId {iaid} at row {i}")

    def test_every_client_has_an_advisor(self):
        """Verify there is no 'unassigned advisor' population to analyse."""
        self.assertEqual(len(self.adv_map), 22)
        self.assertTrue(all(row["IAId"].strip() in self.adv_map for row in self.fact_rows))

    def test_numeric_ranges_and_invariants(self):
        """Verify numerical fields satisfy financial invariants (no negative balances)."""
        for i, row in enumerate(self.fact_rows, 1):
            age = int(row["Age"])
            income = float(row["Estimated Income"])
            deposits = float(row["Bank Deposits"])
            savings = float(row["Saving Accounts"])
            checking = float(row["Checking Accounts"])
            foreign = float(row["Foreign Currency Account"])
            loans = float(row["Bank Loans"])
            business = float(row["Business Lending"])
            cc_balance = float(row["Credit Card Balance"])
            cards_count = int(row["Amount of Credit Cards"])

            self.assertGreaterEqual(age, 16, f"Invalid age {age} at row {i}")
            self.assertGreaterEqual(income, 0.0, f"Negative income at row {i}")
            self.assertGreaterEqual(deposits, 0.0, f"Negative deposits at row {i}")
            self.assertGreaterEqual(savings, 0.0, f"Negative savings at row {i}")
            self.assertGreaterEqual(checking, 0.0, f"Negative checking at row {i}")
            self.assertGreaterEqual(foreign, 0.0, f"Negative foreign currency at row {i}")
            self.assertGreaterEqual(loans, 0.0, f"Negative bank loans at row {i}")
            self.assertGreaterEqual(business, 0.0, f"Negative business lending at row {i}")
            self.assertGreaterEqual(cc_balance, 0.0, f"Negative credit card balance at row {i}")
            self.assertGreaterEqual(cards_count, 0, f"Negative credit cards count at row {i}")

    def test_income_band_classification_logic(self):
        """Verify the derived income band logic behaves according to business rules."""
        self.assertEqual(assign_income_band(50_000), "Low")
        self.assertEqual(assign_income_band(100_000), "Low")
        self.assertEqual(assign_income_band(100_001), "Mid")
        self.assertEqual(assign_income_band(300_000), "Mid")
        self.assertEqual(assign_income_band(300_001), "High")

    def test_fee_rates_mapping(self):
        """Verify fee structure rates match documented DAX thresholds."""
        self.assertEqual(FEE_STRUCTURE_RATES["High"], 0.05)
        self.assertEqual(FEE_STRUCTURE_RATES["Mid"], 0.03)
        self.assertEqual(FEE_STRUCTURE_RATES["Low"], 0.01)


if __name__ == "__main__":
    unittest.main()
