-- Business Analyzer Database Schema

DROP DATABASE IF EXISTS business_analyzer;
CREATE DATABASE business_analyzer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE business_analyzer;

CREATE TABLE user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    registration_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    role ENUM('Admin', 'Customer', 'Moderator') NOT NULL DEFAULT 'Customer',
    INDEX idx_email (email),
    INDEX idx_username (username)
);

CREATE TABLE company (
    company_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    company_type ENUM('public', 'private') NOT NULL,
    industry VARCHAR(100),
    logo_url VARCHAR(512),
    founded_date DATE,
    description TEXT,
    market_cap DECIMAL(20, 2),
    stock_symbol VARCHAR(20),
    stock_exchange VARCHAR(100),
    INDEX idx_company_name (company_name),
    INDEX idx_industry (industry),
    INDEX idx_company_type (company_type),
    INDEX idx_stock_symbol (stock_symbol)
);

CREATE TABLE stock_price (
    price_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(15, 4) NOT NULL,
    close_price DECIMAL(15, 4) NOT NULL,
    high_price DECIMAL(15, 4) NOT NULL,
    low_price DECIMAL(15, 4) NOT NULL,
    volume BIGINT NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    FOREIGN KEY (company_id) REFERENCES company(company_id) ON DELETE CASCADE,
    UNIQUE KEY unique_company_date (company_id, date),
    INDEX idx_date (date),
    INDEX idx_company_date (company_id, date DESC)
);

CREATE TABLE financial_statement (
    statement_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    statement_type ENUM('quarterly', 'yearly') NOT NULL,
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    revenue DECIMAL(20, 2) NOT NULL,
    profit DECIMAL(20, 2) NOT NULL,
    FOREIGN KEY (company_id) REFERENCES company(company_id) ON DELETE CASCADE,
    INDEX idx_company_period (company_id, period_end_date DESC),
    INDEX idx_statement_type (statement_type)
);

CREATE TABLE asset (
    asset_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_name VARCHAR(100) NOT NULL UNIQUE,
    asset_type ENUM('commodity', 'precious_metal') NOT NULL,
    unit_of_measurement VARCHAR(20) NOT NULL,
    description TEXT,
    logo_url VARCHAR(512),
    INDEX idx_asset_name (asset_name),
    INDEX idx_asset_type (asset_type)
);


CREATE TABLE asset_price (
    asset_price_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    date DATE NOT NULL,
    price DECIMAL(15, 4) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    FOREIGN KEY (asset_id) REFERENCES asset(asset_id) ON DELETE CASCADE,
    UNIQUE KEY unique_asset_date (asset_id, date),
    INDEX idx_date (date),
    INDEX idx_asset_date (asset_id, date DESC)
);


CREATE TABLE scraped_content (
    content_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NULL,
    source_url VARCHAR(1024) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content_text TEXT NOT NULL,
    content_type ENUM('news', 'review', 'social_media') NOT NULL,
    scraped_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    publish_date DATETIME,
    author VARCHAR(255),
    source_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (company_id) REFERENCES company(company_id) ON DELETE SET NULL,
    INDEX idx_company_id (company_id),
    INDEX idx_scraped_date (scraped_date DESC),
    INDEX idx_content_type (content_type),
    INDEX idx_publish_date (publish_date DESC)
);


CREATE TABLE sentiment_analysis (
    sentiment_id INT AUTO_INCREMENT PRIMARY KEY,
    content_id INT NOT NULL UNIQUE,
    sentiment_score DECIMAL(3, 2) NOT NULL CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    sentiment_label ENUM('positive', 'negative', 'neutral') NOT NULL,
    confidence_level DECIMAL(3, 2) NOT NULL CHECK (confidence_level >= 0.0 AND confidence_level <= 1.0),
    analysis_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES scraped_content(content_id) ON DELETE CASCADE,
    INDEX idx_sentiment_label (sentiment_label),
    INDEX idx_analysis_date (analysis_date DESC),
    INDEX idx_confidence_level (confidence_level)
);


CREATE TABLE investment_recommendation (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NULL,
    asset_id INT NULL,
    recommendation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    recommendation_type ENUM('invest', 'dont_invest', 'hold', 'wait') NOT NULL,
    investment_score DECIMAL(5, 2) NOT NULL CHECK (investment_score >= 0 AND investment_score <= 100),
    risk_level ENUM('low', 'medium', 'high') NOT NULL,
    expected_return DECIMAL(5, 2),
    rationale_summary TEXT,
    FOREIGN KEY (company_id) REFERENCES company(company_id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES asset(asset_id) ON DELETE CASCADE,
    CHECK ((company_id IS NOT NULL AND asset_id IS NULL) OR (company_id IS NULL AND asset_id IS NOT NULL)),
    INDEX idx_company_date (company_id, recommendation_date DESC),
    INDEX idx_asset_date (asset_id, recommendation_date DESC),
    INDEX idx_recommendation_type (recommendation_type),
    INDEX idx_risk_level (risk_level)
);


CREATE TABLE bookmark (
    bookmark_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    company_id INT NULL,
    asset_id INT NULL,
    bookmark_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES company(company_id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES asset(asset_id) ON DELETE CASCADE,
    CHECK ((company_id IS NOT NULL AND asset_id IS NULL) OR (company_id IS NULL AND asset_id IS NOT NULL)),
    UNIQUE KEY unique_user_company (user_id, company_id),
    UNIQUE KEY unique_user_asset (user_id, asset_id),
    INDEX idx_user_id (user_id),
    INDEX idx_bookmark_date (bookmark_date DESC)
);
