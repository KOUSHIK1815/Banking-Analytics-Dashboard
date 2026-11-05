# Source tables

This directory contains the relational lookup tables used by the SQL star schema:

- `banking-relationships.csv` - Banking relationship lookup (`BRId` to `Banking Relationship`).
- `gender.csv` - Gender lookup (`GenderId` to `Gender`).
- `investment-advisors.csv` - Investment advisor lookup (`IAId` to `Investment Advisor`).

The root `Banking.csv` is the single canonical fact table consumed by the Python ETL, SQL database builder, notebook, and Power BI model. It contains 3,000 banking records and 2,940 distinct client IDs; the duplicate IDs are a documented synthetic-data quality issue, not separate client populations.
