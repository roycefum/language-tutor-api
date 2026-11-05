from core.everyday_lists import is_everyday_category
from core.grammar_lists import GRAMMAR_CATEGORIES

# Metadata for the Sample Lists ("Essentials") feature: which categories exist,
# what each is called, and what type of list it makes. The words themselves
# live in hand-written tables — core/everyday_lists.py (the four everyday
# lists, one table for all three languages) and core/grammar_lists.py (the
# grammar-word lists, one table per language). Adding a category means adding
# its table there and one entry below.

# Display label + list_type ("verb" unlocks tense selection on Generate
# Quiz) per category — used both for the bulk first-time generation
# (Settings' "what are you learning?" step) and the on-demand single-
# category catalog in My Lists. Labels are fixed English regardless of the
# app's current UI locale, since the backend has no concept of that.
SAMPLE_CATEGORY_META = {
    "common_words": ("Common Words", "vocab"),
    "common_verbs": ("Common Verbs", "verb"),
    "irregular_verbs": ("Irregular Verbs", "verb"),
    "food": ("Food", "vocab"),
    # Curated grammar-word lists (see core/grammar_lists.py) — "grammar" is a
    # list_type of its own, so quizzes on them get context-rich questions.
    "subject_pronouns": ("Subject Pronouns", "grammar"),
    "object_pronouns": ("Object Pronouns", "grammar"),
    "reflexive_pronouns": ("Reflexive Pronouns", "grammar"),
    "stressed_pronouns": ("Stressed Pronouns", "grammar"),
    "possessives": ("Possessives", "grammar"),
    "articles": ("Articles", "grammar"),
    "definite_articles": ("Definite Articles", "grammar"),
    "indefinite_articles": ("Indefinite Articles", "grammar"),
    "demonstratives": ("Demonstratives", "grammar"),
    "question_words": ("Question Words", "grammar"),
    "relative_pronouns": ("Relative Pronouns", "grammar"),
    "negatives": ("Negatives", "grammar"),
    "indefinites": ("Indefinites", "grammar"),
    "conjunctions": ("Conjunctions", "grammar"),
    "prepositions": ("Prepositions", "grammar"),
}

# Where a language's own grammar uses a different name for a category, the
# name for that target language. Stressed pronouns (French) are called
# prepositional pronouns in Spanish grammar.
TARGET_NAME_OVERRIDES = {
    ("stressed_pronouns", "Spanish"): "Prepositional Pronouns",
}


def category_name(category_key, target_language):
    """The English name a category is shown and saved under for a target language."""
    override = TARGET_NAME_OVERRIDES.get((category_key, target_language))
    return override or SAMPLE_CATEGORY_META[category_key][0]


# How hard each category is, shown as a badge on the Essentials screen.
# One level per category, the same for every language.
CATEGORY_LEVEL = {
    "common_words": "beginner",
    "common_verbs": "beginner",
    "food": "beginner",
    "subject_pronouns": "beginner",
    "articles": "beginner",
    "definite_articles": "beginner",
    "indefinite_articles": "beginner",
    "demonstratives": "beginner",
    "possessives": "beginner",
    "question_words": "beginner",
    "conjunctions": "beginner",
    "stressed_pronouns": "beginner",
    "irregular_verbs": "intermediate",
    "object_pronouns": "intermediate",
    "reflexive_pronouns": "intermediate",
    "negatives": "beginner",
    "indefinites": "intermediate",
    "prepositions": "intermediate",
    "relative_pronouns": "advanced",
}

# Categories generated automatically the first time a user picks a learning
# pair. Empty on purpose: every list is opt-in from the app's Essentials
# screen, so first-time setup is instant (it used to block Settings while
# four lists were generated) and a new user's library starts empty instead
# of filling with lists nobody chose. Add keys here to bring auto-adding back.
STARTER_CATEGORIES = ()


def essentials_for(target_language):
    """
    The Essentials catalog of one target language, in display order: every
    category that has a table for it. Everyday lists exist for all supported
    languages; grammar lists only where that language's table is written (the
    languages are not translations of each other, so each has its own set).
    """
    catalog = []
    for key, (_, list_type) in SAMPLE_CATEGORY_META.items():
        if is_everyday_category(key):
            group = "everyday"
        elif target_language in GRAMMAR_CATEGORIES.get(key, {}):
            group = "grammar"
        else:
            continue
        catalog.append({
            "key": key, "name": category_name(key, target_language), "list_type": list_type, "group": group,
            "level": CATEGORY_LEVEL[key],
        })
    return catalog
