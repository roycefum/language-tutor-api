import os
import random
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

from core.sample_list_generator import generate_sample_pairs
from core.sample_lists import SAMPLE_CATEGORY_META
from data.models import VocabListMeta

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")


def get_authed_client(access_token) -> Client:
    """
    Builds a fresh Supabase client authenticated as the calling user (via
    postgrest.auth(), same pattern already used in auth/supabase_auth.py's
    sign_out()/delete_own_account()). Every function below takes a client
    built this way rather than reaching for a shared module-level client,
    so its queries carry the caller's own JWT — required for Postgres Row
    Level Security policies (which key off auth.uid()) to recognize who's
    asking. A shared anon-key client would make auth.uid() resolve to null
    for every query, and RLS would deny everything.

    Each FastAPI request builds its own client via this function (see
    api/deps.py's get_db_client dependency) rather than reusing one across
    requests, since a client's auth state isn't meant to be shared/mutated
    concurrently by different users' requests.
    """
    client = create_client(url, key)
    client.postgrest.auth(access_token)
    return client


# ============================================================
# VOCAB LISTS — read
# ============================================================

def find_list(client, user_id, meta: VocabListMeta):
    """
    Look up a single vocab list belonging to this user, by name AND
    language pair together — not name alone. Used by save_list() to decide
    whether to create a new list or update an existing one.

    Matching on name alone used to mean two lists that should be allowed to
    share a name (e.g. a "Common Verbs" sample list for Spanish and another
    for French) had to be given artificially different names instead
    ("Common Verbs (English → Spanish)" vs "... (English → French)") to
    avoid colliding — the language pair columns already exist and already
    say what a suffix like that was manually re-stating in the name
    itself. Matching on all three means the name can just be "Common
    Verbs" for both.

    Returns the matching row (dict) if found, or None if no match.
    """
    result = (
        client.table("vocab_lists")
        .select("*")
        .eq("user_id", user_id)
        .eq("name", meta.name)
        .eq("source_language", meta.source_language)
        .eq("target_language", meta.target_language)
        .execute()
    )
    if len(result.data) > 0:
        return result.data[0]
    else:
        return None


# ============================================================
# VOCAB LISTS — create / update / delete
# ============================================================

def create_list(client, user_id, meta: VocabListMeta):
    """
    Insert a brand-new vocab_lists row. Does NOT insert the actual vocab
    pairs — that's a separate step (see insert_vocab_pairs). id, created_at,
    and last_modified are all auto-populated by the database, so they're
    not passed in here.
    Returns the newly created row (dict), including its generated id.
    """
    response = client.table("vocab_lists").insert({
        "user_id": user_id,
        **meta.model_dump(),
    }).execute()

    return response.data[0]


def update_list(client, list_id, meta: VocabListMeta):
    """
    Update an existing vocab_lists row's metadata (name, source, languages,
    list_type). last_modified updates automatically via the moddatetime
    trigger — no need to set it here.
    """
    client.table("vocab_lists").update(meta.model_dump()).eq("id", list_id).execute()


def rename_list(client, list_id, user_id, name):
    """
    Renames a list in place, independent of its pairs — the counterpart to
    update_list_pairs() below. Scoped to user_id so one user can't rename
    another's list by guessing its id. Returns False if no matching list
    exists for this user (caller should 404), True otherwise.
    """
    result = client.table("vocab_lists").select("id").eq("id", list_id).eq("user_id", user_id).execute()
    if len(result.data) == 0:
        return False
    client.table("vocab_lists").update({"name": name}).eq("id", list_id).execute()
    return True


def update_list_pairs(client, list_id, user_id, source, source_language, target_language, pairs, list_type="vocab"):
    """
    Updates an existing list's metadata (excluding name — see rename_list())
    and replaces its pairs, addressed directly by id rather than by
    matching on name like save_list() does. This is what lets editing an
    already-saved list's words never risk creating a duplicate list under
    a different name. Scoped to user_id; returns False if no matching list
    exists for this user (caller should 404), True otherwise.
    """
    result = client.table("vocab_lists").select("id").eq("id", list_id).eq("user_id", user_id).execute()
    if len(result.data) == 0:
        return False

    client.table("vocab_lists").update({
        "source": source,
        "source_language": source_language,
        "target_language": target_language,
        "list_type": list_type,
    }).eq("id", list_id).execute()

    delete_vocab_pairs_for_list(client, list_id)
    insert_vocab_pairs(client, list_id, pairs)
    return True


def delete_list(client, list_id, user_id):
    """
    Delete a vocab_lists row entirely, scoped to user_id so one user can't
    delete another user's list by guessing its id. Note: this does NOT
    automatically delete the list's vocab_pairs — call
    delete_vocab_pairs_for_list() separately (see delete_list_and_pairs()
    for the full orchestration), or rely on a cascade-delete foreign key
    constraint if one is set up on vocab_pairs.list_id.
    """
    client.table("vocab_lists").delete().eq("id", list_id).eq("user_id", user_id).execute()


def get_user_lists(client, user_id):
    """
    Fetch every vocab list belonging to a user (metadata only, no pairs) —
    powers a "my lists" screen. Returns a list of rows, possibly empty.
    """
    result = client.table("vocab_lists").select("*").eq("user_id", user_id).execute()
    return result.data


def get_list_with_pairs(client, list_id, user_id):
    """
    Fetch a single vocab list's metadata plus its vocab pairs, scoped to
    user_id — e.g. to hand a saved list off to question generation.
    vocab_pairs has no user_id column of its own, so ownership can only be
    checked via the parent list; this looks the list up by id AND user_id
    first, and only fetches its pairs if that succeeds.
    Returns None if no such list exists for this user.
    """
    list_result = client.table("vocab_lists").select("*").eq("id", list_id).eq("user_id", user_id).execute()
    if len(list_result.data) == 0:
        return None
    list_row = list_result.data[0]

    pairs_result = client.table("vocab_pairs").select("*").eq("list_id", list_id).execute()
    list_row["pairs"] = pairs_result.data
    return list_row


def delete_list_and_pairs(client, list_id, user_id):
    """
    The single entry point for fully deleting a vocab list: verifies the
    list belongs to user_id first (same ownership constraint as
    get_list_with_pairs — vocab_pairs can only be scoped via its parent
    list), then removes its vocab_pairs, then the vocab_lists row itself.
    Returns True if deleted, False if no matching list was found for this user.
    """
    result = client.table("vocab_lists").select("id").eq("id", list_id).eq("user_id", user_id).execute()
    if len(result.data) == 0:
        return False

    delete_vocab_pairs_for_list(client, list_id)
    delete_list(client, list_id, user_id)
    return True


# ============================================================
# VOCAB PAIRS
# ============================================================

def insert_vocab_pairs(client, list_id, pairs):
    """
    Bulk-insert a list of vocab pairs for a given list, in a single call.
    Converts from the app's internal shape ({"source word": ..., "target word": ...})
    to the database's column names (source_term, target_term).
    """
    pairs_to_insert = [
        {"list_id": list_id, "source_term": p["source word"], "target_term": p["target word"]}
        for p in pairs
    ]
    client.table("vocab_pairs").insert(pairs_to_insert).execute()


def delete_vocab_pairs_for_list(client, list_id):
    """
    Remove all vocab_pairs belonging to a given list. Used by save_list()
    before re-inserting the current full set, when updating an existing list
    (simpler than diffing individual added/removed pairs).
    """
    client.table("vocab_pairs").delete().eq("list_id", list_id).execute()


# ============================================================
# ORCHESTRATION — create-or-update a full list in one call
# ============================================================

def save_list(client, user_id, meta: VocabListMeta, pairs):
    """
    The single entry point for saving a vocab list. Checks whether a list
    with this name AND language pair already exists for this user:
      - if yes: updates its metadata, wipes its old pairs, inserts the new set
      - if no: creates a brand-new list, then inserts its pairs
    This is what UI code should call directly, rather than the individual
    create/update/insert functions above.
    """
    existing = find_list(client, user_id, meta)

    if existing is not None:
        list_id = existing["id"]
        update_list(client, list_id, meta)
        delete_vocab_pairs_for_list(client, list_id)
    else:
        result = create_list(client, user_id, meta)
        list_id = result["id"]

    insert_vocab_pairs(client, list_id, pairs)

    return list_id


# ============================================================
# USER PROFILE — account-level preferences (currently just the learning
# language pair, but user_profiles is a general-purpose table so future
# account-level data has a home without needing a new one-off table).
# ============================================================

def get_user_profile(client, user_id):
    """
    Fetch a user's profile row, or None if they've never set one — that
    None (or a row with null learning_target_language) is the signal used
    to force a first-login redirect to Settings and to decide whether
    saving the learning pair should also trigger sample-list generation.
    """
    result = client.table("user_profiles").select("*").eq("user_id", user_id).execute()
    return result.data[0] if len(result.data) > 0 else None


def upsert_user_profile(client, user_id, source_language, target_language):
    """
    Creates or updates a user's profile row with their learning language
    pair. Manual select-then-insert-or-update, matching this codebase's
    existing pattern (save_list/update_list) rather than relying on
    postgrest upsert support.
    """
    existing = get_user_profile(client, user_id)
    fields = {
        "learning_source_language": source_language,
        "learning_target_language": target_language,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if existing is not None:
        client.table("user_profiles").update(fields).eq("user_id", user_id).execute()
    else:
        client.table("user_profiles").insert({"user_id": user_id, **fields}).execute()


def generate_and_save_sample_list(client, user_id, category_key, source_language, target_language):
    """
    Generates (via Gemini — see generate_sample_pairs) and saves ONE
    sample-list category for a language pair. Shared by the first-time
    bulk generation (all 4 categories, triggered from Settings) and the
    on-demand single-category catalog in My Lists.

    The plain category label (e.g. "Common Verbs") is the name — no
    language-pair suffix needed, since save_list()/find_list() already
    disambiguate by name AND language pair together, so the same label can
    be reused across every language pair without colliding. Returns the
    new list's id.
    """
    label, list_type = SAMPLE_CATEGORY_META[category_key]
    pairs = generate_sample_pairs(category_key, source_language, target_language)
    meta = VocabListMeta(
        name=label,
        source="sample",
        source_language=source_language,
        target_language=target_language,
        list_type=list_type,
    )
    return save_list(client, user_id, meta, pairs)


def generate_and_save_sample_lists(client, user_id, source_language, target_language):
    """
    Generates and saves all 4 sample-list categories for a language pair —
    called once, the first time a user sets their learning pair in
    Settings. Best-effort per category: if one category's generation
    fails, the others still get saved rather than the whole batch failing
    over one Gemini hiccup.
    """
    for category_key in SAMPLE_CATEGORY_META:
        try:
            generate_and_save_sample_list(client, user_id, category_key, source_language, target_language)
        except Exception:
            continue


# ============================================================
# QUIZ SESSIONS — persisted, resumable quiz progress
# ============================================================

def create_quiz_session(client, user_id, list_id, questions, verb_tense=None):
    """
    Start a new quiz session: stores the full set of AI-generated questions
    (converted from Pydantic Question objects to plain dicts via
    .model_dump(), since they're stored as JSON) along with which list
    they belong to. current_index, status, created_at, and last_active_at
    all use their column defaults (0, "in_progress", now(), now()).
    verb_tense records which tense (if any) was selected on Generate Quiz —
    None for vocab lists or a "Mixed" tense pick — purely informational, so
    My Quizzes can show what a resumable verb quiz is actually testing.
    Returns the new session's id, needed for all subsequent progress updates.
    """
    response = client.table("quiz_sessions").insert({
        "user_id": user_id,
        "list_id": list_id,
        "questions": [q.model_dump() for q in questions],
        "verb_tense": verb_tense,
    }).execute()
    return response.data[0]["id"]


def update_quiz_session(client, session_id, user_id, current_index, status=None):
    """
    Update an in-progress session's position after each answered question.
    Scoped to user_id as well as session_id so one user can't update another
    user's session by guessing/knowing its id. last_active_at updates
    automatically via a moddatetime trigger on this table, so it doesn't
    need to be set explicitly here.

    `status` is optional and only passed when the quiz screen detects the
    last question has been answered — set to "completed" at that point so
    the session stops showing under "Continue a Quiz" and starts counting
    toward that list's quiz-history/score tracking.
    """
    update = {"current_index": current_index}
    if status is not None:
        update["status"] = status
    client.table("quiz_sessions").update(update).eq("id", session_id).eq("user_id", user_id).execute()


def get_active_sessions(client, user_id):
    """
    Fetch every in-progress quiz session for a user — supports multiple
    concurrent quizzes (e.g., a Spanish list at 8/20 and a French list at
    3/15, both resumable independently). Used to power the "jump back in"
    UI on the home screen.
    Returns a list of matching session rows, or None if there are none.
    """
    result = client.table("quiz_sessions").select("*").eq("user_id", user_id).eq("status", "in_progress").execute()
    if len(result.data) > 0:
        return result.data
    else:
        return None


def get_quiz_history_for_list(client, list_id, user_id):
    """
    Fetch this user's completed quizzes for one list, each with a raw score
    (correct/total from quiz_attempts) — powers the score-over-time list and
    line graph on the list-history screen. Ordered oldest to newest, since
    the graph and trend feedback both read left-to-right as "over time".
    last_active_at is used as the completion timestamp — there's no
    separate completed_at column, and last_active_at is set (via the
    moddatetime trigger) at the same moment status flips to "completed".
    Returns a list of {session_id, completed_at, correct, total} dicts,
    possibly empty.
    """
    sessions_result = (
        client.table("quiz_sessions")
        .select("id, last_active_at")
        .eq("list_id", list_id)
        .eq("user_id", user_id)
        .eq("status", "completed")
        .order("last_active_at")
        .execute()
    )
    sessions = sessions_result.data
    if not sessions:
        return []

    session_ids = [s["id"] for s in sessions]
    attempts_result = (
        client.table("quiz_attempts")
        .select("session_id, was_correct")
        .in_("session_id", session_ids)
        .execute()
    )
    totals = {}
    corrects = {}
    for attempt in attempts_result.data:
        sid = attempt["session_id"]
        totals[sid] = totals.get(sid, 0) + 1
        if attempt["was_correct"]:
            corrects[sid] = corrects.get(sid, 0) + 1

    return [
        {
            "session_id": s["id"],
            "completed_at": s["last_active_at"],
            "correct": corrects.get(s["id"], 0),
            "total": totals.get(s["id"], 0),
        }
        for s in sessions
        if totals.get(s["id"], 0) > 0
    ]


def get_completed_sessions(client, user_id):
    """
    Fetch every completed quiz session for a user across all their lists
    (not scoped to one list, unlike get_quiz_history_for_list) — powers a
    "past quizzes" section on My Quizzes. Ordered newest first, since
    that's the natural order for a flat activity list (list-history's
    per-list graph is what wants oldest-first instead).
    Returns a list of {session_id, list_id, completed_at, correct, total}
    dicts, possibly empty.
    """
    sessions_result = (
        client.table("quiz_sessions")
        .select("id, list_id, last_active_at")
        .eq("user_id", user_id)
        .eq("status", "completed")
        .order("last_active_at", desc=True)
        .execute()
    )
    sessions = sessions_result.data
    if not sessions:
        return []

    session_ids = [s["id"] for s in sessions]
    attempts_result = (
        client.table("quiz_attempts")
        .select("session_id, was_correct")
        .in_("session_id", session_ids)
        .execute()
    )
    totals = {}
    corrects = {}
    for attempt in attempts_result.data:
        sid = attempt["session_id"]
        totals[sid] = totals.get(sid, 0) + 1
        if attempt["was_correct"]:
            corrects[sid] = corrects.get(sid, 0) + 1

    return [
        {
            "session_id": s["id"],
            "list_id": s["list_id"],
            "completed_at": s["last_active_at"],
            "correct": corrects.get(s["id"], 0),
            "total": totals.get(s["id"], 0),
        }
        for s in sessions
        if totals.get(s["id"], 0) > 0
    ]


def delete_stale_completed_sessions(client, user_id, days=30):
    """
    Deletes this user's completed quiz sessions whose last_active_at (set
    at completion time, via the moddatetime trigger) is older than `days`
    days ago. Opt-in only — called from the frontend when the user has
    enabled "auto-delete old quizzes" in Settings; otherwise completed
    sessions are kept indefinitely so score history stays intact.
    In-progress sessions are untouched regardless of age.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    client.table("quiz_sessions").delete().eq("user_id", user_id).eq(
        "status", "completed"
    ).lt("last_active_at", cutoff).execute()


def delete_quiz_session(client, session_id, user_id):
    """
    Delete a quiz_sessions row entirely, scoped to user_id so one user can't
    delete another user's session by guessing its id. Lets a user discard an
    in-progress quiz from "My Quizzes" without needing to finish or delete
    the underlying list.
    """
    client.table("quiz_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()


# ============================================================
# QUIZ ATTEMPTS — per-word right/wrong history, powers adaptive requizzing
# ============================================================

def create_quiz_attempt(
    client, user_id, session_id, vocab_pair_id, question_text, skill_category, was_correct,
    user_answer, correct_answer,
):
    """
    Records one answered (or skipped) question. vocab_pair_id may be None
    (e.g. a question generated from a pair with no id) — still recorded,
    just isn't tied to a specific word. user_answer/correct_answer are stored
    (not just was_correct) so a full per-question results view can be
    reconstructed later, including after resuming a session across app
    restarts — see get_attempts_for_session().
    """
    client.table("quiz_attempts").insert({
        "user_id": user_id,
        "session_id": session_id,
        "vocab_pair_id": vocab_pair_id,
        "question_text": question_text,
        "skill_category": skill_category,
        "was_correct": was_correct,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
    }).execute()


def get_attempts_for_session(client, session_id, user_id):
    """
    Fetches every recorded attempt for one quiz session, in the order they
    were answered — powers the full per-question results table. Scoped to
    user_id so one user can't read another's session by guessing its id.
    """
    result = (
        client.table("quiz_attempts")
        .select("question_text, user_answer, correct_answer, was_correct, created_at")
        .eq("session_id", session_id)
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )
    return result.data


def _dedupe_pairs_by_target(pairs):
    """
    Collapses pairs that share the same target word (case/whitespace
    insensitive) down to one representative. A list can end up with the
    same word saved more than once (typed or pasted in twice) — without
    this, a quiz could ask the same target word more than once even when
    plenty of other words are available to fill the requested count.
    """
    seen = set()
    deduped = []
    for pair in pairs:
        key = pair["target_term"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(pair)
    return deduped


def select_quiz_pairs_for_list(client, list_id, user_id, count):
    """
    Picks `count` pairs from a list for a new quiz — a plain random spread,
    deliberately unweighted. (An earlier version leaned toward previously
    missed words; that job now belongs only to the targeted quiz, driven by
    an analysis of the learner's last quiz — see get_last_quiz_evidence().)
    Pairs sharing a target word are collapsed first, so one word can't be
    asked twice. Returns at most `count` pairs (all of them if count >= the
    list's size). Returns None if the list doesn't exist for this user (same
    ownership pattern as get_list_with_pairs — vocab_pairs has no user_id
    column of its own, so ownership can only be checked via the parent list).
    """
    list_result = client.table("vocab_lists").select("id").eq("id", list_id).eq("user_id", user_id).execute()
    if len(list_result.data) == 0:
        return None

    pairs_result = client.table("vocab_pairs").select("*").eq("list_id", list_id).execute()
    pairs = _dedupe_pairs_by_target(pairs_result.data)

    if count >= len(pairs):
        return pairs
    return random.sample(pairs, count)


def get_last_quiz_evidence(client, list_id, user_id):
    """
    Gathers what the quiz-insight analysis needs: this list's full pairs
    (deduped, ownership-checked) plus every recorded answer from the most
    recent COMPLETED quiz on this list. Only that one quiz — the analysis
    is meant to be fresh each time, not a running all-time tally, so a
    problem that's been fixed stops being flagged. Returns None if the list
    doesn't exist for this user; "attempts" is an empty list if the list
    has no completed quiz yet.
    """
    list_result = (
        client.table("vocab_lists")
        .select("id, target_language")
        .eq("id", list_id)
        .eq("user_id", user_id)
        .execute()
    )
    if len(list_result.data) == 0:
        return None
    target_language = list_result.data[0]["target_language"]

    pairs_result = client.table("vocab_pairs").select("*").eq("list_id", list_id).execute()
    pairs = _dedupe_pairs_by_target(pairs_result.data)

    sessions = (
        client.table("quiz_sessions")
        .select("id")
        .eq("list_id", list_id)
        .eq("user_id", user_id)
        .eq("status", "completed")
        .order("last_active_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    attempts = get_attempts_for_session(client, sessions[0]["id"], user_id) if sessions else []

    return {"target_language": target_language, "all_pairs": pairs, "attempts": attempts}


# ============================================================
# ACCOUNT DELETION
# ============================================================

def delete_all_user_data(client, user_id):
    """
    Deletes every vocab_lists/vocab_pairs/quiz_sessions/quiz_attempts row
    belonging to a user. Used when deleting an account — this must run
    BEFORE the auth user itself is deleted (see
    auth.supabase_auth.delete_own_account), since once the auth user is
    gone there's no user_id left to scope a cleanup query to.
    """
    lists = client.table("vocab_lists").select("id").eq("user_id", user_id).execute()
    for row in lists.data:
        delete_vocab_pairs_for_list(client, row["id"])
    client.table("vocab_lists").delete().eq("user_id", user_id).execute()
    client.table("quiz_sessions").delete().eq("user_id", user_id).execute()
    client.table("quiz_attempts").delete().eq("user_id", user_id).execute()
