-- Adds a nullable part-of-speech tag per vocab pair (e.g. "v.", "n.", "adj.").
-- Populated by a single batched Gemini call at save time (see
-- core/pos_classifier.py / insert_vocab_pairs in data/db.py) — never
-- required, so existing rows and any insert that omits it stay valid.
ALTER TABLE vocab_pairs
  ADD COLUMN IF NOT EXISTS part_of_speech text;
