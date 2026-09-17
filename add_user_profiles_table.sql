-- One row per user, holding account-level profile/preference data — the
-- first thing here is the learning language pair (drives forced-redirect
-- to Settings on first login, and one-time sample-list generation), but
-- the table is deliberately general-purpose so future account-level data
-- (display name, streak stats, whatever) has a home without needing a new
-- one-off table each time.
CREATE TABLE IF NOT EXISTS user_profiles (
  user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  -- Null until the user completes the "what are you learning?" step in
  -- Settings — that null-ness is itself the "first time" signal used to
  -- decide whether saving this pair should also trigger sample-list
  -- generation, so no separate "onboarding complete" flag is needed.
  learning_source_language text,
  learning_target_language text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
