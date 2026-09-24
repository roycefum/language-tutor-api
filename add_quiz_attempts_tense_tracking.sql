-- Adds developer-facing tense tracking to quiz_attempts — queried directly
-- in Supabase (SQL editor or Table Editor), not surfaced anywhere in the
-- app. tense is copied from the question's own tense field (present for
-- verb-conjugation questions, null for vocab); used_tense_hint records
-- whether the "not sure which tense?" reveal was tapped before answering.
ALTER TABLE quiz_attempts
  ADD COLUMN IF NOT EXISTS tense text,
  ADD COLUMN IF NOT EXISTS used_tense_hint boolean NOT NULL DEFAULT false;
