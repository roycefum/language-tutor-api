# Which regional variety of each language the app writes in. Spanish, French
# and English all differ by region in vocabulary, spelling and forms of address
# (Spain's coche/ordenador/vosotros against Latin America's carro/computadora/
# ustedes), and a model left to choose will mix them — a question about one
# word can pick up "departamento" or "celular" along the way. Naming the
# variety once, here, keeps every generated sentence consistent with the
# curated lists (see core/everyday_lists.py, which uses the same variety).
#
# This is data keyed by language, like core/tenses.py: the prompts only read
# it and know nothing about any particular language. A language missing from
# the table is left to the model's default. English has no entry yet.
VARIETY_BY_LANGUAGE = {
    "Spanish": "Spanish as spoken in Spain",
    "French": "French as spoken in France",
}


def get_variety_instruction(target_language):
    """
    The one line the question prompts add so every sentence follows the
    configured variety, or an empty string if this language has none.
    """
    variety = VARIETY_BY_LANGUAGE.get(target_language)
    if not variety:
        return ""
    return (
        f"VARIETY: write in {variety}. Wherever the language differs by region (vocabulary, spelling, forms of address, "
        f"everyday terms), use that variety's choice, never another region's."
    )
