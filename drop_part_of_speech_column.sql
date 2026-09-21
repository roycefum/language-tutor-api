-- Reverts add_part_of_speech_column.sql — the part-of-speech feature was
-- removed (a bare "v."/"n." tag with no definition wasn't useful on its
-- own). Safe to run anytime; the column is otherwise just dead weight.
ALTER TABLE vocab_pairs
  DROP COLUMN IF EXISTS part_of_speech;
