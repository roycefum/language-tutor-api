import os
import random
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timezone

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)


# ============================================================
# VOCAB LISTS — read
# ============================================================

def find_list_by_name(user_id, name):
    """
    Look up a single vocab list belonging to this user, by exact name match.
    Used by save_list() to decide whether to create a new list or update
    an existing one with the same name.
    Returns the matching row (dict) if found, or None if no match.
    """
    result = supabase.table("vocab_lists").select("*").eq("user_id", user_id).eq("name", name).execute()
    if len(result.data) > 0:
        return result.data[0]
    else:
        return None


# ============================================================
# VOCAB LISTS — create / update / delete
# ============================================================

def create_list(user_id, name, source, source_language, target_language):
    """
    Insert a brand-new vocab_lists row. Does NOT insert the actual vocab
    pairs — that's a separate step (see insert_vocab_pairs). id, created_at,
    and last_modified are all auto-populated by the database, so they're
    not passed in here.
    Returns the newly created row (dict), including its generated id.
    """
    response = supabase.table("vocab_lists").insert({
        "user_id": user_id,
        "name": name,
        "source": source,
        "source_language": source_language,
        "target_language": target_language
    }).execute()

    return response.data[0]


def update_list(list_id, name, source, source_language, target_language):
    """
    Update an existing vocab_lists row's metadata (name, source, languages).
    last_modified updates automatically via the moddatetime trigger — no
    need to set it here.
    """
    supabase.table("vocab_lists").update({
        "name": name,
        "source": source,
        "source_language": source_language,
        "target_language": target_language
    }).eq("id", list_id).execute()


def delete_list(list_id, user_id):
    """
    Delete a vocab_lists row entirely, scoped to user_id so one user can't
    delete another user's list by guessing its id. Note: this does NOT
    automatically delete the list's vocab_pairs — call
    delete_vocab_pairs_for_list() separately (see delete_list_and_pairs()
    for the full orchestration), or rely on a cascade-delete foreign key
    constraint if one is set up on vocab_pairs.list_id.
    """
    supabase.table("vocab_lists").delete().eq("id", list_id).eq("user_id", user_id).execute()


def get_user_lists(user_id):
    """
    Fetch every vocab list belonging to a user (metadata only, no pairs) —
    powers a "my lists" screen. Returns a list of rows, possibly empty.
    """
    result = supabase.table("vocab_lists").select("*").eq("user_id", user_id).execute()
    return result.data


def get_list_with_pairs(list_id, user_id):
    """
    Fetch a single vocab list's metadata plus its vocab pairs, scoped to
    user_id — e.g. to hand a saved list off to question generation.
    vocab_pairs has no user_id column of its own, so ownership can only be
    checked via the parent list; this looks the list up by id AND user_id
    first, and only fetches its pairs if that succeeds.
    Returns None if no such list exists for this user.
    """
    list_result = supabase.table("vocab_lists").select("*").eq("id", list_id).eq("user_id", user_id).execute()
    if len(list_result.data) == 0:
        return None
    list_row = list_result.data[0]

    pairs_result = supabase.table("vocab_pairs").select("*").eq("list_id", list_id).execute()
    list_row["pairs"] = pairs_result.data
    return list_row


def delete_list_and_pairs(list_id, user_id):
    """
    The single entry point for fully deleting a vocab list: verifies the
    list belongs to user_id first (same ownership constraint as
    get_list_with_pairs — vocab_pairs can only be scoped via its parent
    list), then removes its vocab_pairs, then the vocab_lists row itself.
    Returns True if deleted, False if no matching list was found for this user.
    """
    result = supabase.table("vocab_lists").select("id").eq("id", list_id).eq("user_id", user_id).execute()
    if len(result.data) == 0:
        return False

    delete_vocab_pairs_for_list(list_id)
    delete_list(list_id, user_id)
    return True


# ============================================================
# VOCAB PAIRS
# ============================================================

def insert_vocab_pairs(list_id, pairs):
    """
    Bulk-insert a list of vocab pairs for a given list, in a single call.
    Converts from the app's internal shape ({"source word": ..., "target word": ...})
    to the database's column names (source_term, target_term).
    """
    pairs_to_insert = [
        {"list_id": list_id, "source_term": p["source word"], "target_term": p["target word"]}
        for p in pairs
    ]
    supabase.table("vocab_pairs").insert(pairs_to_insert).execute()


def delete_vocab_pairs_for_list(list_id):
    """
    Remove all vocab_pairs belonging to a given list. Used by save_list()
    before re-inserting the current full set, when updating an existing list
    (simpler than diffing individual added/removed pairs).
    """
    supabase.table("vocab_pairs").delete().eq("list_id", list_id).execute()


# ============================================================
# ORCHESTRATION — create-or-update a full list in one call
# ============================================================

def save_list(user_id, name, source, source_language, target_language, pairs):
    """
    The single entry point for saving a vocab list. Checks whether a list
    with this name already exists for this user:
      - if yes: updates its metadata, wipes its old pairs, inserts the new set
      - if no: creates a brand-new list, then inserts its pairs
    This is what UI code should call directly, rather than the individual
    create/update/insert functions above.
    """
    existing = find_list_by_name(user_id, name)

    if existing is not None:
        list_id = existing["id"]
        update_list(list_id, name, source, source_language, target_language)
        delete_vocab_pairs_for_list(list_id)
    else:
        result = create_list(user_id, name, source, source_language, target_language)
        list_id = result["id"]

    insert_vocab_pairs(list_id, pairs)

    return list_id


# ============================================================
# QUIZ SESSIONS — persisted, resumable quiz progress
# ============================================================

def create_quiz_session(user_id, list_id, questions):
    """
    Start a new quiz session: stores the full set of AI-generated questions
    (converted from Pydantic Question objects to plain dicts via
    .model_dump(), since they're stored as JSON) along with which list
    they belong to. current_index, status, created_at, and last_active_at
    all use their column defaults (0, "in_progress", now(), now()).
    Returns the new session's id, needed for all subsequent progress updates.
    """
    response = supabase.table("quiz_sessions").insert({
        "user_id": user_id,
        "list_id": list_id,
        "questions": [q.model_dump() for q in questions]
    }).execute()
    return response.data[0]["id"]


def update_quiz_session(session_id, user_id, current_index):
    """
    Update an in-progress session's position after each answered question.
    Scoped to user_id as well as session_id so one user can't update another
    user's session by guessing/knowing its id. last_active_at updates
    automatically via a moddatetime trigger on this table, so it doesn't
    need to be set explicitly here.
    """
    supabase.table("quiz_sessions").update({
        "current_index": current_index
    }).eq("id", session_id).eq("user_id", user_id).execute()


def get_active_sessions(user_id):
    """
    Fetch every in-progress quiz session for a user — supports multiple
    concurrent quizzes (e.g., a Spanish list at 8/20 and a French list at
    3/15, both resumable independently). Used to power the "jump back in"
    UI on the home screen.
    Returns a list of matching session rows, or None if there are none.
    """
    result = supabase.table("quiz_sessions").select("*").eq("user_id", user_id).eq("status", "in_progress").execute()
    if len(result.data) > 0:
        return result.data
    else:
        return None


# ============================================================
# QUIZ ATTEMPTS — per-word right/wrong history, powers adaptive requizzing
# ============================================================

def create_quiz_attempt(user_id, session_id, vocab_pair_id, question_text, skill_category, was_correct):
    """
    Records one answered (or skipped) question. vocab_pair_id may be None
    (e.g. a question generated from a pair with no id) — still recorded,
    just won't factor into select_quiz_pairs_for_list()'s weighting since
    that groups by vocab_pair_id.
    """
    supabase.table("quiz_attempts").insert({
        "user_id": user_id,
        "session_id": session_id,
        "vocab_pair_id": vocab_pair_id,
        "question_text": question_text,
        "skill_category": skill_category,
        "was_correct": was_correct,
    }).execute()


def select_quiz_pairs_for_list(list_id, user_id, count):
    """
    Picks `count` pairs from a list for a new quiz, weighted toward pairs
    this user has gotten wrong before — so requizzing the same list leans
    more and more toward weak words over time. Unattempted pairs still get
    a baseline weight so they're never excluded entirely.

    weight = 1 + (wrong_count * 3) — a simple first-pass formula: a pair
    missed 3 times is ~10x more likely to be picked than one always gotten
    right. Not claiming this is optimal, just a reasonable starting point.

    Returns at most `count` pairs (all of them if count >= the list's
    size, skipping weighting/sampling entirely since there's nothing to
    choose between). Returns None if the list doesn't exist for this user
    (same ownership pattern as get_list_with_pairs — vocab_pairs has no
    user_id column of its own, so ownership can only be checked via the
    parent list).
    """
    list_result = supabase.table("vocab_lists").select("id").eq("id", list_id).eq("user_id", user_id).execute()
    if len(list_result.data) == 0:
        return None

    pairs_result = supabase.table("vocab_pairs").select("*").eq("list_id", list_id).execute()
    pairs = pairs_result.data
    if not pairs:
        return []

    if count >= len(pairs):
        return pairs

    pair_ids = [p["id"] for p in pairs]
    attempts_result = (
        supabase.table("quiz_attempts")
        .select("vocab_pair_id, was_correct")
        .eq("user_id", user_id)
        .in_("vocab_pair_id", pair_ids)
        .execute()
    )
    wrong_counts = {}
    for attempt in attempts_result.data:
        if not attempt["was_correct"]:
            wrong_counts[attempt["vocab_pair_id"]] = wrong_counts.get(attempt["vocab_pair_id"], 0) + 1

    weights = [1 + wrong_counts.get(p["id"], 0) * 3 for p in pairs]
    return _weighted_sample_without_replacement(pairs, weights, count)


def _weighted_sample_without_replacement(items, weights, count):
    """
    Picks `count` items without replacement, proportional to weight.
    random.choices() samples WITH replacement, which isn't right here (the
    same pair could get picked twice for one quiz) — this does the
    standard trick of drawing one at a time and removing what's picked.
    """
    items = list(items)
    weights = list(weights)
    selected = []
    for _ in range(count):
        chosen = random.choices(items, weights=weights, k=1)[0]
        index = items.index(chosen)
        selected.append(items.pop(index))
        weights.pop(index)
    return selected


# ============================================================
# ACCOUNT DELETION
# ============================================================

def delete_all_user_data(user_id):
    """
    Deletes every vocab_lists/vocab_pairs/quiz_sessions/quiz_attempts row
    belonging to a user. Used when deleting an account — this must run
    BEFORE the auth user itself is deleted (see
    auth.supabase_auth.delete_own_account), since once the auth user is
    gone there's no user_id left to scope a cleanup query to.
    """
    lists = supabase.table("vocab_lists").select("id").eq("user_id", user_id).execute()
    for row in lists.data:
        delete_vocab_pairs_for_list(row["id"])
    supabase.table("vocab_lists").delete().eq("user_id", user_id).execute()
    supabase.table("quiz_sessions").delete().eq("user_id", user_id).execute()
    supabase.table("quiz_attempts").delete().eq("user_id", user_id).execute()