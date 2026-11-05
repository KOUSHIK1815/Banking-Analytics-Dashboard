-- ============================================================================
-- Banking Portfolio Analytics — Database Schema (Star Schema DDL)
-- Dialect: SQLite 3.25+ (window functions + AUTOINCREMENT)
--
-- PostgreSQL note: replace INTEGER PRIMARY KEY AUTOINCREMENT with
-- GENERATED ALWAYS AS IDENTITY (or SERIAL), and replace SQLite date helpers
-- in analytics_queries.sql (strftime) with EXTRACT / DATE_TRUNC.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- Drop tables if they already exist (in reverse dependency order)
DROP TABLE IF EXISTS fact_banking_clients;
DROP TABLE IF EXISTS dim_investment_advisors;
DROP TABLE IF EXISTS dim_banking_relationships;
DROP TABLE IF EXISTS dim_gender;

-- ----------------------------------------------------------------------------
-- Dimension: Gender
-- Source: datasets/gender.csv
-- ----------------------------------------------------------------------------
CREATE TABLE dim_gender (
    gender_id       INTEGER PRIMARY KEY,
    gender_name     VARCHAR(20) NOT NULL
);

-- ----------------------------------------------------------------------------
-- Dimension: Banking Relationship
-- Source: datasets/banking-relationships.csv
-- ----------------------------------------------------------------------------
CREATE TABLE dim_banking_relationships (
    relationship_id   INTEGER PRIMARY KEY,
    relationship_type VARCHAR(50) NOT NULL
);

-- ----------------------------------------------------------------------------
-- Dimension: Investment Advisors
-- Source: datasets/investment-advisors.csv
-- ----------------------------------------------------------------------------
CREATE TABLE dim_investment_advisors (
    advisor_id      INTEGER PRIMARY KEY,
    advisor_name    VARCHAR(100) NOT NULL
);

-- ----------------------------------------------------------------------------
-- Fact Table: Banking Clients
-- Source: Banking.csv
-- Granularity: One row per banking record (3,000 rows, 2,940 distinct client IDs).
-- The source contains synthetic client-ID collisions, so client-level KPIs must
-- use COUNT(DISTINCT client_id), not COUNT(*).
-- ----------------------------------------------------------------------------
CREATE TABLE fact_banking_clients (
    record_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id               VARCHAR(50) NOT NULL,
    client_name             VARCHAR(100) NOT NULL,
    age                     INTEGER NOT NULL CHECK (age >= 0),
    location_id             INTEGER NOT NULL,
    joined_date             DATE NOT NULL,
    banking_contact         VARCHAR(100),
    nationality             VARCHAR(50) NOT NULL,
    occupation              VARCHAR(100) NOT NULL,
    fee_structure           VARCHAR(20) NOT NULL,
    loyalty_classification  VARCHAR(20) NOT NULL,
    estimated_income        NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    superannuation_savings  NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    credit_cards_count      INTEGER NOT NULL DEFAULT 0 CHECK (credit_cards_count >= 0),
    credit_card_balance     NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    bank_loans              NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    bank_deposits           NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    checking_accounts       NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    saving_accounts         NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    foreign_currency_account NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    business_lending        NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    properties_owned        INTEGER NOT NULL DEFAULT 0 CHECK (properties_owned >= 0),
    risk_weighting          VARCHAR(20) NOT NULL,
    relationship_id         INTEGER NOT NULL REFERENCES dim_banking_relationships(relationship_id),
    gender_id               INTEGER NOT NULL REFERENCES dim_gender(gender_id),
    advisor_id              INTEGER NOT NULL REFERENCES dim_investment_advisors(advisor_id)
);

-- ----------------------------------------------------------------------------
-- Performance Indexes for Analytical Joins & Groupings
-- ----------------------------------------------------------------------------
CREATE INDEX idx_fact_clients_client_id ON fact_banking_clients (client_id);
CREATE INDEX idx_fact_clients_joined_date ON fact_banking_clients (joined_date);
CREATE INDEX idx_fact_clients_advisor ON fact_banking_clients (advisor_id);
CREATE INDEX idx_fact_clients_relationship ON fact_banking_clients (relationship_id);
CREATE INDEX idx_fact_clients_income ON fact_banking_clients (estimated_income);
