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


class PatternAnalysis(BaseModel):
    # One encouraging, specific sentence naming what the learner is doing
    # well and what pattern (e.g. a stem-change type, tense, irregularity)
    # is giving them trouble — shown directly to the user on Generate Quiz.
    message: str
    # Pair ids (from the full list) chosen to reinforce that same weak
    # pattern — used for the "Target My Mistakes" quiz option.
    targeted_pair_ids: List[str]

