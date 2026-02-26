"""Database schema SQL."""

SCHEMA_SQL = """
-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    platform TEXT NOT NULL,
    status TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result_path TEXT,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    discovered_links_count INTEGER DEFAULT 0
);

-- Bulk jobs table
CREATE TABLE IF NOT EXISTS bulk_jobs (
    id TEXT PRIMARY KEY,
    source_file TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    status TEXT NOT NULL,
    total_rows INTEGER,
    processed_rows INTEGER DEFAULT 0,
    error_rows INTEGER DEFAULT 0,
    state_manifest_path TEXT,
    state_index_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Discovered links table
CREATE TABLE IF NOT EXISTS discovered_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_task_id TEXT NOT NULL,
    url TEXT NOT NULL,
    relationship_type TEXT,
    priority_delta INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- Ingestion jobs table
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id TEXT PRIMARY KEY,
    source_file TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    status TEXT NOT NULL,
    total_rows INTEGER,
    processed_rows INTEGER DEFAULT 0,
    error_rows INTEGER DEFAULT 0,
    state_data BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Platform configs table
CREATE TABLE IF NOT EXISTS platform_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT UNIQUE NOT NULL,
    config_path TEXT NOT NULL,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE,
    error TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_status_priority ON tasks(status, priority DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_platform ON tasks(platform);
CREATE INDEX IF NOT EXISTS idx_bulk_jobs_status ON bulk_jobs(status);
CREATE INDEX IF NOT EXISTS idx_discovered_links_source ON discovered_links(source_task_id);
CREATE INDEX IF NOT EXISTS idx_discovered_links_processed ON discovered_links(processed);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion_jobs(status);
"""
