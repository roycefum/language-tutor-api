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

-- Row-level security: each user can only see and change their own row.
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "read own profile" ON user_profiles
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "create own profile" ON user_profiles
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "update own profile" ON user_profiles
  FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Policies only filter rows; the role still needs table-level privileges
-- or every query fails with "permission denied" (42501). Newer Supabase
-- projects no longer grant these automatically on tables created in SQL.
GRANT SELECT, INSERT, UPDATE ON public.user_profiles TO authenticated;
