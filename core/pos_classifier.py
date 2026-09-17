from google.genai import types

from core.exceptions import GeminiAPIError
from core.question_generator import client
from data.models import PartOfSpeechResult


def classify_parts_of_speech(target_words: list[str], target_language: str) -> list[str]:
    """
    Given a list of target-language words (a saved list's target_term
    column), asks Gemini for one abbreviated part-of-speech tag per word,
    in the same order — a single batched call per Save/Save Changes action
    rather than one call per word, so tagging is free-ish regardless of how
    the list was built (typed, pasted, uploaded).
    """
    prompt = f"""Here is a list of words in {target_language}: {target_words}

        For each word, give its most common part of speech as a short abbreviated
        label (e.g. "v.", "n.", "adj.", "adv.", "prep.", "pron.", "conj.", "interj.").
        If a word could plausibly be more than one part of speech, pick whichever
        sense is most common for a standalone vocabulary word (the way a dictionary
        lists its primary entry first). If a word is a multi-word phrase rather than
        a single word, pick the part of speech of the phrase as a whole (e.g. a verb
        phrase like "to give up" is "v.").

        Return one tag per word, in the same order as given.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PartOfSpeechResult,
            ),
        )
    except Exception as e:
        raise GeminiAPIError(f"classify_parts_of_speech failed: {e}") from e

    return response.parsed.parts_of_speech
