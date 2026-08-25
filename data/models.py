from pydantic import BaseModel
from typing import List



class Question(BaseModel):
    question_text: str
    correct_answer: str
    skill_category: str

class QuestionBatch(BaseModel):
    questions: List[Question]



class VocabPair(BaseModel):
    source_term: str
    target_term: str

class ExtractedVocabList(BaseModel):
    pairs: List[VocabPair]

