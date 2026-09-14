from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from core.question_generator import generate_question_batch, analyze_missed_pattern
from core.extraction import extract_vocab_from_image
from core.language_detector import detect_languages
from core.translator import translate_word_list
from core.exceptions import GeminiAPIError, AuthError
from api.schemas import (
    GenerateQuestionsRequest,
    SaveListRequest,
    SignUpRequest,
    LoginRequest,
    LogoutRequest,
    CreateQuizSessionRequest,
    UpdateQuizSessionRequest,
    CreateAttemptRequest,
    DetectLanguageRequest,
    TranslateWordListRequest,
    RenameListRequest,
    UpdateListPairsRequest,
)
from core.helpers import save_list_if_valid, parse_pasted_list
from auth.supabase_auth import sign_up, sign_in, sign_out, delete_own_account
from api.deps import get_current_user_id, get_db_client, bearer_scheme
from data.db import (
    create_quiz_session,
    update_quiz_session,
    get_active_sessions,
    get_completed_sessions,
    delete_quiz_session,
    delete_stale_completed_sessions,
    get_quiz_history_for_list,
    get_user_lists,
    get_list_with_pairs,
    delete_list_and_pairs,
    rename_list,
    update_list_pairs,
    delete_all_user_data,
    create_quiz_attempt,
    get_attempts_for_session,
    select_quiz_pairs_for_list,
    get_missed_pairs_for_list,
)


app = FastAPI()

# Permissive pre-launch: no real users yet, and the Expo app has no fixed
# origin during development (simulator, physical device, Expo Go all differ).
# Tighten to specific origins before this is client-facing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "email": response.user.email,
    }


@app.post("/logout")
def route_logout(request: LogoutRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    sign_out(credentials.credentials, request.refresh_token)
    return {"status": "logged out"}


@app.delete("/account")
def route_delete_account(
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    # App data must go first — once the auth user is deleted there's no
    # user_id left to scope the cleanup query to.
    delete_all_user_data(client, current_user_id)
    delete_own_account(credentials.credentials)
    return {"status": "deleted"}


# ============================================================
# VOCAB LISTS
# ============================================================

@app.post("/save-list")
def route_save_list(
    request: SaveListRequest,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    list_id = save_list_if_valid(
        client,
        current_user_id,
        request.name,
        request.source,
        request.source_language,
        request.target_language,
        request.pairs,
        request.list_type
    )
    return {"list_id": list_id}


@app.get("/lists")
def route_get_user_lists(current_user_id: str = Depends(get_current_user_id), client=Depends(get_db_client)):
    lists = get_user_lists(client, current_user_id)
    return {"lists": lists}


@app.get("/lists/{list_id}")
def route_get_list(
    list_id: str,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    list_data = get_list_with_pairs(client, list_id, current_user_id)
    if list_data is None:
        raise HTTPException(status_code=404, detail="List not found")
    return list_data


@app.delete("/lists/{list_id}")
def route_delete_list(
    list_id: str,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    deleted = delete_list_and_pairs(client, list_id, current_user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="List not found")
    return {"status": "deleted"}


@app.patch("/lists/{list_id}")
def route_rename_list(
    list_id: str,
    request: RenameListRequest,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    renamed = rename_list(client, list_id, current_user_id, request.name)
    if not renamed:
        raise HTTPException(status_code=404, detail="List not found")
    return {"status": "renamed"}


@app.put("/lists/{list_id}")
def route_update_list_pairs(
    list_id: str,
    request: UpdateListPairsRequest,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    updated = update_list_pairs(
        client,
        list_id,
        current_user_id,
        request.source,
        request.source_language,
        request.target_language,
        request.pairs,
        request.list_type,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="List not found")
    return {"status": "updated"}


@app.get("/lists/{list_id}/quiz-pairs")
def route_select_quiz_pairs(
    list_id: str,
    count: int,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    # Weighted toward previously-wrong pairs for this user — see
    # select_quiz_pairs_for_list()'s docstring for the weighting formula.
    # This is what makes requizzing the same list "get smarter" over time.
    pairs = select_quiz_pairs_for_list(client, list_id, current_user_id, count)
    if pairs is None:
        raise HTTPException(status_code=404, detail="List not found")
    return {"pairs": pairs}


# Minimum wrong-answer signal before bothering with a Gemini call to find a
# pattern — below this there's not enough data for a meaningful pattern,
# and it'd just be spending a call to say "not sure yet."
MIN_WRONG_ATTEMPTS_FOR_INSIGHT = 5
MIN_DISTINCT_MISSED_WORDS_FOR_INSIGHT = 3


@app.get("/lists/{list_id}/quiz-insight")
def route_get_quiz_insight(
    list_id: str,
    count: int,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    data = get_missed_pairs_for_list(client, list_id, current_user_id)
    if data is None:
        raise HTTPException(status_code=404, detail="List not found")

    if (
        len(data["missed_pairs"]) < MIN_DISTINCT_MISSED_WORDS_FOR_INSIGHT
        or data["total_wrong_attempts"] < MIN_WRONG_ATTEMPTS_FOR_INSIGHT
    ):
        return {"available": False, "message": None, "targeted_pair_ids": []}

    analysis = analyze_missed_pattern(
        data["missed_pairs"], data["all_pairs"], data["target_language"], count
    )
    return {
        "available": True,
        "message": analysis.message,
        "targeted_pair_ids": analysis.targeted_pair_ids,
    }


@app.get("/lists/{list_id}/quiz-history")
def route_get_quiz_history(
    list_id: str,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    history = get_quiz_history_for_list(client, list_id, current_user_id)
    return {"history": history}


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

    pairs, skipped_lines = parse_pasted_list(text)
    return {"pairs": pairs, "skipped_lines": skipped_lines}


@app.post("/detect-language")
def route_detect_language(request: DetectLanguageRequest):
    # Anonymous-use, like /parse-vocab-text — this is a nice-to-have that
    # pre-fills the language picker after parsing a file/paste/photo, not
    # something that needs to be tied to an account.
    if not request.pairs:
        raise HTTPException(status_code=400, detail="No pairs provided")
    result = detect_languages(request.pairs)
    return {"source_language": result.source_language, "target_language": result.target_language}


@app.post("/translate-word-list")
def route_translate_word_list(request: TranslateWordListRequest):
    # Anonymous-use, like /parse-vocab-text and /detect-language. Used when
    # a parsed file/paste turns out to be a monolingual word list (lines
    # that failed to split into a pair) — translates them into a language
    # the user picks instead of leaving them stuck as unusable skipped lines.
    if not request.words:
        raise HTTPException(status_code=400, detail="No words provided")
    result = translate_word_list(request.words, request.target_language)
    return {
        "source_language": result.source_language,
        "pairs": [
            {"source word": p.source_term, "target word": p.target_term} for p in result.pairs
        ],
    }


# ============================================================
# QUESTION GENERATION
# ============================================================

@app.post("/generate-questions")
def route_generate_question_batch(request: GenerateQuestionsRequest):
    result = generate_question_batch(
        request.pairs,
        request.source_language,
        request.target_language,
        request.batch_size,
        request.level,
        request.verb_tense,
        request.flip
    )
    return result


# ============================================================
# QUIZ SESSIONS — persisted, resumable quiz progress
# ============================================================

@app.post("/quiz-sessions")
def route_create_quiz_session(
    request: CreateQuizSessionRequest,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    session_id = create_quiz_session(
        client, current_user_id, request.list_id, request.questions, request.verb_tense
    )
    return {"session_id": session_id}


@app.patch("/quiz-sessions/{session_id}")
def route_update_quiz_session(
    session_id: str,
    request: UpdateQuizSessionRequest,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    update_quiz_session(client, session_id, current_user_id, request.current_index, request.status)
    return {"status": "updated"}


@app.get("/quiz-sessions")
def route_get_active_sessions(current_user_id: str = Depends(get_current_user_id), client=Depends(get_db_client)):
    sessions = get_active_sessions(client, current_user_id)
    return {"sessions": sessions or []}


@app.get("/quiz-sessions/completed")
def route_get_completed_sessions(
    current_user_id: str = Depends(get_current_user_id), client=Depends(get_db_client)
):
    return {"sessions": get_completed_sessions(client, current_user_id)}


@app.delete("/quiz-sessions/{session_id}")
def route_delete_quiz_session(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    delete_quiz_session(client, session_id, current_user_id)
    return {"status": "deleted"}


@app.delete("/quiz-sessions/stale/cleanup")
def route_delete_stale_sessions(current_user_id: str = Depends(get_current_user_id), client=Depends(get_db_client)):
    # Opt-in, triggered from the frontend only when the user has enabled
    # "auto-delete old quizzes" in Settings — see delete_stale_completed_sessions.
    delete_stale_completed_sessions(client, current_user_id)
    return {"status": "deleted"}


@app.post("/quiz-attempts")
def route_create_attempt(
    request: CreateAttemptRequest,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    create_quiz_attempt(
        client,
        current_user_id,
        request.session_id,
        request.vocab_pair_id,
        request.question_text,
        request.skill_category,
        request.was_correct,
        request.user_answer,
        request.correct_answer,
    )
    return {"status": "recorded"}


@app.get("/quiz-sessions/{session_id}/attempts")
def route_get_session_attempts(
    session_id: str,
    current_user_id: str = Depends(get_current_user_id),
    client=Depends(get_db_client),
):
    attempts = get_attempts_for_session(client, session_id, current_user_id)
    return {"attempts": attempts}
