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
    "conjunctions": ("Conjunctions", "grammar"),
    "prepositions": ("Prepositions", "grammar"),
    "question_words": ("Question Words", "grammar"),
    "possessives": ("Possessives", "grammar"),
    "negatives_indefinites": ("Negatives and Indefinites", "grammar"),
    "relative_pronouns": ("Relative Pronouns", "grammar"),
}

# Categories generated automatically the first time a user picks a learning
# pair. Empty on purpose: every list is opt-in from the app's Essentials
# screen, so first-time setup is instant (it used to block Settings while
# four lists were generated) and a new user's library starts empty instead
# of filling with lists nobody chose. Add keys here to bring auto-adding back.
STARTER_CATEGORIES = ()
