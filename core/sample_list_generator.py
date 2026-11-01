from core.everyday_lists import everyday_pairs, is_everyday_category
from core.grammar_lists import grammar_pairs, is_grammar_category


def generate_sample_pairs(category_key: str, source_language: str, target_language: str) -> list[dict]:
    """
    Builds one sample (Essentials) list's pairs for a language pair. Every
    category is a hand-written, reviewed table in this repo — nothing is
    generated or translated at request time, so this is instant and free:
    - everyday lists (core/everyday_lists.py) are assembled from the two
      matching language columns, so any pair of the three supported languages
      works;
    - grammar lists (core/grammar_lists.py) are per target language, and
      source_language only matters to the caller.
    Raises ValueError if the category or language isn't covered.
    """
    if is_everyday_category(category_key):
        pairs = everyday_pairs(category_key, source_language, target_language)
        if pairs is None:
            raise ValueError(f"No {category_key} list for {source_language} -> {target_language}")
        return pairs
    if is_grammar_category(category_key):
        pairs = grammar_pairs(category_key, target_language)
        if pairs is None:
            raise ValueError(f"No {category_key} list for {target_language}")
        return pairs
    raise ValueError(f"Unknown sample list category: {category_key}")
