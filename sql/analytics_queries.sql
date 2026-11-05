-- ============================================================================
-- Banking Portfolio Analytics — Core Analytical Queries
-- Dialect: SQLite 3.25+ (window functions, CTEs, strftime)
-- Focus: portfolio KPIs, income deciles, high-value advisor review,
--        credit concentration, cohort acquisition, fee yield, data quality.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Executive Summary: Portfolio Totals & Loan-to-Deposit Ratio (LDR)
-- Purpose: Portfolio liquidity health & overall credit exposure.
-- Note: 3,000 records represent 2,940 distinct clients (synthetic ID collisions).
-- ----------------------------------------------------------------------------
SELECT
    COUNT(DISTINCT client_id) AS distinct_clients,
    COUNT(*) AS banking_records,
    ROUND(SUM(bank_deposits + saving_accounts + checking_accounts + foreign_currency_account), 2) AS total_deposits,
    ROUND(SUM(bank_loans + business_lending + credit_card_balance), 2) AS total_loans,
    ROUND(SUM(credit_card_balance), 2) AS total_credit_card_exposure,
    ROUND(
        SUM(bank_loans + business_lending + credit_card_balance) * 100.0 /
        NULLIF(SUM(bank_deposits + saving_accounts + checking_accounts + foreign_currency_account), 0),
        2
    ) AS loan_to_deposit_ratio_pct,
    ROUND(AVG(estimated_income), 2) AS avg_client_income
FROM fact_banking_clients;


-- ----------------------------------------------------------------------------
-- 2. Customer Income Segmentation & Decile Yield (Window Function: NTILE)
-- Purpose: Segment banking records into 10 equal income deciles and analyze
-- balance concentration. Account-level grain; duplicate client IDs can appear
-- in adjacent deciles.
-- ----------------------------------------------------------------------------
WITH client_income_deciles AS (
    SELECT
        client_id,
        estimated_income,
        (bank_deposits + saving_accounts + checking_accounts + foreign_currency_account) AS client_deposits,
        (bank_loans + business_lending + credit_card_balance) AS client_loans,
        NTILE(10) OVER (ORDER BY estimated_income ASC) AS income_decile
    FROM fact_banking_clients
)
SELECT
    income_decile,
    COUNT(*) AS banking_records,
    COUNT(DISTINCT client_id) AS distinct_clients,
    ROUND(MIN(estimated_income), 0) AS min_income,
    ROUND(MAX(estimated_income), 0) AS max_income,
    ROUND(AVG(client_deposits), 2) AS avg_deposits,
    ROUND(AVG(client_loans), 2) AS avg_loans,
    ROUND(SUM(client_deposits) * 100.0 / (SELECT SUM(client_deposits) FROM client_income_deciles), 2) AS pct_of_portfolio_deposits
FROM client_income_deciles
GROUP BY income_decile
ORDER BY income_decile;


-- ----------------------------------------------------------------------------
-- 3. Top-Decile Deposit Clients Without a Bank Loan (Advisor Review)
-- Purpose: Prioritise the highest-value liquidity relationships for advisor
-- review. Uses the top 10% of total deposits (>= ~$2.72M) instead of the
-- non-selective $150k cutoff, which captures ~94.5% of records.
-- Note: every client already has an advisor ID; "unassigned advisor" is not a
-- valid segment in this dataset.
-- ----------------------------------------------------------------------------
WITH client_totals AS (
    SELECT
        f.*,
        (f.bank_deposits + f.saving_accounts + f.checking_accounts + f.foreign_currency_account) AS total_deposits,
        NTILE(10) OVER (
            ORDER BY (f.bank_deposits + f.saving_accounts + f.checking_accounts + f.foreign_currency_account) DESC
        ) AS deposit_decile
    FROM fact_banking_clients f
)
SELECT
    f.client_id,
    f.client_name,
    f.age,
    f.occupation,
    ROUND(f.estimated_income, 2) AS estimated_income,
    ROUND(f.total_deposits, 2) AS total_deposits,
    f.properties_owned,
    adv.advisor_name,
    rel.relationship_type
FROM client_totals f
JOIN dim_investment_advisors adv ON f.advisor_id = adv.advisor_id
JOIN dim_banking_relationships rel ON f.relationship_id = rel.relationship_id
WHERE f.deposit_decile = 1
  AND f.bank_loans = 0.00
ORDER BY f.total_deposits DESC
LIMIT 20;


-- ----------------------------------------------------------------------------
-- 4. Top 3 Borrowers by Banking Relationship Tier (Window Function: DENSE_RANK)
-- Purpose: Credit concentration analysis across customer relationship tiers.
-- ----------------------------------------------------------------------------
WITH ranked_borrowers AS (
    SELECT
        rel.relationship_type,
        f.client_id,
        f.client_name,
        f.occupation,
        (f.bank_loans + f.business_lending + f.credit_card_balance) AS total_debt,
        DENSE_RANK() OVER (
            PARTITION BY f.relationship_id
            ORDER BY (f.bank_loans + f.business_lending + f.credit_card_balance) DESC
        ) AS rank_in_tier
    FROM fact_banking_clients f
    JOIN dim_banking_relationships rel ON f.relationship_id = rel.relationship_id
)
SELECT
    relationship_type,
    rank_in_tier,
    client_name,
    occupation,
    ROUND(total_debt, 2) AS total_debt
FROM ranked_borrowers
WHERE rank_in_tier <= 3
ORDER BY relationship_type, rank_in_tier;


-- ----------------------------------------------------------------------------
-- 5. Annual Cohort Acquisition & Balance Profile
-- Purpose: Measure record acquisition pace and balances by join year.
-- This is a cohort acquisition view, not a retention/attrition calculation.
-- ----------------------------------------------------------------------------
SELECT
    strftime('%Y', joined_date) AS join_year,
    COUNT(*) AS banking_records,
    COUNT(DISTINCT client_id) AS distinct_clients,
    ROUND(SUM(bank_deposits + saving_accounts + checking_accounts), 2) AS cohort_deposits,
    ROUND(AVG(bank_deposits + saving_accounts + checking_accounts), 2) AS avg_deposit_per_record,
    ROUND(SUM(bank_loans + business_lending), 2) AS cohort_loans
FROM fact_banking_clients
GROUP BY strftime('%Y', joined_date)
ORDER BY join_year ASC;


-- ----------------------------------------------------------------------------
-- 6. Fee Structure Yield Analysis per Loyalty Classification
-- Purpose: Analyze fee generation rate across loyalty tiers.
-- Fee Calculation: High = 5%, Mid = 3%, Low = 1% of Total Loan.
-- ----------------------------------------------------------------------------
WITH client_fees AS (
    SELECT
        client_id,
        loyalty_classification,
        fee_structure,
        (bank_loans + business_lending + credit_card_balance) AS total_loans,
        CASE
            WHEN fee_structure = 'High' THEN 0.05
            WHEN fee_structure = 'Mid'  THEN 0.03
            ELSE 0.01
        END AS fee_rate
    FROM fact_banking_clients
)
SELECT
    loyalty_classification,
    fee_structure,
    COUNT(*) AS banking_records,
    COUNT(DISTINCT client_id) AS distinct_clients,
    ROUND(SUM(total_loans), 2) AS total_loans,
    ROUND(SUM(total_loans * fee_rate), 2) AS estimated_fee_revenue,
    ROUND(AVG(total_loans * fee_rate), 2) AS avg_fee_per_record
FROM client_fees
GROUP BY loyalty_classification, fee_structure
ORDER BY loyalty_classification, estimated_fee_revenue DESC;


-- ----------------------------------------------------------------------------
-- 7. Client ID Collision Audit
-- Purpose: Surface duplicate client IDs so client-level reporting uses
-- DISTINCT counts and the data-quality caveat stays visible.
-- ----------------------------------------------------------------------------
SELECT
    client_id,
    COUNT(*) AS banking_records,
    ROUND(SUM(bank_deposits + saving_accounts + checking_accounts + foreign_currency_account), 2) AS total_deposits
FROM fact_banking_clients
GROUP BY client_id
HAVING COUNT(*) > 1
ORDER BY banking_records DESC, client_id
LIMIT 20;
