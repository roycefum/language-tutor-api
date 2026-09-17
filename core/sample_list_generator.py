from google.genai import types

from core.exceptions import GeminiAPIError
from core.question_generator import client
from core.sample_lists import SAMPLE_LIST_CATEGORIES
from data.models import WordListTranslation


def translate_english_word_list(words: list[str], target_language: str) -> list[str]:
    """
    Translates a list of known-English words into target_language,
    preserving order. Simpler than translator.py's translate_word_list —
    that one also has to *detect* an unknown source language from
    ambiguous input; here the source is always definitively English (the
    master sample-list data), so there's nothing to detect.
    """
    prompt = f"""Here is a list of English words/phrases: {words}

        Translate every one into {target_language}, in the same order as given. Each
        translation should be a natural, direct translation — not a definition or
        explanation. If a word could have multiple valid translations, pick the single
        most common one.

        Give the bare translated word or phrase only — no leading article ("the", "a")
        unless it's grammatically part of the term. Be consistent: every translation
        should follow this same bare-word convention.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=WordListTranslation,
            ),
        )
    except Exception as e:
        raise GeminiAPIError(f"translate_english_word_list failed: {e}") from e

    return response.parsed.translated_words


def generate_sample_pairs(category_key: str, source_language: str, target_language: str) -> list[dict]:
    """
    Builds one sample list's pairs for an arbitrary language pair from the
    English-only master data in sample_lists.py. Only translates the sides
    that actually need it — if either language is English, that side IS
    the master data, so at most 2 Gemini calls happen here (1 if one side
    is English, 2 if neither is — e.g. a Spanish -> French sample list).
    """
    master_words = SAMPLE_LIST_CATEGORIES[category_key]

    source_words = (
        master_words if source_language == "English"
        else translate_english_word_list(master_words, source_language)
    )
    target_words = (
        master_words if target_language == "English"
        else translate_english_word_list(master_words, target_language)
    )

    return [
        {"source word": s, "target word": t}
        for s, t in zip(source_words, target_words)
    ]
