CREATE TABLE IF NOT EXISTS script_uploads (
    id UUID PRIMARY KEY,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_scenes INTEGER NOT NULL DEFAULT 0,
    total_pages_decimal NUMERIC(6,2) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'parsed'
);

CREATE TABLE IF NOT EXISTS day_plans (
    id UUID PRIMARY KEY,
    upload_id UUID NOT NULL REFERENCES script_uploads(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    shooting_date DATE,
    total_cost NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_minutes NUMERIC(8,2) NOT NULL DEFAULT 0,
    total_pages_decimal NUMERIC(6,2) NOT NULL DEFAULT 0,
    location_summary JSONB NOT NULL DEFAULT '[]'::jsonb,
    cast_summary JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS scenes (
    id UUID PRIMARY KEY,
    upload_id UUID NOT NULL REFERENCES script_uploads(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    sequence_index INTEGER NOT NULL DEFAULT 0,
    slugline TEXT NOT NULL,
    page_eighths INTEGER NOT NULL,
    page_decimal NUMERIC(6,3) NOT NULL,
    estimated_minutes NUMERIC(8,2) NOT NULL,
    location TEXT NOT NULL,
    day_night TEXT NOT NULL,
    estimated_cost NUMERIC(12,2) NOT NULL DEFAULT 0,
    script_day INTEGER,
    schedule_day_id UUID REFERENCES day_plans(id),
    synopsis TEXT
);

CREATE TABLE IF NOT EXISTS scene_cast (
    id SERIAL PRIMARY KEY,
    scene_id UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    performer_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scene_props (
    id SERIAL PRIMARY KEY,
    scene_id UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    prop_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rate_cards (
    id SERIAL PRIMARY KEY,
    category TEXT NOT NULL,
    item_name TEXT NOT NULL,
    unit TEXT NOT NULL,
    base_rate NUMERIC(12,2) NOT NULL,
    overtime_rate NUMERIC(12,2) NOT NULL DEFAULT 0,
    is_default BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS day_plan_scenes (
    id SERIAL PRIMARY KEY,
    day_plan_id UUID NOT NULL REFERENCES day_plans(id) ON DELETE CASCADE,
    scene_id UUID NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    position INTEGER NOT NULL DEFAULT 0,
    UNIQUE(day_plan_id, scene_id)
);

CREATE INDEX IF NOT EXISTS idx_scenes_upload ON scenes (upload_id);
CREATE INDEX IF NOT EXISTS idx_day_plans_upload ON day_plans (upload_id);
CREATE INDEX IF NOT EXISTS idx_day_plan_scenes_plan ON day_plan_scenes (day_plan_id);

CREATE TABLE IF NOT EXISTS actor_compensation (
    id SERIAL PRIMARY KEY,
    actor_name VARCHAR NOT NULL UNIQUE,
    daily_rate FLOAT NOT NULL DEFAULT 0.0,
    overtime_rate FLOAT NOT NULL DEFAULT 0.0,
    union_status VARCHAR NOT NULL DEFAULT 'NON_SAG',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_actor_compensation_name ON actor_compensation(actor_name);

CREATE TABLE IF NOT EXISTS location_compensation (
    id SERIAL PRIMARY KEY,
    location_name VARCHAR NOT NULL UNIQUE,
    daily_fee FLOAT NOT NULL DEFAULT 0.0,
    permits_cost FLOAT NOT NULL DEFAULT 0.0,
    insurance_cost FLOAT NOT NULL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_location_compensation_name ON location_compensation(location_name);

CREATE TABLE IF NOT EXISTS character_assignments (
    id SERIAL PRIMARY KEY,
    upload_id UUID NOT NULL REFERENCES script_uploads(id) ON DELETE CASCADE,
    character_name TEXT NOT NULL,
    actor_id INTEGER REFERENCES actor_compensation(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(upload_id, character_name)
);

CREATE INDEX IF NOT EXISTS idx_character_assignments_actor ON character_assignments(actor_id);

CREATE TABLE IF NOT EXISTS schedule_day_overrides (
    id SERIAL PRIMARY KEY,
    upload_id UUID NOT NULL REFERENCES script_uploads(id) ON DELETE CASCADE,
    script_day INTEGER NOT NULL,
    shooting_location TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(upload_id, script_day)
);

CREATE INDEX IF NOT EXISTS idx_schedule_day_overrides_upload ON schedule_day_overrides(upload_id);
