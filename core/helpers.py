import re
import unicodedata
from data.db import save_list

BULLET_PREFIX_RE = re.compile(r"^\s*(?:[-*•‣▪·]|\d+[.)])\s+")

# Tried in order per line, first match wins. Ordered from most specific/
# unambiguous (won't appear inside a normal word) to loosest (more likely to
# misfire on legitimate word content), so an unambiguous separator is always
# preferred over a loose one when a line happens to contain both.
SEPARATOR_PATTERNS = [
    r"\t",
    r"->",
    r":",
    r"=",
    r"\|",
    r"[—–]",  # em dash, en dash
    r"\s-\s",  # " - " — common, but only with surrounding spaces so it
    # doesn't split hyphenated words like "well-known"
    r"\s{2,}",  # 2+ spaces, e.g. from a pasted table
    r"\bto\b",  # natural phrasing, e.g. "hello to hola"
]


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
    Parses raw pasted/uploaded text into a list of vocab pairs. Tries a
    range of separator styles per line (see SEPARATOR_PATTERNS) and splits
    on the first match only, so a separator character appearing again later
    in the line (e.g. inside a word) doesn't break the split. Strips common
    list-formatting noise (bullets, numbering) before matching, and light
    trailing punctuation after.

    Lines that still can't be split are NOT silently dropped — they're
    returned separately as skipped_lines so the caller can tell the user
    what didn't parse, instead of pairs quietly going missing.

    Returns (pairs, skipped_lines).
    """
    lines = raw_text.split("\n")
    all_pairs = []
    skipped_lines = []

    for raw_line in lines:
        line = raw_line.strip()
        if len(line) == 0:
            continue

        line = BULLET_PREFIX_RE.sub("", line)

        parts = None
        for pattern in SEPARATOR_PATTERNS:
            match = re.search(pattern, line)
            if match:
                source_term = line[: match.start()].strip(" .,;")
                target_term = line[match.end() :].strip(" .,;")
                if source_term and target_term:
                    parts = (source_term, target_term)
                    break

        if parts is not None:
            all_pairs.extend(split_ambiguous_pair(parts[0], parts[1]))
        else:
            skipped_lines.append(raw_line)

    return all_pairs, skipped_lines


def chunk_list(lst, size):
    """Splits a list into sublists of at most `size` items each."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def remove_accents(text):
    """Strips diacritical marks (accents) from a string for lenient answer matching."""
    normalized = unicodedata.normalize('NFKD', text)
    return ''.join(char for char in normalized if not unicodedata.combining(char))


def save_list_if_valid(user_id, name, source, source_language, target_language, pairs, list_type="vocab"):
    """
    Thin wrapper around data.db.save_list(). Kept as its own function so
    API routes have one consistent entry point for saving a list, matching
    the naming/shape used elsewhere in the codebase.
    """
    return save_list(user_id, name, source, source_language, target_language, pairs, list_type)