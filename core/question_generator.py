import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from data.models import Question,QuestionBatch,PatternAnalysis
from core.exceptions import GeminiAPIError
from core.cefr import get_cefr_guidance, DEFAULT_CEFR_LEVEL
from core.tenses import get_tense_labels

load_dotenv()
client = genai.Client()

# Gemini's structured JSON output occasionally corrupts an accented
# character into a literal "#XXXX" sequence instead of the real character
# (e.g. "después" -> "Despu#00e9s", "jardín" -> "jard#00edn") — looks like a
# malformed unicode escape the model emits at a low rate. "#" followed by
# exactly 4 hex digits doesn't occur in real question text otherwise, so
# repairing it back to the intended character is safe.
_MOJIBAKE_ESCAPE_RE = re.compile(r"#([0-9a-fA-F]{4})")


def _repair_mojibake_escapes(text):
    return _MOJIBAKE_ESCAPE_RE.sub(lambda m: chr(int(m.group(1), 16)), text)


def _repair_question(question):
    question.question_text = _repair_mojibake_escapes(question.question_text)
    question.correct_answer = _repair_mojibake_escapes(question.correct_answer)
    return question


# Catches the modal-verb self-collision failure mode (e.g. "j'ai dû ___ de
# l'argent. (devoir)" with correct_answer "dû") — the answer word/phrase
# shouldn't appear anywhere in the sentence outside the blank it belongs in.
# Word-boundary matching avoids false positives from short answers that are
# substrings of unrelated words (e.g. "es" inside "esos").
_TRAILING_PAREN_RE = re.compile(r"\([^)]*\)\s*$")


def _answer_duplicated_in_sentence(question):
    sentence = _TRAILING_PAREN_RE.sub("", question.question_text)
    sentence = sentence.replace("_____", " ")
    answer = question.correct_answer.strip()
    if not answer:
        return False
    return re.search(rf"\b{re.escape(answer)}\b", sentence, re.IGNORECASE) is not None


# A pair counts as a VERB pair by the same rule the prompt itself uses:
# either side starting with "to " (e.g. "to walk"). Mirrors the prompt's own
# "Verb conjugation" section — kept in sync with it by hand, not derived
# from it, so a future prompt wording change needs both updated.
def _verb_infinitive(pair):
    target = pair["target word"].strip()
    return target[3:].strip() if target.lower().startswith("to ") else target


# Two mechanical checks on top of the model actually following its own
# verb-prompt instructions (steps 3 and 4) — both feed the same per-pair
# retry below rather than being patched after the fact: the infinitive
# check can't be safely auto-corrected (conjugating a verb ourselves would
# need real grammar knowledge we don't have in code), and the parenthetical,
# even though it could be appended as text, is retried too so a batch never
# ends up with a blindly-appended infinitive next to one the model already
# wrote wrong. Only meaningful for a Verb list — the caller gates on
# list_type, since a Vocab list's pair legitimately answers with the bare
# infinitive and has no parenthetical at all; that's correct there, not a
# bug.
def _verb_answer_is_bare_infinitive(question, pair):
    infinitive = _verb_infinitive(pair).lower()
    answer = question.correct_answer.strip().lower()
    return bool(infinitive) and answer == infinitive


def _verb_parenthetical_missing(question):
    return _TRAILING_PAREN_RE.search(question.question_text) is None

def question_generator (source_term: str, target_term: str, source_language: str, target_language:str) -> Question:

    prompt = f""" {source_term} is the source term in the {source_language}. This is the language that the user already knows.
                {target_term} is the target term in the {target_language}. This is the language that the user is learning.
                Write a fill in the blanks language quiz type question using a translation of {source_term} from {source_language}.
                This question is meant to test how well the user knows the {target_term}. The sentence must include a specific descriptive detail or defining clue about {target_term} 
                so that it is the only word that could logically complete the sentence — not a generic statement 
                that many different words could equally complete.
                Here are examples of well-constrained questions:

                Situational/scenario-based (like the math exam one): "Este examen de matemáticas es muy ___, no entiendo nada." → difícil
                Cause-and-effect/reasoning-based: "Como no dormí anoche, hoy me siento muy ___." (Since I didn't sleep last night, today I feel very ___.) → cansado (tired)
                Comparison-based: "A diferencia de mi hermano, que es muy alto, yo soy bastante ___." (Unlike my brother, who is very tall, I am quite ___.) → bajo (short)

                Here are some bad exmaples:
                Too generic: "Mi ___ es muy grande." → fails because many nouns fit
                Definitional: "A standalone residential building where a family lives is a ___." → fails because it defines the word instead of using it naturally
                Leaks the answer: "My parents bought me a big furry ___. (perro)" → fails because the parenthetical directly reveals the translation

                Now write a similar question for: {target_term}
                The question should be a natural sentence phrased to test the user's knowledge of {target_language}
                Do NOT write the question as a dictionary-style definition of {target_term}. 
                The sentence should use the word naturally, in a realistic situation or context, 
                not describe or define what the word means.
                Use "_____" to mark where the blank goes. The blank is the {target_term}
                Do not use {source_term} in the question text.



            """

    


    try: 
        response = client.models.generate_content(
        model = "gemini-3.6-flash",
        contents = prompt,
        config = types.GenerateContentConfig(
            response_mime_type= "application/json",
            response_schema= Question

        )
    )

    except Exception as e:
        raise GeminiAPIError(f"question_generator failed: {e}") from e


    return _repair_question(response.parsed)


def generate_question_batch (pairs:list[dict], source_language: str, target_language:str,batch_size:int, level:str = DEFAULT_CEFR_LEVEL, verb_tenses: list[str] | None = None, flip: bool = False, focus: str | None = None, list_type: str = "vocab", _retries_left: int = 4) -> QuestionBatch:

    cefr_guidance = get_cefr_guidance(level)
    # One tense selected behaves like the old "specific tense" mode; more
    # than one behaves like the old "Mixed" mode (which used to mean ALL
    # tenses, unconditionally) — both are really the same instruction,
    # "conjugate within this set," just with a set of size 1 or more, so
    # there's no need for them to be two separate code paths.
    tense_labels = get_tense_labels(target_language, verb_tenses or [])
    if len(tense_labels) == 1:
        tense_instruction = (
            f'For every VERB pair in this batch (see the Verb conjugation guidance below), conjugate it '
            f'specifically in the {tense_labels[0]} — do not vary the tense for verb pairs in this batch, use '
            f'{tense_labels[0]} for all of them. Still vary the subject/person across questions so they are not all '
            f'identical.'
        )
    elif len(tense_labels) > 1:
        # Without an explicit menu, the model left to "vary the tense" on
        # its own defaults to whichever tenses are most common in ordinary
        # writing (present and future), so a multi-tense quiz was never
        # actually landing on the others. Naming exactly the chosen tenses,
        # the same way a single selection names its one tense, fixes that
        # the same way the earlier verb-conjugation and parenthetical
        # fixes did: give the model the concrete list instead of a vague
        # instruction.
        tense_instruction = (
            f'For every VERB pair in this batch (see the Verb conjugation guidance below), spread the questions '
            f'across these selected tenses/moods — draw from: {", ".join(tense_labels)}. Do not let more than '
            f'about a third of this batch\'s verb questions land on any single one of them.'
        )
    else:
        tense_instruction = ""

    # Only for a "Target My Mistakes" quiz: steer the questions toward the
    # skill the learner's last quiz showed them struggling with. Not used in
    # flip mode (that's a separate, comprehension-only prompt).
    focus_instruction = (
        f"""FOCUS FOR THIS QUIZ: this learner is specifically struggling with: {focus}
                Write the questions so that as many as possible require exactly that skill. For verb pairs, choose the
                subject and tense that exercise it (this takes precedence over the earlier instruction to vary the
                subject and tense — but if a specific tense was required above, stay within that tense). For spelling
                or accent problems, choose forms where it matters. Leave a few questions ordinary so the quiz is not a
                monotonous drill. Never mention this focus, or the learner's weakness, in any question text."""
        if focus
        else ""
    )

    # Pairs may carry an "id" (from a saved list, used below to stamp each
    # returned Question with its source vocab_pair_id) that has nothing to
    # do with the question content — strip it before it goes in the prompt.
    prompt_pairs = [{"source word": p["source word"], "target word": p["target word"]} for p in pairs]

    # Flip mode tests comprehension instead of production: the target word is
    # given, visible, in a natural sentence — the learner just translates it
    # back to source_language. This is a deliberately separate, much simpler
    # prompt branch (no blank, no whole-category-ambiguity concerns, no verb
    # conjugation) rather than threading a flag through the production prompt
    # below — flip is vocab-only, not meant to interact with verb handling.
    if flip:
        prompt = f""" {prompt_pairs} is a list of dictionaries and each dictionary is in the form "source term : target term". The source term (the first term) is in
                {source_language} — the language the user already knows. The target term (the second term) is in {target_language} — the language the user is learning.

                Write a batch of {batch_size} questions, one per pair, in the same order. This tests the REVERSE
                of normal vocabulary testing: whether the learner can translate a {target_language} word back into
                {source_language}, given the word itself.

                For each pair, write one natural sentence entirely in {target_language} that uses the target_term
                in context, with the target_term itself wrapped in square brackets — e.g. "El perro corre en el
                [parque]." Do NOT blank it out or hide it; the word must be visible exactly as target_term (a
                minimally-inflected natural form, e.g. pluralized, is fine if the sentence calls for it).

                {cefr_guidance}
                This complexity guidance applies to the sentence surrounding the bracketed word, not to the word
                itself.

                The correct_answer for each question must be exactly source_term, verbatim, in {source_language} —
                this is a direct vocabulary pair with a known translation, so do not invent an alternate
                translation, paraphrase, or add extra words.

                Do not include source_term anywhere in the question_text itself — the sentence must be entirely in
                {target_language}, with only the bracketed target_term as the word being tested.

                Leave the "tense" field empty/null for every question — it only applies to verb-conjugation
                questions, not this comprehension mode.
            """
    elif list_type == "verb":
        # A Verb list is, by definition, entirely verb pairs — every pair
        # gets conjugated, unconditionally, unlike a Vocab list where a
        # verb-shaped entry is tested as an ordinary word (see the vocab
        # branch below). Kept as its own prompt, not a section bolted onto
        # the vocab one, so it isn't diluted by — or diluting — the
        # category-ambiguity framework that only applies to vocab.
        prompt = f""" {prompt_pairs} is a list of dictionaries and each dictionary is in the form "source term : target term". The source term (the first term) is in
                {source_language} — the language the user already knows. The target term (the second term) is in {target_language} — the language the user is learning.
                Every pair in this list is a verb.

                Write a batch of {batch_size} fill-in-the-blank questions, one per pair, in the same order, testing
                whether the learner can conjugate each verb — not just recall its infinitive. For each pair:

                1. Find the bare infinitive to conjugate: if target_term begins with "to ", strip that "to " to get
                   it (e.g. "to walk" → "walk"); otherwise target_term is already the bare infinitive (e.g.
                   "caminar", a Spanish/French infinitive needs no stripping).
                2. Pick a natural subject (a pronoun, a name, or a noun) and a tense/mood appropriate to the
                   complexity level below, then conjugate the infinitive for that subject and tense in
                   {target_language} (e.g. "caminar" + "ella" + preterite → "caminó").
                3. Make that specific conjugated form — not the infinitive — both the blank and the correct_answer
                   for this question. Never use the bare infinitive as the answer; that tests recall, not
                   conjugation, which is the entire point of a verb quiz.
                4. After the sentence, append the bare infinitive in parentheses, e.g. "Ayer, mi hermano ___ cinco
                   millas. (caminar)". This parenthetical is required on every single question in this batch, with
                   no exceptions — since the infinitive is given directly, the sentence doesn't need any other clue
                   about which verb it is. It DOES still need something that settles the TENSE — a subject alone
                   ("Ellos ___ ayuda al profesor.") only says WHO, never WHEN, so present, preterite, and imperfect
                   could all fit equally well and the question becomes unscoreable. Every single question needs an
                   explicit time marker ("ayer"/"todos los días"/"el año que viene") or an equally unambiguous
                   clue elsewhere in the sentence (e.g. "mientras estudiaba" already implies imperfect) — never
                   just a bare subject and blank with nothing else pinning down when it happens. And the marker
                   must point to ONLY the tense you picked, not double as a natural fit for a different tense too.
                   Some time words are genuinely ambiguous this way: "mañana" ("tomorrow") is used naturally with BOTH the
                   future ("Mañana saldremos temprano") and the present, for a planned near-future action ("Mañana
                   salimos temprano") — a learner answering with either tense would be correct, which makes the
                   question unscoreable. Before finalizing, check whether a different tense could also sound
                   natural with the same sentence and marker; if so, either pick a marker that rules that out
                   (a habitual marker like "todos los días" only fits present; "ayer" only fits a past tense) or
                   add unambiguous context elsewhere in the sentence. This matters most for verbs whose conjugated
                   form is itself identical across two tenses for a given subject (e.g. -ir verbs' nosotros form is
                   spelled the same in the present and the preterite, like "salimos") — for those, the sentence's
                   own context has to be the only thing settling which tense is intended, since the word itself
                   can't. Subjunctive is a special case here: it isn't a time at all, so a time marker doesn't
                   apply to it. Its disambiguating clue is a grammatical trigger phrase that requires the
                   subjunctive — doubt, wish, necessity, or emotion ("espero que", "es importante que", "ojalá
                   que", "no creo que", "quiero que") — built into the sentence right before the subject/blank, so
                   the mood itself is forced by the sentence's structure rather than guessed from timing.
                5. Vary the subject and tense across the different verb questions in this batch rather than
                   defaulting to the same person/tense every time — this is what makes a requiz of the same verb
                   list actually test different conjugations over time. {tense_instruction}
                6. Report which tense/mood you actually used for this question in the "tense" field, as the exact
                   value string {json.dumps(verb_tenses) if verb_tenses else "matching a value from core/tenses.py's TENSES_BY_LANGUAGE"}
                   — not the display label, and not anything else. This must be set on every question in this
                   batch.

                {cefr_guidance}
                This complexity guidance applies to the sentence surrounding the blank and the choice of
                subject/tense, not to which verb is being tested — that's fixed by the pair.

                Modal/semi-auxiliary verbs (e.g. devoir, pouvoir, vouloir, savoir, and their equivalents in other
                languages) are typically followed by an infinitive complement to form a natural sentence (e.g. "j'ai
                dû finir mes dossiers" — "finir" is the complement, not the tested word). When target_term is such a
                verb: the blank and correct_answer must be ONLY the conjugated form of target_term itself. Any
                infinitive complement the sentence needs must be a DIFFERENT verb, written out normally, NOT left as
                a second blank and NOT filled with another form of target_term. Never let any form of target_term
                (conjugated, participle, or infinitive) appear anywhere in the sentence outside the one blank it
                belongs in — a sentence like "j'ai dû ___ de l'argent (devoir)" where the blank is also meant to be
                "dû" is wrong twice over: it repeats the already-visible "j'ai dû" and leaves no real infinitive
                complement.

                CRITICAL: every single question's sentence AND its answer must be entirely in {target_language}.
                Do not write any question in {source_language}. Double-check each question before finalizing.

                {focus_instruction}

                Now write a similar question for target term, following the conjugation steps above exactly. Use
                "_____" to mark where the blank goes — the blank and correct_answer are the specific conjugated form,
                never the bare infinitive. Do not use source_term in the question text.
            """
    else:
        prompt = f""" {prompt_pairs} is a list of dictionaries and each dictionary is in the form "source term : target term" The source term (the first term) is in the
                {source_language}. This is the language that the user already knows. The target term (the second term) is in the {target_language}. This is the
                language that the user is learning.
                Write a batch of {batch_size} questions. One question per pair, in the same order Each question should be formed with the following guidelines:
                Write a fill in the blanks language quiz type question using a translation of source_term from {source_language}.
                This question is meant to test how well the user knows the target_term. The sentence must include a specific descriptive detail or defining clue about each pair's target term
                so that it is the only word that could logically complete the sentence — not a generic statement
                that many different words could equally complete.

                {cefr_guidance}
                This complexity guidance applies to the sentence surrounding the blank, not to the target_term itself — the target_term is fixed by the pair and must not be simplified or substituted.

                "CRITICAL: every single question's sentence AND its answer must be entirely in {target_language}.
                Do not write any question in {source_language}. Double-check each question before finalizing —
                the sentence language and the answer language must always match {target_language}."
                Here are examples of well-constrained questions:

                Situational/scenario-based (like the math exam one): "Este examen de matemáticas es muy ___, no entiendo nada." → difícil
                Cause-and-effect/reasoning-based: "Como no dormí anoche, hoy me siento muy ___." (Since I didn't sleep last night, today I feel very ___.) → cansado (tired)
                Comparison-based: "A diferencia de mi hermano, que es muy alto, yo soy bastante ___." (Unlike my brother, who is very tall, I am quite ___.) → bajo (short)
                Contrast with another named person (useful for disambiguating within a category, e.g. family roles, without resorting to a definition): "Aunque mi padre cocina muy bien, mi ___ siempre prefiere pedir comida a domicilio." (Even though my father cooks well, my ___ always prefers to order delivery food.) → madre

                Here are some bad exmaples:
                Too generic: "Mi ___ es muy grande." → fails because many nouns fit
                Definitional: "Un edificio residencial independiente con paredes y techo donde vive una sola familia es una ___." → fails
                because it defines the word instead of using it naturally
                Leaks the answer: "Mis padres me compraron un ___ grande y peludo. (perro)" → fails because the parenthetical directly reveals the translation
                Whole-category ambiguity: "Usé el ___ para arreglar la tele." (I used the ___ to fix the TV.) → fails because any tool
                (destornillador, martillo, alicate...) fits equally well, not just the intended one. Same problem with "Me gusta comer ___
                para el almuerzo." (any food fits) or "Mi ___ amable me despierta y me hace el desayuno." (any family member fits).

                Before finalizing each question, check it against this: could an entire CATEGORY of words — not just the exact target term —
                fit the blank equally well (any tool, any food, any family member, any color, etc.)? If swapping in a different member of
                that same category would still make the sentence sound completely natural, the sentence is not specific enough. Fix it with
                a natural, concrete, distinguishing detail — a specific action, cause, contrast with another named person, or fact — that is
                true of the target word but not of other members of its category. Do NOT fix it by turning the sentence into a dictionary-style
                definition (e.g. "the person who gave birth to me") — that trades one banned pattern for another. Natural techniques like
                contrasting with another named person (see the madre/padre example above), pronouns, or situational context work better than
                spelling out what the word means.

                A pair may look like a verb (source_term or target_term begins with "to ", e.g. "to walk"), but this
                is a VOCABULARY list, not a verb-conjugation quiz — treat every pair as an ordinary word regardless
                of its shape. The blank and correct_answer are the target_term exactly as given (its bare infinitive
                form, e.g. "caminar"), never a conjugated form, and no parenthetical infinitive is added. The
                whole-category-ambiguity check above still applies to these pairs like any other.

                CRITICAL: every single question's sentence AND its answer must be entirely in {target_language}.
                Do not write any question in {source_language}. Double-check each question before finalizing.

                {focus_instruction}

                Now write a similar question for target term
                The question should be a natural sentence phrased to test the user's knowledge of {target_language}
                Do NOT write the question as a dictionary-style definition of target term.
                The sentence should use the word naturally, in a realistic situation or context,
                not describe or define what the word means.
                Use "_____" to mark where the blank goes. The blank is the target_term.
                Do not use source_term in the question text.

                Leave the "tense" field empty/null for every question — it only applies to a Verb list.

            """

    


    try: 
        response = client.models.generate_content(
        model = "gemini-3.5-flash-lite",
        contents = prompt,
        config = types.GenerateContentConfig(
            response_mime_type= "application/json",
            response_schema= QuestionBatch

        )
    )

    except Exception as e:
        raise GeminiAPIError(f"generate_question_batch failed: {e}") from e


    questions = [_repair_question(q) for q in response.parsed.questions]
    # The prompt guarantees "one question per pair, in the same order" —
    # zip by position rather than asking Gemini to echo an id back, which
    # would be both unreliable and unnecessary.
    for question, pair in zip(questions, pairs):
        question.vocab_pair_id = pair.get("id")

    # Modal verbs (devoir, pouvoir, ...) occasionally trip the self-collision
    # bug the prompt above warns against; verb pairs occasionally get left
    # unconjugated (answer == the bare infinitive) or lose their trailing
    # "(infinitive)" hint entirely, despite the prompt spelling both out.
    # Retry just the affected pair (up to _retries_left times) rather than
    # regenerating the whole batch — keeps the quiz's word selection intact
    # and only spends extra calls when a question actually needs it.
    if _retries_left > 0:
        for i, question in enumerate(questions):
            pair = pairs[i]
            needs_retry = _answer_duplicated_in_sentence(question) or (
                list_type == "verb"
                and (
                    _verb_answer_is_bare_infinitive(question, pair)
                    or _verb_parenthetical_missing(question)
                )
            )
            if not needs_retry:
                continue
            try:
                retried = generate_question_batch(
                    [pairs[i]],
                    source_language,
                    target_language,
                    1,
                    level,
                    verb_tenses,
                    flip,
                    focus,
                    list_type,
                    _retries_left=_retries_left - 1,
                )
                questions[i] = retried[0]
            except GeminiAPIError:
                pass  # keep the original rather than fail the whole batch

    return questions


SKIPPED_ANSWER = "(skipped)"


def split_quiz_evidence(attempts: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Sorts one quiz's recorded attempts into (wrong, correct), each item
    {"question", "typed", "correct"}.

    - wrong: graded incorrect. Skipped questions are left out entirely — a
      skip records no typed answer, so it carries no information about
      what kind of mistake is being made.
    - correct: graded correct. Answers accepted only because accents were
      ignored count as correct here too — the quiz accepted them, so the
      feedback doesn't hold them against the learner.
    """
    wrong, correct = [], []
    for attempt in attempts:
        typed = (attempt.get("user_answer") or "").strip()
        expected = (attempt.get("correct_answer") or "").strip()
        item = {"question": attempt.get("question_text") or "", "typed": typed, "correct": expected}
        if not attempt["was_correct"]:
            if typed == SKIPPED_ANSWER:
                continue
            wrong.append(item)
        else:
            correct.append(item)
    return wrong, correct


def analyze_last_quiz(
    wrong: list[dict],
    correct: list[dict],
    all_pairs: list[dict],
    target_language: str,
    count: int,
    message_language: str = "English",
) -> dict:
    """
    Reads ONE quiz's real answers — what was asked, what the learner typed,
    what was expected — and names what their mistakes have in common, as
    specifically as the evidence supports (a broad category when that's all
    the evidence shows, an exact feature like a specific ending or stem
    change when several mistakes share it, and plainly "no clear pattern"
    when they don't). Also picks `count` words from the full list that
    would practice that same pattern, and writes a one-sentence `focus`
    for the question writer.

    Returns {"message", "examples", "focus", "targeted_pair_ids"}.
    "examples" are built here from the numbers the model cites, not quoted
    by the model, so they can't be misremembered.

    The caller is responsible for not calling this on too little evidence
    (see MIN_WRONG_ANSWERS_FOR_INSIGHT in api/main.py).
    """
    evidence = [{"n": i, **item} for i, item in enumerate(wrong)]
    correct_summary = [{"question": c["question"], "answer": c["correct"]} for c in correct[:15]]
    full_list = [
        {"id": p["id"], "source word": p["source_term"], "target word": p["target_term"]}
        for p in all_pairs
    ]

    prompt = f""" A language learner is studying {target_language}. Below is their MOST RECENT quiz, question by question.

                MISTAKES, each with a number "n" (what they typed differs from the correct answer):
                {json.dumps(evidence, ensure_ascii=False)}

                QUESTIONS THEY ANSWERED CORRECTLY:
                {json.dumps(correct_summary, ensure_ascii=False)}

                Their full vocabulary list, to choose practice words from:
                {json.dumps(full_list, ensure_ascii=False)}

                Compare what they typed against the correct answer in each item and work out what the mistakes have
                in common. Be as specific as the evidence supports, and no more:
                - If two or more items share a specific feature — a particular ending, a stem change, a tense or
                  person, an accent on a particular form — name that exact feature (for example "missing the e→ie
                  stem change in tú forms like tienes", or "leaving the accent off -ábamos endings").
                - If they share only a broad category (accents in general, conjugation endings in general, noun
                  gender, spelling), name that broad category.
                - If the items have nothing meaningful in common, say plainly that you see no clear pattern and
                  mention the most notable individual slip. Never invent a pattern to sound helpful.
                Describe what you can SEE ("you wrote X where Y was needed"). Present the underlying cause as likely
                ("it looks like you're dropping...") — never as established fact.

                Return:
                - message: one or two encouraging sentences combining one thing they are doing well (only if the
                  correct answers support it) with what is giving them trouble, ending by noting that the next quiz
                  will target it. Write the message in {message_language} — the language the learner reads the app
                  in — even though they are studying {target_language}. Quote any {target_language} words or
                  endings exactly as they are.
                - evidence_indexes: the "n" numbers of up to 4 items above that best support the pattern you named.
                  Use only numbers that appear above.
                - focus: ONE sentence telling a question writer which skill to exercise, for example
                  "present-tense nosotros forms of -ar and -er verbs, where the -amos/-emos ending is required".
                  Use an empty string if there is no clear pattern.
                - targeted_pair_ids: the ids of {count} pairs from the full vocabulary list that would give the most
                  practice on that same pattern. If there is no clear pattern, pick a reasonable mix.
            """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PatternAnalysis,
            ),
        )
    except Exception as e:
        raise GeminiAPIError(f"analyze_last_quiz failed: {e}") from e

    analysis = response.parsed
    seen, examples = set(), []
    for n in analysis.evidence_indexes:
        if n in seen or not (0 <= n < len(evidence)):
            continue
        seen.add(n)
        item = evidence[n]
        examples.append(f"{item['typed']} → {item['correct']}")
        if len(examples) == 4:
            break

    return {
        "message": analysis.message,
        "examples": examples,
        "focus": analysis.focus.strip(),
        "targeted_pair_ids": analysis.targeted_pair_ids,
    }
