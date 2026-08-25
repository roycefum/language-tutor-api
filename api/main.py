from fastapi import FastAPI
from core.question_generator import generate_question_batch
from api.schemas import GenerateQuestionsRequest


app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "API is running"}


@app.post("/generate-questions")
def route_generate_question_batch(request: GenerateQuestionsRequest):
    result = generate_question_batch(
        request.pairs,
        request.source_language,
        request.target_language,
        request.batch_size
    )
    return result