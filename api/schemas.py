from pydantic import BaseModel
from fastapi import FastAPI
from core.question_generator import generate_question_batch
from core.cefr import DEFAULT_CEFR_LEVEL
from data.models import Question, VocabListMeta




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
    # Only set for a "Target My Mistakes" quiz: one sentence describing the
    # skill the learner is struggling with (from the quiz-insight analysis
    # of their last quiz), so the questions get written to exercise it.
    focus: str | None = None
    # "vocab" or "verb" — decides which prompt this batch uses. A verb-
    # shaped pair ("to walk"/"caminar") is tested as an ordinary word in a
    # vocab list (bare infinitive, no conjugation) and conjugated in a verb
    # list; verb_tense alone can't tell these apart, since it's null for
    # both a vocab list and a verb list set to "Mixed".
    list_type: str = "vocab"


class SaveListRequest(VocabListMeta):
    # Inherits name/source/source_language/target_language/list_type from
    # VocabListMeta — the same metadata cluster save_list() itself takes —
    # so the request IS a VocabListMeta and can be passed straight through
    # without re-listing these fields or reconstructing the object.
    pairs: list[dict]


class SignUpRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LogoutRequest(BaseModel):
    refresh_token: str


class RequestPasswordResetRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    access_token: str
    refresh_token: str
    new_password: str


class CreateQuizSessionRequest(BaseModel):
    list_id: str
    questions: list[Question]
    verb_tense: str | None = None


class UpdateQuizSessionRequest(BaseModel):
    current_index: int
    status: str | None = None


class CreateAttemptRequest(BaseModel):
    session_id: str
    vocab_pair_id: str | None
    question_text: str
    skill_category: str | None
    was_correct: bool
    user_answer: str
    correct_answer: str


class DetectLanguageRequest(BaseModel):
    # Each dict is {"source word": ..., "target word": ...} — the same
    # plain shape /parse-vocab-text returns and the frontend already uses,
    # so no reshaping is needed on either side of this call.
    pairs: list[dict[str, str]]


class TranslateWordListRequest(BaseModel):
    words: list[str]
    target_language: str


class RenameListRequest(BaseModel):
    name: str


class UpdateListPairsRequest(BaseModel):
    source: str
    source_language: str
    target_language: str
    pairs: list[dict[str, str]]
    list_type: str = "vocab"


class UpdateProfileRequest(BaseModel):
    source_language: str
    target_language: str


class GenerateSampleListRequest(BaseModel):
    category: str
    source_language: str
    target_language: str

