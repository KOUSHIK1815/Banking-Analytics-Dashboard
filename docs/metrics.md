# Metrics and interpretation notes

The definitions below make the Power BI and SQL logic understandable without opening the PBIX file. They are aligned with the verified figures in the current dataset.

## Data grain

- The fact table contains **3,000 banking records** but only **2,940 distinct client IDs**.
- 59 client IDs appear more than once (60 extra records) because of synthetic ID collisions.
- Treat the fact grain as a **banking record/account**, and use `COUNT(DISTINCT client_id)` / `DISTINCTCOUNT` for client-level KPIs.

## Derived fields

| Field | Definition |
| --- | --- |
| Income Band | `Low` for estimated income below 100,000; `Mid` below 300,000; otherwise `High`. |
| Processing Fees | 5% for `High`, 3% for `Mid`, and 1% for `Low` fee structure. |
| Engagement Days | `DATEDIFF([Joined Bank], TODAY(), DAY)`. |
| Engagement Timeframe | Bucketed engagement duration used by report slicers and charts. |

`Engagement Days` is calculated relative to `TODAY()`. In Power BI, a calculated column changes when the model is refreshed, not continuously while a report remains open.

## KPI definitions

| KPI | Definition |
| --- | --- |
| Total Clients | Distinct count of `Client ID` (2,940). |
| Banking Records | Row count of the fact table (3,000). |
| Bank Loan | Sum of `Bank Loans`. |
| Business Lending | Sum of `Business Lending`. |
| Total Loan | Bank Loan + Business Lending + Credit Card Balance. |
| Bank Deposit | Sum of `Bank Deposits`. |
| Total Deposit | Bank Deposit + Saving Accounts + Checking Accounts + Foreign Currency Account. |
| Total Fees | Sum, at the record level, of Total Loan × Processing Fees. |
| Loan-to-Deposit Ratio (LDR) | Total Loan ÷ Total Deposit. |
| Savings Account Amount | Sum of `Saving Accounts`. |
| Checking Account Amount | Sum of `Checking Accounts`. |
| Foreign Currency Amount | Sum of `Foreign Currency Account`. |
| Credit Card Balance | Sum of `Credit Card Balance`. |
| Total CC Amount | Count of cards from `Amount of Credit Cards`; do **not** format as currency. |

## Verified portfolio figures

| Metric | Value |
| --- | --- |
| Distinct clients | 2,940 |
| Banking records | 3,000 |
| Total deposits | $3,766,335,079.58 |
| Total loans | $4,383,966,512.51 |
| Loan-to-deposit ratio | 116.40% |
| Estimated fees | $158,192,196.33 |
| High fee tier share of fees | 67.7% |
| Mid income band share of fees | 54.0% |
| Top-decile deposit threshold | $2,722,282.69 |
| Records at/above top-decile threshold | 300 |
| Records with no bank loan | 27 |
| Records with no business lending | 14 |

## Important caveats

- **Total CC Amount** should be treated as the count of cards when it is calculated from `Amount of Credit Cards`; it should not use a currency symbol. The current PBIX tile is formatted as currency and should be corrected in Power BI.
- **Engagement Account** is a sum of engagement days, not a currency amount; it should be renamed and formatted as days.
- The data is a customer-level snapshot, not a dated transaction ledger. Timeframe analysis reflects how long a customer has been with the bank, not historical performance over calendar time.
- The dataset does not include default, repayment, approval, or loss outcomes. It supports descriptive customer/portfolio segmentation only, not credit underwriting or risk prediction.
- **Every client has an advisor ID** (22 advisors, 88–177 clients each). There is no "unassigned advisor" field, so avoid claiming an unassigned-advisor cross-sell segment.
- **The $150,000 deposit cutoff is not selective**: it captures 94.5% of records. Use the top decile ($2.72M+) or top quartile ($1.74M+) when defining a high-value segment.
- **Cross-sell whitespace is limited**: 99.1% of records have a bank loan, 99.5% have business lending, 100% have a credit card balance, and 98.9% have deposits/savings/checking. Only 27 records have no bank loan; none have zero total debt.
