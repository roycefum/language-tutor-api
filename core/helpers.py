import unicodedata
from data.db import save_list


def split_ambiguous_pair(source_word, target_word):
    """
    If a target word contains multiple meanings separated by '/' or ',',
    split it into separate pairs, one per meaning, all sharing the same
    source_word. Returns a list of pairs (always at least one).
    """
    if "/" in target_word:
        split_terms = target_word.split("/")
    elif "," in target_word:
        split_terms = target_word.split(",")
    else:
        split_terms = [target_word]

    stripped_terms = [p.strip() for p in split_terms]
    return [{"source word": source_word, "target word": term} for term in stripped_terms]


def parse_pasted_list(raw_text):
    """
    Parses raw pasted/uploaded text into a list of vocab pairs. Supports
    tab, "->", or ":" as separators between term and definition, tried in
    that order per line. Lines that don't produce exactly 2 parts with any
    separator are skipped. Returns a flat list of pairs (ambiguous ones
    already split via split_ambiguous_pair).
    """
    separators = ["\t", "->", ":"]
    lines = raw_text.split("\n")
    all_pairs = []

    for line in lines:
        line = line.strip()
        if len(line) > 0:
            parts = None
            for sep in separators:
                candidate = line.split(sep)
                if len(candidate) == 2:
                    parts = candidate
                    break
            if parts is not None:
                source_term = parts[0].strip()
                target_term = parts[1].strip()
                all_pairs.extend(split_ambiguous_pair(source_term, target_term))

    return all_pairs


def chunk_list(lst, size):
    """Splits a list into sublists of at most `size` items each."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def remove_accents(text):
    """Strips diacritical marks (accents) from a string for lenient answer matching."""
    normalized = unicodedata.normalize('NFKD', text)
    return ''.join(char for char in normalized if not unicodedata.combining(char))


def save_list_if_valid(user_id, name, source, source_language, target_language, pairs):
    """
    Thin wrapper around data.db.save_list(). Kept as its own function so
    API routes have one consistent entry point for saving a list, matching
    the naming/shape used elsewhere in the codebase.
    """
    return save_list(user_id, name, source, source_language, target_language, pairs)