-- LICEU 6.0 Workspace + Kanban Enterprise Schema
-- PostgreSQL production schema

CREATE TABLE IF NOT EXISTS workspace (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    max_users INT NOT NULL DEFAULT 10,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workspace_users (
    id UUID PRIMARY KEY,
    workspace_id UUID REFERENCES workspace(id) ON DELETE SET NULL,
    external_username TEXT UNIQUE,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workspace_users_role ON workspace_users(role);
CREATE INDEX IF NOT EXISTS idx_workspace_users_workspace_id ON workspace_users(workspace_id);

CREATE TABLE IF NOT EXISTS kanban_cards (
    id UUID PRIMARY KEY,
    title TEXT,
    entity_type TEXT,
    stage TEXT,
    owner_id UUID,
    source TEXT,
    value NUMERIC,
    risk TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kanban_events (
    id UUID PRIMARY KEY,
    card_id UUID REFERENCES kanban_cards(id) ON DELETE CASCADE,
    event_type TEXT,
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kanban_events_card_id ON kanban_events(card_id);

CREATE TABLE IF NOT EXISTS kanban_actors (
    id UUID PRIMARY KEY,
    card_id UUID REFERENCES kanban_cards(id) ON DELETE CASCADE,
    monolith TEXT,
    status TEXT
);

CREATE INDEX IF NOT EXISTS idx_kanban_actors_card_id ON kanban_actors(card_id);

CREATE TABLE IF NOT EXISTS kanban_john (
    card_id UUID PRIMARY KEY REFERENCES kanban_cards(id) ON DELETE CASCADE,
    suggestion TEXT,
    confidence FLOAT,
    risk TEXT,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kanban_audit (
    id UUID PRIMARY KEY,
    user_id UUID,
    action TEXT,
    card_id UUID REFERENCES kanban_cards(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kanban_audit_card_id ON kanban_audit(card_id);
CREATE INDEX IF NOT EXISTS idx_kanban_audit_user_id ON kanban_audit(user_id);
