BEGIN;

CREATE TABLE IF NOT EXISTS sheriff_events (
    event_id TEXT PRIMARY KEY,
    body_hash CHAR(64) NOT NULL CHECK (body_hash ~ '^[0-9a-f]{64}$'),
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    subject TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    raw_event JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sheriff_incidents (
    incident_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE REFERENCES sheriff_events(event_id),
    agent_id TEXT NOT NULL,
    task_ref TEXT NOT NULL,
    error_signature TEXT NOT NULL,
    incident_class TEXT NOT NULL CHECK (incident_class IN (
        'I0_SELF_CAUGHT', 'I1_CORRECTNESS', 'I2_PROCESS',
        'I3_CRITICAL_INTEGRITY', 'I4_SAFETY_SECURITY'
    )),
    repeat_count INTEGER NOT NULL CHECK (repeat_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (agent_id, error_signature, repeat_count)
);

CREATE INDEX IF NOT EXISTS sheriff_incidents_agent_signature_idx
    ON sheriff_incidents(agent_id, error_signature, created_at);

CREATE TABLE IF NOT EXISTS sheriff_verdicts (
    verdict_id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL UNIQUE REFERENCES sheriff_incidents(incident_id),
    sheriff_id TEXT NOT NULL,
    root_cause TEXT NOT NULL,
    evidence JSONB NOT NULL,
    discipline_delta INTEGER NOT NULL,
    merit_delta INTEGER NOT NULL,
    hard_hold BOOLEAN NOT NULL,
    decision JSONB NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (jsonb_typeof(evidence) = 'array'),
    CHECK (jsonb_array_length(evidence) > 0)
);

CREATE TABLE IF NOT EXISTS sheriff_remediations (
    remediation_id BIGSERIAL PRIMARY KEY,
    verdict_id TEXT NOT NULL REFERENCES sheriff_verdicts(verdict_id),
    step_order INTEGER NOT NULL CHECK (step_order > 0),
    step_code TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'REQUIRED' CHECK (status IN ('REQUIRED', 'IN_PROGRESS', 'PASS', 'WAIVED_BY_OWNER')),
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (verdict_id, step_order),
    UNIQUE (verdict_id, step_code)
);

CREATE TABLE IF NOT EXISTS sheriff_agent_scores (
    agent_id TEXT PRIMARY KEY,
    discipline_score INTEGER NOT NULL DEFAULT 100 CHECK (discipline_score BETWEEN 0 AND 100),
    merit_points INTEGER NOT NULL DEFAULT 0,
    active_gate TEXT NOT NULL DEFAULT 'NONE' CHECK (active_gate IN ('NONE', 'HEIGHTENED_QC', 'RESTRICTED', 'HOLD', 'HARD_HOLD')),
    incident_count INTEGER NOT NULL DEFAULT 0 CHECK (incident_count >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sheriff_skill_ratings (
    agent_id TEXT PRIMARY KEY,
    rating DOUBLE PRECISION NOT NULL DEFAULT 1500,
    rating_deviation DOUBLE PRECISION NOT NULL DEFAULT 350 CHECK (rating_deviation > 0),
    volatility DOUBLE PRECISION NOT NULL DEFAULT 0.06 CHECK (volatility > 0),
    rated_matches INTEGER NOT NULL DEFAULT 0 CHECK (rated_matches >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sheriff_league_matches (
    match_id TEXT PRIMARY KEY,
    competitor_a TEXT NOT NULL,
    competitor_b TEXT NOT NULL,
    score_a DOUBLE PRECISION NOT NULL CHECK (score_a IN (0.0, 0.5, 1.0)),
    safety_gate_passed BOOLEAN NOT NULL,
    evidence JSONB NOT NULL,
    applied_at TIMESTAMPTZ,
    CHECK (competitor_a <> competitor_b),
    CHECK (jsonb_typeof(evidence) = 'array'),
    CHECK (jsonb_array_length(evidence) > 0)
);

CREATE OR REPLACE FUNCTION sheriff_reject_immutable_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'SHERIFF_IMMUTABLE_RECORD';
END;
$$;

DROP TRIGGER IF EXISTS sheriff_events_immutable ON sheriff_events;
CREATE TRIGGER sheriff_events_immutable
BEFORE UPDATE OR DELETE ON sheriff_events
FOR EACH ROW EXECUTE FUNCTION sheriff_reject_immutable_mutation();

DROP TRIGGER IF EXISTS sheriff_verdicts_immutable ON sheriff_verdicts;
CREATE TRIGGER sheriff_verdicts_immutable
BEFORE UPDATE OR DELETE ON sheriff_verdicts
FOR EACH ROW EXECUTE FUNCTION sheriff_reject_immutable_mutation();

INSERT INTO sheriff_agent_scores(agent_id)
VALUES ('LESTER'), ('DUNCAN'), ('DJANGO'), ('JINGO'), ('SHERIFF')
ON CONFLICT (agent_id) DO NOTHING;

INSERT INTO sheriff_skill_ratings(agent_id)
VALUES ('LESTER'), ('DUNCAN'), ('DJANGO'), ('JINGO'), ('SHERIFF')
ON CONFLICT (agent_id) DO NOTHING;

COMMIT;
