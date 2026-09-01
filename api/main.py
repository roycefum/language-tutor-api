from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from core.question_generator import generate_question_batch
from core.extraction import extract_vocab_from_image
from core.exceptions import GeminiAPIError, AuthError
from api.schemas import (
    GenerateQuestionsRequest,
    SaveListRequest,
    SignUpRequest,
    LoginRequest,
    LogoutRequest,
    CreateQuizSessionRequest,
    UpdateQuizSessionRequest,
)
from core.helpers import save_list_if_valid, parse_pasted_list
from auth.supabase_auth import sign_up, sign_in, sign_out
from api.deps import get_current_user_id, bearer_scheme
from data.db import (
    create_quiz_session,
    update_quiz_session,
    get_active_sessions,
    get_user_lists,
    get_list_with_pairs,
    delete_list_and_pairs,
)


app = FastAPI()


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

@app.exception_handler(GeminiAPIError)
def handle_gemini_api_error(request: Request, exc: GeminiAPIError):
    return JSONResponse(
        status_code=502,
        content={"detail": f"Gemini API request failed: {exc}"},
    )


@app.exception_handler(AuthError)
def handle_auth_error(request: Request, exc: AuthError):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def read_root():
    return {"status": "API is running"}


# ============================================================
# AUTH
# ============================================================

@app.post("/signup")
def route_signup(request: SignUpRequest):
    response = sign_up(request.email, request.password)
    return {
        "user_id": response.user.id if response.user else None,
        "email": response.user.email if response.user else None,
        # Supabase requires email confirmation by default before a session is issued.
        "confirmation_required": response.session is None,
    }


@app.post("/login")
def route_login(request: LoginRequest):
    response = sign_in(request.email, request.password)
    return {
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
        "user_id": response.user.id,
    }


@app.post("/logout")
def route_logout(request: LogoutRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    sign_out(credentials.credentials, request.refresh_token)
    return {"status": "logged out"}


# ============================================================
# VOCAB LISTS
# ============================================================

@app.post("/save-list")
def route_save_list(request: SaveListRequest, current_user_id: str = Depends(get_current_user_id)):
    list_id = save_list_if_valid(
        current_user_id,
        request.name,
        request.source,
        request.source_language,
        request.target_language,
        request.pairs
    )
    return {"list_id": list_id}


@app.get("/lists")
def route_get_user_lists(current_user_id: str = Depends(get_current_user_id)):
    lists = get_user_lists(current_user_id)
    return {"lists": lists}


@app.get("/lists/{list_id}")
def route_get_list(list_id: str, current_user_id: str = Depends(get_current_user_id)):
    list_data = get_list_with_pairs(list_id, current_user_id)
    if list_data is None:
        raise HTTPException(status_code=404, detail="List not found")
    return list_data


@app.delete("/lists/{list_id}")
def route_delete_list(list_id: str, current_user_id: str = Depends(get_current_user_id)):
    deleted = delete_list_and_pairs(list_id, current_user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="List not found")
    return {"status": "deleted"}


@app.post("/extract-vocab-from-image")
async def route_extract_vocab_from_image(file: UploadFile = File(...)):
    # No auth dependency here: anonymous users can build lists (including
    # via photo extraction) without persistence, same as /generate-questions.
    image_bytes = await file.read()
    pairs = extract_vocab_from_image(image_bytes, file.content_type)
    return {"pairs": [p.model_dump() for p in pairs]}


@app.post("/parse-vocab-text")
async def route_parse_vocab_text(raw_text: str = Form(None), file: UploadFile = File(None)):
    # Covers both "paste text" and "upload file" input methods, since both
    # end up as plain text fed to the same parser. Same anonymous-use
    # precedent as /generate-questions and /extract-vocab-from-image.
    if file is not None:
        try:
            text = (await file.read()).decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be plain text")
    elif raw_text is not None:
        text = raw_text
    else:
        raise HTTPException(status_code=400, detail="Provide either raw_text or file")

    pairs = parse_pasted_list(text)
    return {"pairs": pairs}


# ============================================================
# QUESTION GENERATION
# ============================================================

@app.post("/generate-questions")
def route_generate_question_batch(request: GenerateQuestionsRequest):
    result = generate_question_batch(
        request.pairs,
        request.source_language,
        request.target_language,
        request.batch_size
    )
    return result


# ============================================================
# QUIZ SESSIONS — persisted, resumable quiz progress
# ============================================================

@app.post("/quiz-sessions")
def route_create_quiz_session(request: CreateQuizSessionRequest, current_user_id: str = Depends(get_current_user_id)):
    session_id = create_quiz_session(current_user_id, request.list_id, request.questions)
    return {"session_id": session_id}


@app.patch("/quiz-sessions/{session_id}")
def route_update_quiz_session(session_id: str, request: UpdateQuizSessionRequest, current_user_id: str = Depends(get_current_user_id)):
    update_quiz_session(session_id, current_user_id, request.current_index)
    return {"status": "updated"}


@app.get("/quiz-sessions")
def route_get_active_sessions(current_user_id: str = Depends(get_current_user_id)):
    sessions = get_active_sessions(current_user_id)
    return {"sessions": sessions or []}
