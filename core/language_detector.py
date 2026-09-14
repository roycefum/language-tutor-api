from google.genai import types

from core.exceptions import GeminiAPIError
from core.question_generator import client
from data.models import LanguageDetection

# Mirrors the frontend's LANGUAGES constant (src/lib/types.ts) — the only
# languages the app actually supports end to end (Generate Quiz's tense
# picker, CEFR guidance, etc. are all keyed off these three).
SUPPORTED_LANGUAGES = ["English", "Spanish", "French"]

# A handful of pairs is plenty of signal for a closed 3-way classification,
# and keeps the prompt (and cost) small regardless of how long the list is.
SAMPLE_SIZE = 5


def detect_languages(pairs: list[dict]) -> LanguageDetection:
    """
    Given a sample of parsed {"source word", "target word"} pairs, asks
    Gemini which of SUPPORTED_LANGUAGES each side is in. Uses several pairs
    together rather than a single word, since one word in isolation can be
    ambiguous (shared cognates, short function words) in a way a whole
    sample usually isn't.
    """
    sample = pairs[:SAMPLE_SIZE]
    languages_list = ", ".join(SUPPORTED_LANGUAGES)

    prompt = f"""Here is a sample of word-translation pairs from a vocabulary list a language
        learner uploaded: {sample}

        Each pair has a "source word" and a "target word". Determine which language the source
        words are written in, and which language the target words are written in.

        Only choose from these languages: {languages_list}. Pick the closest match even if a
        single word looks ambiguous on its own — base your answer on the whole sample together,
        not any one pair in isolation.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LanguageDetection,
            ),
        )
    except Exception as e:
        raise GeminiAPIError(f"detect_languages failed: {e}") from e

    return response.parsed
