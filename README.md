# LangReps API

FastAPI backend for **LangReps**, a vocabulary-learning app for serious language learners. Users build vocab lists (typed, pasted, uploaded from a file, or read from a photo), then take AI-generated quizzes on them. After a quiz, the AI reads the learner's actual mistakes and writes tailored feedback, and can generate a follow-up quiz that targets those mistakes.

The mobile app lives in a separate repo: [langreps-app](https://github.com/roycefum/langreps-app) (React Native + Expo).

## Stack

- **FastAPI** + Uvicorn
- **Supabase** (Postgres + Auth) for lists, quiz sessions, attempts, and user profiles
- **Google Gemini** (`google-genai`) for question generation, quiz analysis, vocab extraction, translation, and language detection
- Deployed on **Railway** (`Procfile`)

## Setup

Requires Python 3.13.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the repo root (it is gitignored — never commit it):

```
SUPABASE_URL=...
SUPABASE_KEY=...
GEMINI_API_KEY=...
```

Run locally:

```bash
uvicorn api.main:app --reload
```

The interactive API docs are at `http://127.0.0.1:8000/docs`.

## Database

The Supabase project is shared with the older Streamlit prototype (`language-tutor`). Schema changes live as SQL files in the repo root and are run by hand in the Supabase SQL editor:

- `add_user_profiles_table.sql` — per-user learning languages (table, RLS policies, and the `GRANT` to `authenticated` that Supabase also requires)
- `drop_part_of_speech_column.sql` — optional cleanup of a removed column

Row Level Security is on; requests act as the signed-in user via their access token.

## Project layout

```
api/
  main.py                    Route definitions
  schemas.py                 Request models
  deps.py                    Auth / DB-client dependencies
auth/
  supabase_auth.py           Sign up, log in, log out, password reset
core/
  question_generator.py      Quiz question writing + last-quiz analysis
  sample_list_generator.py   AI-generated starter lists for new users
  sample_lists.py            English master lists the generator translates
  extraction.py              Vocab from images and pasted text
  translator.py              Fills in missing translations
  language_detector.py       Detects a list's language pair
  cefr.py, tenses.py         Level and verb-tense guidance for prompts
data/
  db.py                      Supabase queries
  models.py                  Pydantic models
```

## API overview

All routes except sign-up, log-in, and password reset require a bearer token from `/login`.

| Area | Routes |
|---|---|
| Auth | `POST /signup`, `/login`, `/logout`, `/request-password-reset`, `/reset-password`; `DELETE /account` |
| Profile | `GET`/`PATCH /me/profile`; `POST /sample-lists` |
| Lists | `POST /save-list`; `GET /lists`, `/lists/{id}`; `PATCH`/`PUT`/`DELETE /lists/{id}` |
| Building lists | `POST /extract-vocab-from-image`, `/parse-vocab-text`, `/detect-language`, `/translate-word-list` |
| Quizzes | `POST /generate-questions`; `GET /lists/{id}/quiz-pairs` |
| Feedback | `GET /lists/{id}/quiz-insight`, `/lists/{id}/quiz-history` |
| Sessions | `POST`/`PATCH /quiz-sessions`; `GET /quiz-sessions`, `/quiz-sessions/completed`, `/quiz-sessions/{id}/attempts`; `DELETE /quiz-sessions/{id}` |
| Attempts | `POST /quiz-attempts` |

## How the quiz feedback works

- A quiz records each answer (what was asked, what was typed, the correct answer).
- `GET /lists/{id}/quiz-insight` looks only at the **last completed quiz** on that list. With at least 3 wrong answers, Gemini finds what the mistakes have in common — as specific as the evidence supports, no more — and returns a short message, real "typed → correct" examples, and a `focus` for the next quiz.
- Sending that `focus` to `/generate-questions` writes a quiz that targets the pattern. Ordinary quizzes are a plain random spread with no weighting.
- Answers accepted only because accents were ignored count as correct and are not held against the learner.

## Deployment

Pushing to `main` deploys to Railway. Set the three environment variables above in the Railway service settings.
