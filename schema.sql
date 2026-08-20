-- CampusChain — Phase 5: Database Schema (Postgres)
-- Run this against a fresh database, e.g.:
--   psql "$DATABASE_URL" -f schema.sql

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(120)  NOT NULL,
    school_email    VARCHAR(150)  NOT NULL UNIQUE,
    student_id      VARCHAR(50)   NOT NULL UNIQUE,
    password_hash   VARCHAR(255)  NOT NULL,
    role            VARCHAR(20)   NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'admin')),
    phone           VARCHAR(30)   NULL,
    profile_image   VARCHAR(255)  NULL,
    status          VARCHAR(20)   NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_status ON users (status);

-- ============================================================
-- PRODUCTS
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    seller_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(150)  NOT NULL,
    description     TEXT NULL,
    price           NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    category        VARCHAR(50)   NOT NULL,
    condition       VARCHAR(30)   NULL,
    image_url       VARCHAR(255)  NULL,
    status          VARCHAR(20)   NOT NULL DEFAULT 'available'
                        CHECK (status IN ('available', 'pending', 'sold', 'removed')),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_products_status ON products (status);
CREATE INDEX IF NOT EXISTS idx_products_seller ON products (seller_id);
-- Full-text search replacement for MySQL's FULLTEXT index — the app already
-- queries with ILIKE, which uses this trigram index for speed on larger data.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_products_search ON products USING gin (title gin_trgm_ops, description gin_trgm_ops);

-- ============================================================
-- BLOCKCHAIN BLOCKS  (created before transactions since transactions
-- reference block_id)
-- ============================================================
CREATE TABLE IF NOT EXISTS blockchain_blocks (
    id              SERIAL PRIMARY KEY,
    transaction_id  INTEGER NOT NULL,
    seller_id       INTEGER NOT NULL,
    buyer_id        INTEGER NOT NULL,
    product_id      INTEGER NOT NULL,
    timestamp       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    previous_hash   CHAR(64) NOT NULL,
    current_hash    CHAR(64) NOT NULL UNIQUE
    -- Note: no FK to transactions here to avoid a circular FK dependency
    -- (transactions.block_id -> blockchain_blocks.id). Referential
    -- integrity between the two is enforced at the application layer
    -- in blockchain.py (add_block runs inside the same request that
    -- updates the transaction row).
);
CREATE INDEX IF NOT EXISTS idx_blocks_transaction ON blockchain_blocks (transaction_id);

-- ============================================================
-- TRANSACTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS transactions (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    seller_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    buyer_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    amount          NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    status          VARCHAR(20) NOT NULL DEFAULT 'requested'
                        CHECK (status IN ('requested', 'accepted', 'rejected', 'completed', 'cancelled')),
    qr_code_token   VARCHAR(64) NULL,
    block_id        INTEGER NULL REFERENCES blockchain_blocks(id) ON DELETE SET NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions (status);
CREATE INDEX IF NOT EXISTS idx_tx_buyer ON transactions (buyer_id);
CREATE INDEX IF NOT EXISTS idx_tx_seller ON transactions (seller_id);

-- ============================================================
-- REVIEWS
-- ============================================================
CREATE TABLE IF NOT EXISTS reviews (
    id              SERIAL PRIMARY KEY,
    transaction_id  INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    reviewer_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    seller_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating          SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment         VARCHAR(500) NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (transaction_id, reviewer_id)
);
CREATE INDEX IF NOT EXISTS idx_reviews_seller ON reviews (seller_id);

-- ============================================================
-- MESSAGES
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id              SERIAL PRIMARY KEY,
    sender_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id      INTEGER NULL REFERENCES products(id) ON DELETE SET NULL,
    content         VARCHAR(1000) NOT NULL,
    sent_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_flag       BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages (sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages (receiver_id);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type            VARCHAR(30) NOT NULL CHECK (type IN ('message', 'offer', 'sale', 'review', 'system')),
    content         VARCHAR(255) NOT NULL,
    link_id         INTEGER NULL,
    read_flag       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications (user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications (user_id, read_flag);
