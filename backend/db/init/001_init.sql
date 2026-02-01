-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ======================
-- USERS TABLE (Clerk-backed)
-- ======================
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,              -- Clerk user_id (string)
    email TEXT NOT NULL UNIQUE,
    username TEXT,                    -- maps from UI "name"

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ======================
-- SERVERS TABLE (User-owned)
-- ======================
CREATE TABLE IF NOT EXISTS servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id TEXT NOT NULL,             -- MUST match users.id type
    server_tag TEXT NOT NULL,           -- user-facing server name

    ip_address INET NOT NULL,
    hostname TEXT,

    -- auth-related (used later)
    ssh_username TEXT,
    ssh_key_path TEXT,
    ssh_password_encrypted TEXT,

    -- dynamic UI fields (added but can be unused now)
    additional_components JSONB,

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT fk_servers_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    -- server_tag unique PER USER (not global)
    CONSTRAINT unique_server_per_user
        UNIQUE (user_id, server_tag)
);

-- ======================
-- MONITORING CONFIGS (used later)
-- ======================
CREATE TABLE IF NOT EXISTS monitoring_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    server_id UUID NOT NULL,
    monitor_path TEXT,
    interval_seconds INT DEFAULT 60,

    cpu_enabled BOOLEAN DEFAULT true,
    memory_enabled BOOLEAN DEFAULT true,
    disk_enabled BOOLEAN DEFAULT true,
    network_enabled BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT fk_monitoring_server
        FOREIGN KEY (server_id)
        REFERENCES servers(id)
        ON DELETE CASCADE
);

-- ======================
-- POLICIES TABLE (used later)
-- ======================
CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    server_id UUID NOT NULL,
    policy_type TEXT NOT NULL,
    policy_data JSONB NOT NULL,

    created_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT fk_policy_server
        FOREIGN KEY (server_id)
        REFERENCES servers(id)
        ON DELETE CASCADE
);

-- ======================
-- INDEXES
-- ======================
CREATE INDEX IF NOT EXISTS idx_servers_user_id ON servers(user_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_server_id ON monitoring_configs(server_id);
CREATE INDEX IF NOT EXISTS idx_policies_server_id ON policies(server_id);