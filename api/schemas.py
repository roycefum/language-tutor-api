from pydantic import BaseModel
from fastapi import FastAPI
from core.question_generator import generate_question_batch




class GenerateQuestionsRequest(BaseModel):
    pairs: list[dict]
    source_language: str
    target_language: str
    batch_size: int


