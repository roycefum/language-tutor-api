#!/usr/bin/env python3
"""
Developer-only tool: generate a batch of quiz questions from a FIXED word set
and write them to a review page, so question quality can be read at a glance
instead of by taking quizzes. Not imported by the API; never deployed to any
user-facing path.

    python tools/review_questions.py --tenses all --count 100 --label baseline
    python tools/review_questions.py --tenses preterite,imperfect --count 50 --label new-prompt
    python tools/review_questions.py --build-html-only

Every run is saved as tools/reports/<run id>.json, and tools/reports/review.html
is rebuilt from ALL saved runs (a run selector on the page switches between
them), so a change to the prompt or model can be compared against an earlier
run on the very same words.

Each question also gets automatic flags from the same mechanical checks the
generator itself uses to decide what to regenerate (so a flag here means the
retry safety net missed it or ran out of attempts). Every flag is
language-independent on purpose — nothing here knows any language's time words
or grammar, so the same tool works for any language. Judging whether a tense
is really pinned down is left to the reader (and later a judge model). The
flags are a shortcut for where to look first, not a verdict.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from google.genai import types  # noqa: E402

from core import question_generator as qg  # noqa: E402
from core.tenses import TENSES_BY_LANGUAGE  # noqa: E402

REPORTS = ROOT / "tools" / "reports"
TEMPLATE = ROOT / "tools" / "review_template.html"
BATCH_SIZE = 5  # matches the app's own batch size

# Fixed on purpose — the same words every run is what makes two runs
# comparable. Chosen to include the verbs that have actually produced bad
# questions (dejar, salir, pedir, tener, jugar, vender) plus irregular,
# stem-changing and -ir verbs, where conjugation mistakes are most likely.
SPANISH_VERBS = [
    ("to leave (behind)", "dejar"), ("to leave (go out)", "salir"), ("to ask for", "pedir"),
    ("to have", "tener"), ("to play", "jugar"), ("to sell", "vender"), ("to eat", "comer"),
    ("to speak", "hablar"), ("to live", "vivir"), ("to go", "ir"), ("to be (permanent)", "ser"),
    ("to be (state)", "estar"), ("to do", "hacer"), ("to say", "decir"), ("to come", "venir"),
    ("to know", "saber"), ("to want", "querer"), ("to be able", "poder"), ("to put", "poner"),
    ("to see", "ver"), ("to give", "dar"), ("to think", "pensar"), ("to sleep", "dormir"),
    ("to open", "abrir"), ("to write", "escribir"), ("to bring", "traer"), ("to follow", "seguir"),
    ("to find", "encontrar"), ("to begin", "empezar"), ("to walk", "caminar"),
    ("to study", "estudiar"), ("to work", "trabajar"), ("to arrive", "llegar"),
    ("to return", "volver"),
]
SPANISH_VOCAB = [
    ("dog", "perro"), ("house", "casa"), ("hammer", "martillo"), ("grandmother", "abuela"),
    ("apple", "manzana"), ("book", "libro"), ("tired", "cansado"), ("tall", "alto"),
    ("kitchen", "cocina"), ("teacher", "profesor"), ("river", "río"), ("window", "ventana"),
    ("bread", "pan"), ("brother", "hermano"), ("cold", "frío"), ("beach", "playa"),
    ("umbrella", "paraguas"), ("doctor", "médico"), ("street", "calle"), ("lunch", "almuerzo"),
    ("happy", "feliz"), ("key", "llave"), ("mountain", "montaña"), ("shoes", "zapatos"),
    ("neighbor", "vecino"), ("garden", "jardín"), ("train", "tren"), ("gift", "regalo"),
    ("rain", "lluvia"), ("mirror", "espejo"),
]
WORD_SETS = {("Spanish", "verb"): SPANISH_VERBS, ("Spanish", "vocab"): SPANISH_VOCAB}

# A harder vocab set, closer to what learners actually upload than the plain
# nouns above: words whose neighbours in the same list could fill the same
# blank, words with several meanings, verb-dependent prepositions, phrases,
# connector words (as a control — these should be easy), and lines with
# formatting noise. Entries are (source, target, category); the "messy" ones
# are raw text lines that go through the app's real parser first
# (core.helpers.parse_pasted_list), so what the generator sees is what it
# would see for a pasted list.
SPANISH_VOCAB_HARD = [
    ("tired", "cansado", "near-synonyms"), ("exhausted", "agotado", "near-synonyms"),
    ("house", "casa", "near-synonyms"), ("home", "hogar", "near-synonyms"),
    ("small", "pequeño", "near-synonyms"), ("little", "chico", "near-synonyms"),
    ("fast", "rápido", "near-synonyms"), ("quick", "veloz", "near-synonyms"),
    ("bank", "banco", "several meanings"), ("letter", "carta", "several meanings"),
    ("match", "partido", "several meanings"), ("orange", "naranja", "several meanings"),
    ("spring", "primavera", "several meanings"),
    ("during", "durante", "preposition"), ("without", "sin", "preposition"),
    ("until", "hasta", "preposition"), ("among", "entre", "preposition"),
    ("to depend on", "depender de", "preposition"), ("to dream about", "soñar con", "preposition"),
    ("by the way", "por cierto", "phrase"), ("to be fed up", "estar harto", "phrase"),
    ("as soon as possible", "lo antes posible", "phrase"), ("on the other hand", "por otro lado", "phrase"),
    ("although", "aunque", "connector (control)"), ("whereas", "mientras que", "connector (control)"),
    ("nevertheless", "sin embargo", "connector (control)"), ("despite", "a pesar de", "connector (control)"),
    ("raw", "bat (animal) - murciélago", "messy line"),
    ("raw", "doctor (male): el médico", "messy line"),
    ("raw", "job / work -> trabajo", "messy line"),
]
HARD_SETS = {("Spanish", "vocab"): SPANISH_VOCAB_HARD}

def _git(*args):
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        return ""


def _flags_for(question, pair, mode, requested_tenses, language, seen_questions):
    flags = []
    text = question.question_text or ""
    if "__" not in text:
        flags.append("no_blank")
    if qg._answer_duplicated_in_sentence(question):
        flags.append("answer_in_sentence")
    if text.strip().lower() in seen_questions:
        flags.append("duplicate_question")
    seen_questions.add(text.strip().lower())
    if mode == "verb":
        if qg._verb_answer_is_bare_infinitive(question, pair):
            flags.append("answer_is_infinitive")
        if qg._verb_parenthetical_missing(question):
            flags.append("no_parenthetical")
        if not question.tense:
            flags.append("tense_not_reported")
        elif qg._verb_tense_mismatch(question, requested_tenses):
            flags.append("tense_not_requested")
    return flags


def build_html():
    runs = []
    for path in sorted(REPORTS.glob("*.json")):
        runs.append(json.loads(path.read_text(encoding="utf-8")))
    runs.sort(key=lambda r: r["created"])
    payload = json.dumps(runs, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("__RUNS_JSON__", payload)
    out = REPORTS / "review.html"
    out.write_text(html, encoding="utf-8")
    return out, len(runs)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["verb", "vocab"], default="verb")
    parser.add_argument("--language", default="Spanish", help="target language (only Spanish has a word set so far)")
    parser.add_argument("--tenses", default="present",
                        help='comma-separated tense values (see core/tenses.py), or "all"')
    parser.add_argument("--level", default="B1", help="CEFR level A1-C2")
    parser.add_argument("--count", type=int, default=None,
                        help="questions to write (default: 100, or the whole set for --wordset hard)")
    parser.add_argument("--wordset", choices=["standard", "hard"], default="standard",
                        help="which fixed word set to draw from (hard exists for Spanish vocab only)")
    parser.add_argument("--label", default="run", help="short note on what this run tests, e.g. baseline / short-prompt")
    parser.add_argument("--model", default=None, help="force a specific Gemini model for every call")
    parser.add_argument("--thinking", default=None, choices=["minimal", "low", "medium", "high"],
                        help="force a thinking level for every call (models that support it)")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--build-html-only", action="store_true")
    args = parser.parse_args()

    REPORTS.mkdir(parents=True, exist_ok=True)
    if args.build_html_only:
        out, n = build_html()
        print(f"Rebuilt {out} from {n} run(s).")
        return

    sets = HARD_SETS if args.wordset == "hard" else WORD_SETS
    words = sets.get((args.language, args.mode))
    if words is None:
        sys.exit(f"No {args.wordset} word set for {args.language} / {args.mode} yet.")
    categories = {}
    if args.wordset == "hard":
        # Raw lines go through the real parser, so a messy line is tested as
        # the app would actually receive it (including if it gets skipped).
        from core.helpers import parse_pasted_list
        resolved = []
        for source, target, category in words:
            if source == "raw":
                parsed, skipped = parse_pasted_list(target)
                for line in skipped:
                    print(f"  parser skipped: {line!r}")
                for pair in parsed:
                    resolved.append((pair["source word"], pair["target word"]))
                    categories[pair["target word"]] = category
            else:
                resolved.append((source, target))
                categories[target] = category
        words = resolved
    if args.count is None:
        args.count = len(words) if args.wordset == "hard" else 100

    requested = []
    if args.mode == "verb":
        valid = [t["value"] for t in TENSES_BY_LANGUAGE.get(args.language, [])]
        requested = valid if args.tenses == "all" else [t.strip() for t in args.tenses.split(",") if t.strip()]
        unknown = [t for t in requested if t not in valid]
        if unknown or not requested:
            sys.exit(f"Unknown/empty tenses {unknown or requested}. Valid for {args.language}: {valid}")

    # Every call goes through this wrapper: it applies --model / --thinking
    # when given, and always adds up the token counts, so a run reports what
    # it actually used (thinking tokens are billed as output).
    real_generate = qg.client.models.generate_content
    tokens = {"input": 0, "output": 0, "thinking": 0, "calls": 0}
    token_lock = threading.Lock()

    def wrapped_generate(**kwargs):
        if args.model:
            kwargs["model"] = args.model
        if args.thinking and kwargs.get("config") is not None:
            kwargs["config"].thinking_config = types.ThinkingConfig(thinking_level=args.thinking.upper())
        response = real_generate(**kwargs)
        usage = getattr(response, "usage_metadata", None)
        if usage:
            with token_lock:
                tokens["calls"] += 1
                tokens["input"] += usage.prompt_token_count or 0
                tokens["output"] += usage.candidates_token_count or 0
                tokens["thinking"] += usage.thoughts_token_count or 0
        return response

    qg.client.models.generate_content = wrapped_generate

    # The generator regenerates a flawed question by calling itself again
    # (passing _retries_left); counting those shows how often its own safety
    # net fired, which the flags on the final questions can't show.
    retry_calls = 0
    lock = threading.Lock()
    original = qg.generate_question_batch

    def counting(*a, **kw):
        nonlocal retry_calls
        if "_retries_left" in kw:
            with lock:
                retry_calls += 1
        return original(*a, **kw)

    qg.generate_question_batch = counting

    pairs = [
        {"source word": english, "target word": target}
        for english, target in (words[i % len(words)] for i in range(args.count))
    ]
    chunks = [pairs[i:i + BATCH_SIZE] for i in range(0, len(pairs), BATCH_SIZE)]

    def work(index):
        chunk = chunks[index]
        batch = qg.generate_question_batch(
            chunk, "English", args.language, len(chunk), args.level, requested, False, None, args.mode
        )
        print(f"  batch {index + 1}/{len(chunks)} done", flush=True)
        return list(batch)

    print(f"Generating {len(pairs)} {args.mode} questions in {len(chunks)} batches "
          f"(tenses: {requested or 'n/a'}, level {args.level}, model {args.model or 'default'})…")
    results, errors = {}, []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(work, i): i for i in range(len(chunks))}
        for future, index in futures.items():
            try:
                results[index] = future.result()
            except Exception as exc:  # keep going; report at the end
                errors.append(f"batch {index + 1}: {exc}")

    rows, seen, n = [], set(), 0
    for index in sorted(results):
        for question, pair in zip(results[index], chunks[index]):
            n += 1
            rows.append({
                "id": f"r{n}",
                "n": n,
                "word": pair["target word"],
                "gloss": pair["source word"],
                "category": categories.get(pair["target word"]),
                "question": question.question_text,
                "answer": question.correct_answer,
                "reported_tense": question.tense,
                "flags": _flags_for(question, pair, args.mode, requested, args.language, seen),
            })

    now = datetime.datetime.now()
    slug = re.sub(r"[^a-z0-9]+", "-", args.label.lower()).strip("-") or "run"
    run_id = f"{now:%Y%m%d-%H%M%S}_{slug}"
    run = {
        "id": run_id,
        "label": args.label,
        "created": now.isoformat(timespec="seconds"),
        "mode": args.mode,
        "language": args.language,
        "level": args.level,
        "wordset": args.wordset,
        "requested_tenses": requested,
        "model": (args.model or "default (as configured in code)")
        + (f", thinking {args.thinking}" if args.thinking else ""),
        "tokens": tokens,
        "git_commit": _git("rev-parse", "--short", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain", "--", "core")),
        "code_hash": hashlib.sha1((ROOT / "core" / "question_generator.py").read_bytes()).hexdigest()[:8],
        "retry_calls": retry_calls,
        "errors": errors,
        "rows": rows,
    }
    (REPORTS / f"{run_id}.json").write_text(json.dumps(run, ensure_ascii=False, indent=1), encoding="utf-8")
    out, count = build_html()

    flagged = sum(1 for r in rows if r["flags"])
    print(f"\nSaved run {run_id}: {len(rows)} questions, {flagged} auto-flagged, "
          f"{retry_calls} regenerations by the generator's own checks, {len(errors)} failed batch(es).")
    for message in errors:
        print("  ERROR", message)
    print(f"Tokens: {tokens['input']} in, {tokens['output']} out, {tokens['thinking']} thinking, "
          f"over {tokens['calls']} calls")
    print(f"Review page: {out} ({count} run(s) inside)")


if __name__ == "__main__":
    main()
