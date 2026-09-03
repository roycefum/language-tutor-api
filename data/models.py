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

class ExtractedVocabList(BaseModel):
    pairs: List[VocabPair]

