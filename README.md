# Banking Portfolio Analytics Dashboard

An end-to-end portfolio project that explores a banking client dataset in Python and presents loan, deposit, client-engagement, and fee metrics in Power BI.

> **Scope:** This is a descriptive analytics dashboard, not a credit-risk or loan-approval model. The data contains no repayment, default, approval, credit-score, or ground-truth risk-outcome field, so it must not be used to make lending decisions.

![Dashboard overview](images/dashboard_overview-1.png)

## Project highlights

- **3,000 client-level records** across 25 raw fields.
- Python exploratory analysis covering distributions, categories, missing values, correlation, and selected bivariate relationships.
- A five-page Power BI report with home, loan analysis, deposit analysis, summary, and client-detail/drill-through views.
- Slicers for engagement timeframe, banking relationship, gender, and investment advisor.
- Derived Power BI fields for engagement duration, income segment, and processing-fee rate.

## Repository layout

```text
.
├── Banking.csv                         # Primary client dataset used by the notebook
├── datasets/                           # Relationship, gender, advisor, and client source tables
├── notebooks/banking_eda.ipynb         # Current Python EDA notebook
├── powerbi/banking_dashboard.pbix      # Current Power BI report
├── powerbi/banking_dashboard.pdf       # Exported dashboard preview
├── docs/banking_project_report.pdf     # Project and DAX documentation
├── docs/metrics.md                     # Metric definitions and limitations
├── images/dashboard_overview-1.png     # README preview image
└── archive/                            # Earlier notebook and dashboard iterations
```

## Data model

`Banking.csv` is the client fact table. It contains demographic attributes, banking balances, lending balances, loyalty/fee attributes, and foreign keys to the lookup tables in `datasets/`.

| Lookup table | Join key | Purpose |
| --- | --- | --- |
| `datasets/gender.csv` | `GenderId` | Maps gender IDs to labels |
| `datasets/banking-realtionships.csv` | `BRId` | Maps banking relationship IDs to labels |
| `datasets/investment-advisiors.csv` | `IAId` | Maps adviser IDs to names |

`datasets/banking-clients.csv` is an identical copy of the root `Banking.csv`, retained as part of the original source bundle.

## Dashboard pages

1. **Home** - portfolio-level client, loan, deposit, fee, credit-card, and savings KPIs.
2. **Loan Analysis** - lending segmented by banking relationship, income band, nationality, and engagement timeframe.
3. **Deposit Analysis** - deposits and account balances by income band, nationality, and engagement timeframe.
4. **Summary** - consolidated KPI cards.
5. **Client detail** - client-level fees, engagement, adviser, and credit-card balance detail.

See [metric definitions and caveats](docs/metrics.md) before interpreting the cards.

## Run the Python analysis

Use Python 3.8+.

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
jupyter notebook notebooks/banking_eda.ipynb
```

The notebook reads `../Banking.csv`, so run it from the `notebooks/` directory or open it with Jupyter from the repository root.

## Open the Power BI report

Open `powerbi/banking_dashboard.pbix` in Power BI Desktop. The report uses the client fact data and the lookup tables described above. If Power BI prompts for a data-source path after cloning, point it to the CSV files in this repository.

## Data and publication notice

This dataset was supplied with the project. It includes names, client IDs, location IDs, and banking-contact names that resemble personal data. Before making the repository public, confirm that the data is synthetic or that you have permission to redistribute it. Otherwise, keep the repository private or replace the raw data with anonymized/sample data.

No license has been added to this repository. Add a license only after choosing the reuse terms you intend to grant.

## Technologies

Python, pandas, NumPy, Matplotlib, Seaborn, Jupyter Notebook, Power BI, DAX, and Power Query.
