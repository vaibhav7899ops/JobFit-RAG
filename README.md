# JobFit-RAG

A resume-to-job matching platform. Upload a resume, and a RAG pipeline retrieves the most
relevant synced job listings and scores each one with an LLM-generated breakdown of matching
and missing skills.

## Architecture

- **Backend**: FastAPI + PostgreSQL (SQLAlchemy + Alembic migrations)
- **Vector search**: ChromaDB (persistent) + `sentence-transformers` (`all-MiniLM-L6-v2`) for
  resume/job embeddings
- **Job data**: [Adzuna API](https://developer.adzuna.com/), synced on a schedule via
  APScheduler running in-process
- **Matching**: top-5 retrieval from Chroma, then a single batched call to Groq
  (`openai/gpt-oss-20b`) that scores and analyzes all 5 jobs against the resume in one request
- **Auth**: JWT (bcrypt-hashed passwords, 24h token expiry)
- **Frontend**: Next.js 16 (App Router, TypeScript, Tailwind), JWT stored in an `httpOnly`
  cookie, all backend calls proxied through Next.js server-side route handlers (browser never
  talks to FastAPI directly)

Design decisions, tradeoffs, and bugs hit along the way are logged in
[docs/developer-log.md](docs/developer-log.md).

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL running locally (or a connection string to one)
- Free API keys: [Adzuna](https://developer.adzuna.com/) (`app_id` + `app_key`) and
  [Groq](https://console.groq.com/)

## Backend setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # or requirements-dev.txt to include test tooling

cp .env.example .env
# edit .env: DATABASE_URL, SECRET_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY, GROQ_API_KEY

createdb jobfit_rag
alembic upgrade head

uvicorn app.main:app --reload --port 8000
```

The backend starts an in-process scheduler that syncs jobs from Adzuna every 4 hours (see
`JOB_SYNC_INTERVAL_HOURS` in `app/core/config.py`). Job embeddings are written to a local
`chroma_data/` directory on first sync.

### Running tests

```bash
createdb jobfit_rag_test
pip install -r requirements-dev.txt
pytest
```

Tests run against a real (separate) Postgres database with per-test transaction rollback for
isolation. External services (Adzuna, Groq, the embedding model, Chroma) are mocked.

## Frontend setup

```bash
cd frontend
npm install

cp .env.local.example .env.local
# edit .env.local if the backend isn't at http://localhost:8000

npm run dev
```

Visit `http://localhost:3000`.

## API overview

| Method | Path             | Auth | Description                              |
| ------ | ---------------- | ---- | ----------------------------------------- |
| POST   | `/auth/signup`   | -    | Create an account, returns a JWT          |
| POST   | `/auth/login`    | -    | Log in (OAuth2 form body), returns a JWT  |
| GET    | `/users/me`      | ✓    | Current user's profile                    |
| POST   | `/resumes/upload`| ✓    | Upload a PDF/DOCX resume (max 5MB)        |
| GET    | `/resumes`       | ✓    | Current user's resume upload history      |
| GET    | `/jobs`          | -    | Paginated list of synced jobs             |
| GET    | `/jobs/{id}`     | -    | A single job                              |
| GET    | `/matches`       | ✓    | Top-5 scored matches for the latest resume (cached until resume/jobs change) |

## Repo layout

```
app/                  FastAPI backend
  api/                 route handlers
  core/                 config, JWT/hashing, scheduler
  db/                    SQLAlchemy session, Chroma client
  models/               SQLAlchemy ORM models
  schemas/              Pydantic request/response schemas
  services/             business logic (auth, resumes, jobs, matching)
alembic/               DB migrations
tests/                 pytest suite
frontend/              Next.js app
docs/developer-log.md  architecture decisions, tradeoffs, bugs (dated log)
```
