from google.genai import types

from core.exceptions import GeminiAPIError
from core.language_detector import SUPPORTED_LANGUAGES
from core.question_generator import client
from data.models import TranslationResult


def translate_word_list(words: list[str], target_language: str) -> TranslationResult:
    """
    Given a plain list of single words (no translations — e.g. parsed from
    a monolingual textbook photo/paste where every line failed to split
    into a pair), asks Gemini to (1) detect which SUPPORTED_LANGUAGES the
    words are written in, and (2) translate each one into target_language,
    preserving order. Combines detection and translation in one call
    rather than two, since the translation step needs to know the source
    language anyway to do a good job.
    """
    languages_list = ", ".join(SUPPORTED_LANGUAGES)

    prompt = f"""Here is a list of words from a vocabulary list: {words}

        First, determine which language these words are written in. Only choose from these
        languages: {languages_list} — pick the closest match even if a single word looks
        ambiguous on its own, basing your answer on the whole list together.

        Then translate every word into {target_language}, in the same order as given. Each
        translation should be a natural, direct translation of that specific word — not a
        definition or explanation. If a word could have multiple valid translations, pick the
        single most common one.

        Give the bare translated word or phrase only — no leading article ("the", "a") unless
        the source word's own article makes it grammatically part of the term (e.g. French "le
        rhume" -> "cold", not "the cold"). Be consistent: every translation should follow this
        same bare-word convention.

        Return each original word as the "source_term" and its translation as "target_term".
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TranslationResult,
            ),
        )
    except Exception as e:
        raise GeminiAPIError(f"translate_word_list failed: {e}") from e

    return response.parsed
