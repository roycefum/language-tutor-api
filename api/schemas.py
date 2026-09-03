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


class SaveListRequest(BaseModel):
    name: str
    source: str
    source_language: str
    target_language: str
    pairs: list[dict]


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


class CreateAttemptRequest(BaseModel):
    session_id: str
    vocab_pair_id: str | None
    question_text: str
    skill_category: str | None
    was_correct: bool

