# Metrics and interpretation notes

The definitions below are transcribed from the project report and intended to make the Power BI logic understandable without opening the PBIX file.

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
| Total Clients | Distinct count of `Client ID`. |
| Bank Loan | Sum of `Bank Loans`. |
| Business Lending | Sum of `Business Lending`. |
| Total Loan | Bank Loan + Business Lending + Credit Card Balance. |
| Bank Deposit | Sum of `Bank Deposits`. |
| Total Deposit | Bank Deposit + Saving Accounts + Checking Accounts + Foreign Currency Account. |
| Total Fees | Sum, at the client level, of Total Loan × Processing Fees. |
| Savings Account Amount | Sum of `Saving Accounts`. |
| Checking Account Amount | Sum of `Checking Accounts`. |
| Foreign Currency Amount | Sum of `Foreign Currency Account`. |
| Credit Card Balance | Sum of `Credit Card Balance`. |

## Important caveats

- **Total CC Amount** should be treated as the count of cards when it is calculated from `Amount of Credit Cards`; it should not use a currency symbol.
- **Engagement Account** is a sum of engagement days, not a currency amount; it should be renamed and formatted as days.
- The data is a customer-level snapshot, not a dated transaction ledger. Timeframe analysis reflects how long a customer has been with the bank, not historical performance over calendar time.
- The data does not include default, repayment, approval, or loss outcomes. It supports descriptive customer/portfolio segmentation only, not credit underwriting or risk prediction.
