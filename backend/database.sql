-- DCAT Database Schema (SQLite)
-- Run: sqlite3 dcat.db < database.sql

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(20) DEFAULT 'admin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Accounts (brands)
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL
);

-- Dealerships linked to accounts
CREATE TABLE IF NOT EXISTS dealerships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    name VARCHAR(150) NOT NULL,
    folder_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

-- Generated creatives log
CREATE TABLE IF NOT EXISTS generated_creatives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    dealership_id INTEGER NOT NULL,
    bg_filename VARCHAR(255),
    output_filename VARCHAR(255),
    format_label VARCHAR(30),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (dealership_id) REFERENCES dealerships(id)
);

-- Seed data

-- Admin user (password: admin123, sha256 hashed)
INSERT OR IGNORE INTO users (username, password_hash, role)
VALUES ('admin', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'admin');

-- Brands
INSERT OR IGNORE INTO accounts (name, slug) VALUES ('Tata', 'tata');
INSERT OR IGNORE INTO accounts (name, slug) VALUES ('Volkswagen', 'volkswagen');

-- Dealerships
INSERT OR IGNORE INTO dealerships (account_id, name, folder_name)
VALUES (1, 'Bellad Tata', 'Bellad-tata');

INSERT OR IGNORE INTO dealerships (account_id, name, folder_name)
VALUES (2, 'VW Autobahn', 'VW-Autobhan');

INSERT OR IGNORE INTO dealerships (account_id, name, folder_name)
VALUES (2, 'VW Hubli (Kumar)', 'VW-Hubli');
