from pydantic import BaseModel
from fastapi import FastAPI
from core.question_generator import generate_question_batch
from core.cefr import DEFAULT_CEFR_LEVEL
from data.models import Question




class GenerateQuestionsRequest(BaseModel):
    pairs: list[dict]
    source_language: str
    target_language: str
    batch_size: int
    level: str = DEFAULT_CEFR_LEVEL
    # Only meaningful for verb-shaped pairs (see core/tenses.py) — a
    # specific tense to conjugate every verb pair in, instead of the
    # default of varying subject/tense freely across the batch.
    verb_tense: str | None = None
    # Vocab-only reversed-direction mode: shows the target-language word and
    # asks for its source-language translation, instead of the normal
    # fill-in-the-blank production direction.
    flip: bool = False


class SaveListRequest(BaseModel):
    name: str
    source: str
    source_language: str
    target_language: str
    pairs: list[dict]
    list_type: str = "vocab"


class SignUpRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LogoutRequest(BaseModel):
    refresh_token: str


class CreateQuizSessionRequest(BaseModel):
    list_id: str
    questions: list[Question]


class UpdateQuizSessionRequest(BaseModel):
    current_index: int
    status: str | None = None


class CreateAttemptRequest(BaseModel):
    session_id: str
    vocab_pair_id: str | None
    question_text: str
    skill_category: str | None
    was_correct: bool

