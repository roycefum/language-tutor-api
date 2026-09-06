# Verb tenses/moods offered per target language for the "Target My Mistakes"
# tense selector — only meaningful for a "verb" list (see list_type on
# vocab_lists). Mirrored on the frontend (a duplicated list, same pattern
# already used for CEFR levels) so the picker doesn't need a network call.
# English, Spanish, and French for now — other languages can be added here
# later without touching the generation logic that reads this.
TENSES_BY_LANGUAGE = {
    "Spanish": [
        {"value": "present", "label": "Present (presente)"},
        {"value": "preterite", "label": "Preterite (pretérito)"},
        {"value": "imperfect", "label": "Imperfect (imperfecto)"},
        {"value": "future", "label": "Future (futuro)"},
        {"value": "conditional", "label": "Conditional (condicional)"},
        {"value": "present_subjunctive", "label": "Present Subjunctive (presente de subjuntivo)"},
        {"value": "present_perfect", "label": "Present Perfect (pretérito perfecto)"},
    ],
    "English": [
        {"value": "present_simple", "label": "Present Simple"},
        {"value": "past_simple", "label": "Past Simple"},
        {"value": "future_simple", "label": "Future Simple"},
        {"value": "present_continuous", "label": "Present Continuous"},
        {"value": "past_continuous", "label": "Past Continuous"},
        {"value": "present_perfect", "label": "Present Perfect"},
    ],
    "French": [
        {"value": "present", "label": "Present (présent)"},
        {"value": "passe_compose", "label": "Present Perfect (passé composé)"},
        {"value": "imperfect", "label": "Imperfect (imparfait)"},
        {"value": "future", "label": "Future (futur simple)"},
        {"value": "conditional", "label": "Conditional (conditionnel)"},
        {"value": "present_subjunctive", "label": "Present Subjunctive (subjonctif présent)"},
        {"value": "pluperfect", "label": "Pluperfect (plus-que-parfait)"},
    ],
}


def get_tense_label(target_language, tense_value):
    """
    Returns the human-readable label for a tense value (e.g. "preterite" ->
    "Preterite (pretérito)"), used to build the prompt instruction naming
    which tense to conjugate in. Returns None if target_language has no
    tense list or tense_value isn't recognized — the caller should fall
    back to "vary it freely" behavior in that case, not error.
    """
    for tense in TENSES_BY_LANGUAGE.get(target_language, []):
        if tense["value"] == tense_value:
            return tense["label"]
    return None
