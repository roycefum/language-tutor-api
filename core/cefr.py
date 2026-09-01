# Sentence-complexity guidance per CEFR level, for calibrating the
# *surrounding sentence* of a generated quiz question — not the target word
# itself, which is whatever the user put in their vocab list. Synthesized
# from the official Council of Europe CEFR Global Scale, Vocabulary Range,
# and Grammatical Accuracy descriptors (Common European Framework of
# Reference for Languages), not just a rough approximation of "beginner"
# vs "advanced."
CEFR_LEVEL_GUIDANCE = {
    "A1": (
        "The learner is at CEFR level A1 (Breakthrough). Use only short, simple "
        "sentences (roughly 4-8 words) in the present tense. Use only the most "
        "common, everyday vocabulary in the surrounding sentence (family, "
        "numbers, colors, common objects, basic daily routines). Do not use "
        "subordinate clauses, idioms, or compound sentences — one simple clause only."
    ),
    "A2": (
        "The learner is at CEFR level A2 (Waystage). Use short, simple sentences "
        "describing familiar everyday situations (shopping, family, routine, "
        "local geography, work). Present and simple past tense are allowed. At "
        "most one simple connecting clause (e.g. \"and\", \"but\", \"because\") is "
        "allowed. Avoid idioms and abstract vocabulary."
    ),
    "B1": (
        "The learner is at CEFR level B1 (Threshold). Use natural, connected "
        "sentences on familiar everyday topics (family, hobbies, work, travel, "
        "current events). Present, past, and future tense are all allowed, along "
        "with reasoning or explanation clauses (e.g. \"because\", \"although\", "
        "\"when\"). Avoid highly specialized or abstract vocabulary and idiomatic "
        "expressions."
    ),
    "B2": (
        "The learner is at CEFR level B2 (Vantage). Use clear, well-structured "
        "sentences that may address more general or abstract topics, with varied "
        "vocabulary and natural connectors. Some complex sentence structures and "
        "less common vocabulary are fine, but avoid highly idiomatic or "
        "colloquial language."
    ),
    "C1": (
        "The learner is at CEFR level C1 (Advanced). Use fluent, natural "
        "sentences with sophisticated structure and vocabulary, including "
        "idiomatic expressions and colloquialisms where natural. The topic may "
        "be abstract, specialized, or complex."
    ),
    "C2": (
        "The learner is at CEFR level C2 (Mastery). Use fully natural, "
        "native-level language with no simplification — idiomatic expressions, "
        "nuanced vocabulary, and complex sentence structures are all "
        "appropriate, exactly as a native speaker would write."
    ),
}

DEFAULT_CEFR_LEVEL = "A1"


def get_cefr_guidance(level):
    """Returns the prompt guidance for a CEFR level string, falling back to
    the default level for anything unrecognized rather than erroring —
    malformed/missing level shouldn't break question generation."""
    return CEFR_LEVEL_GUIDANCE.get(level, CEFR_LEVEL_GUIDANCE[DEFAULT_CEFR_LEVEL])
