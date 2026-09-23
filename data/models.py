from pydantic import BaseModel
from typing import List, Optional



class Question(BaseModel):
    question_text: str
    correct_answer: str
    skill_category: str
    # Which vocab pair this question was generated from, so an attempt at
    # answering it can be tracked back to a specific word. Stamped by
    # generate_question_batch() after Gemini returns — not something Gemini
    # is asked to produce itself. None for pairs with no id (ad-hoc/unsaved
    # lists, which have no attempt history to track anyway).
    vocab_pair_id: Optional[str] = None

class QuestionBatch(BaseModel):
    questions: List[Question]



class VocabPair(BaseModel):
    source_term: str
    target_term: str


class LanguageDetection(BaseModel):
    source_language: str
    target_language: str

class ExtractedVocabList(BaseModel):
    pairs: List[VocabPair]


class TranslationResult(BaseModel):
    # Detected from the words themselves, not asked of the caller — a
    # monolingual list (e.g. from a textbook photo/paste with no
    # translations) doesn't come with a declared source language.
    source_language: str
    pairs: List[VocabPair]


class WordListTranslation(BaseModel):
    # One translation per input word, same order — see
    # translate_english_word_list() in core/sample_list_generator.py.
    translated_words: List[str]


class VocabListMeta(BaseModel):
    """
    The metadata cluster that used to travel as 4-5 separate positional
    parameters through create_list/update_list/save_list and the
    /save-list API schema — name, source, and the language pair are what
    identifies a list; list_type is stored alongside them. Bundling them
    here means a function taking a VocabListMeta can't have its fields
    passed in the wrong order, and model_dump() hands back exactly the
    dict these functions already needed to build for an insert/update.
    """
    name: str
    source: str
    source_language: str
    target_language: str
    list_type: str = "vocab"


class PatternAnalysis(BaseModel):
    # One or two encouraging, specific sentences naming what the learner is
    # doing well and what pattern is giving them trouble — shown directly
    # to the user on Generate Quiz / Quiz Complete.
    message: str
    # Numbers ("n") of the mistakes the analyzer was shown that
    # best support the pattern it named. The server turns these into
    # "typed -> correct" examples itself rather than trusting the model to
    # quote answers back accurately.
    evidence_indexes: List[int]
    # One sentence telling the question writer which skill to exercise
    # (e.g. "present-tense nosotros forms of -ar verbs"). Empty string when
    # there's no clear pattern.
    focus: str
    # Pair ids (from the full list) that would give the most practice on
    # that pattern — used to pick the words for the targeted quiz.
    targeted_pair_ids: List[str]