-- IB Analytics Production - PostgreSQL Schema
-- Optimizado para millones de deals

-- Extensiones
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Tabla principal de deals
CREATE TABLE deals (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    login VARCHAR(20) NOT NULL,
    deal_id BIGINT,
    external_id VARCHAR(128),
    order_id BIGINT,
    position_id BIGINT,
    symbol VARCHAR(50) NOT NULL,
    action VARCHAR(20),
    entry VARCHAR(20),
    volume DECIMAL(12, 2) NOT NULL DEFAULT 0,
    volume_closed DECIMAL(12, 2),
    gateway_volume DECIMAL(12, 2),
    price DECIMAL(18, 5),
    stop_loss DECIMAL(18, 5),
    take_profit DECIMAL(18, 5),
    market_bid DECIMAL(18, 5),
    market_ask DECIMAL(18, 5),
    market_last DECIMAL(18, 5),
    reason VARCHAR(50),
    fee DECIMAL(12, 2) DEFAULT 0,
    swap DECIMAL(12, 2) DEFAULT 0,
    value DECIMAL(18, 2),
    profit DECIMAL(18, 2) DEFAULT 0,
    dealer VARCHAR(128),
    comment TEXT,
    imported_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convertir a hypertable (TimescaleDB)
SELECT create_hypertable('deals', 'time', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Índices para performance
CREATE INDEX idx_deals_login ON deals (login, time DESC);
CREATE INDEX idx_deals_symbol ON deals (symbol, time DESC);
CREATE INDEX idx_deals_time ON deals (time DESC);
CREATE INDEX idx_deals_deal_id ON deals (deal_id);

-- Vista agregada por símbolo (actualización continua)
CREATE MATERIALIZED VIEW deals_by_symbol AS
SELECT 
    symbol,
    COUNT(*) as total_deals,
    SUM(volume) as total_volume,
    SUM(profit) as total_profit,
    SUM(volume) * 25.0 as revenue,
    COUNT(DISTINCT login) as unique_accounts,
    MIN(time) as first_deal,
    MAX(time) as last_deal
FROM deals
GROUP BY symbol
ORDER BY total_volume DESC;

CREATE INDEX idx_deals_by_symbol ON deals_by_symbol (symbol);

-- Vista agregada por cuenta
CREATE MATERIALIZED VIEW deals_by_account AS
SELECT 
    login,
    COUNT(*) as total_deals,
    SUM(volume) as total_volume,
    SUM(profit) as total_profit,
    SUM(volume) * 25.0 as revenue,
    COUNT(DISTINCT symbol) as unique_symbols,
    MIN(time) as first_deal,
    MAX(time) as last_deal
FROM deals
GROUP BY login
ORDER BY total_volume DESC;

CREATE INDEX idx_deals_by_account ON deals_by_account (login);

-- Vista resumen general
CREATE MATERIALIZED VIEW deals_summary AS
SELECT 
    COUNT(*) as total_deals,
    COUNT(DISTINCT login) as unique_accounts,
    COUNT(DISTINCT symbol) as unique_symbols,
    SUM(volume) as total_volume,
    SUM(profit) as total_profit,
    SUM(fee) as total_fee,
    SUM(swap) as total_swap,
    SUM(volume) * 25.0 as revenue_bruto,
    SUM(CASE WHEN profit > 0 THEN profit ELSE 0 END) as gross_profit,
    ABS(SUM(CASE WHEN profit < 0 THEN profit ELSE 0 END)) as gross_loss,
    MIN(time) as first_deal,
    MAX(time) as last_deal
FROM deals;

-- Función para actualizar vistas materializadas
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY deals_by_symbol;
    REFRESH MATERIALIZED VIEW CONCURRENTLY deals_by_account;
    REFRESH MATERIALIZED VIEW deals_summary;
END;
$$ LANGUAGE plpgsql;

-- Trigger para auto-refresh cada 1000 inserts
CREATE OR REPLACE FUNCTION trigger_refresh_views()
RETURNS trigger AS $$
BEGIN
    IF (SELECT COUNT(*) FROM deals) % 1000 = 0 THEN
        PERFORM refresh_materialized_views();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER refresh_views_trigger
    AFTER INSERT ON deals
    FOR EACH STATEMENT
    EXECUTE FUNCTION trigger_refresh_views();

-- Tabla de metadatos de importación
CREATE TABLE import_logs (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT,
    lines_read BIGINT,
    deals_imported BIGINT,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    status VARCHAR(20),
    error_message TEXT
);

CREATE INDEX idx_import_logs_filename ON import_logs (filename);
CREATE INDEX idx_import_logs_started ON import_logs (started_at DESC);
