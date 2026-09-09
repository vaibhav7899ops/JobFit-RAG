# Developer Log

## Architecture Discussion & Decisions

### 2026-09-08 — Postgres for relational data, not a DynamoDB-style KV store
DynamoDB-style single-table key-value patterns don't fit here. Users, resumes, jobs, and matches are relational — resumes and matches both carry foreign keys back to users, and matches link two entities (user + job) with query needs (filter/sort by score, join to job details) that map naturally onto SQL. Postgres was chosen for this relational core.

**Why:** The data has real relational structure (foreign keys, joins, multi-column filtering) that a KV/single-table design would force into awkward denormalization for no benefit at this scale.
**Tradeoff:** Postgres requires schema migrations as the app evolves, versus a schemaless KV store's flexibility — acceptable given the data is well-understood upfront.

### 2026-09-08 — ChromaDB for vector search, not pgvector
Vector search (resume/job embedding similarity) is handled by ChromaDB as a separate store, rather than the pgvector extension inside Postgres.

**Why:** Chosen deliberately for hands-on experience operating a dedicated vector database, rather than for a technical limitation of pgvector — this is a learning/portfolio project, and running a real vector DB alongside Postgres demonstrates that skill explicitly.
**Tradeoff:** Two datastores to run and keep in sync instead of one; added operational complexity that pgvector would have avoided.

### 2026-09-08 — Adzuna API for job data
Adzuna was chosen as the job listings data source.

**Why:** Free tier available and no Terms-of-Service risk, unlike scraping job boards directly.
**Tradeoff:** Job data quality/coverage is bounded by whatever Adzuna's free tier exposes, and the app is coupled to Adzuna's response schema.

### 2026-09-08 — APScheduler in-process instead of a separate cron service
Job syncing (pulling fresh listings from Adzuna) runs via APScheduler inside the FastAPI process rather than as an external cron job or separate worker service.

**Why:** Avoids standing up and deploying a second service just to run a periodic task, which is unnecessary overhead for this project's scale.
**Tradeoff:** Scheduled jobs are tied to the API process's lifecycle (restarts interrupt scheduling, and it won't scale cleanly if the API ever runs multi-instance) — acceptable for a single-instance portfolio deployment.

### 2026-09-08 — Free local embedding model instead of OpenAI's embedding API
Embeddings for resumes and jobs will be generated with a free, locally-run model rather than a paid API like OpenAI's embeddings endpoint.

**Why:** Keeps the project fully cost-free to run and demo indefinitely.
**Tradeoff:** Local embedding quality/speed likely lags a hosted model, and it adds a model-loading dependency to the app instead of a simple API call.

### 2026-09-08 — Matches cached and lazily regenerated
Match results (score + analysis) are cached in the `matches` table rather than recomputed on every request. They're only regenerated lazily, when a newer resume upload or a job sync makes the cached match stale.

**Why:** Match computation involves embedding lookups and an LLM call, both of which are relatively expensive — recomputing on every page view would be wasteful and slow.
**Tradeoff:** Requires tracking staleness (comparing resume/job timestamps against `calculated_at`) instead of always having fresh data, and there's a window where a match could technically be recomputed but hasn't been requested yet.

### 2026-09-08 — One batched LLM call for all 5 retrieved jobs
When generating match analysis, a single LLM call handles all 5 retrieved jobs at once, returning structured JSON for all of them, instead of issuing 5 separate per-job calls.

**Why:** Conserves free-tier LLM API rate limits — 1 call instead of 5 per match cycle.
**Tradeoff:** The batched call has a larger prompt/response payload and a single point of failure (if the batch call fails or returns malformed JSON, all 5 job analyses are lost, versus only losing one in a per-job design). Requires stricter output-format enforcement to reliably parse structured JSON for 5 jobs from one response.

### 2026-09-09 — ChromaDB over other vector DBs (Pinecone, Weaviate, Qdrant, Milvus)
Chroma was picked as the specific vector DB, not just "a vector DB in general."

**Why:** Pinecone is cloud-hosted and gated behind an API key with paid tiers past its free quota, which conflicts with the project's cost-free constraint the same way a paid embeddings API would. Weaviate, Qdrant, and Milvus are all capable, but heavier to self-host (Docker services, more config) than Chroma, which runs embedded/in-process or as a lightweight local server with minimal setup — less operational overhead for the same "operate a real vector DB" learning goal. Chroma's Python API is also the simplest of the group, which matters when the goal is learning vector-DB concepts (indexing, similarity search, metadata filtering) rather than fighting deployment.
**Tradeoff:** Chroma is less production-hardened and has fewer scaling/clustering features than Weaviate/Qdrant/Milvus, and less managed convenience than Pinecone — acceptable since this is a single-instance portfolio project, not a production deployment.

### 2026-09-09 — Postgres over other SQL databases (MySQL, SQLite)
Postgres was picked as the specific relational database, not just "a SQL DB in general."

**Why:** SQLite has no real concurrent-write support and no separate server process, so it doesn't hold up as a realistic stand-in for a deployable backend. MySQL is a legitimate alternative and roughly equivalent for this use case, but Postgres has native `JSON`/`JSONB` support (used directly for the `matches.analysis_json` column) and is the default pairing with `pgvector` in the Python/AI tooling ecosystem — so even though pgvector isn't being used (Chroma is, for the vector-DB learning goal above), Postgres keeps that door open at zero migration cost if the project ever needed it.
**Tradeoff:** None significant versus MySQL for this project's scale — this was more "the ecosystem default" than a hard technical requirement.

### 2026-09-09 — Alembic added for migrations, local Postgres installed via Homebrew
Alembic was wired up (`alembic/env.py` reads `DATABASE_URL` from `app.core.config` and points `target_metadata` at `Base.metadata` from `app.models`, instead of the default hardcoded-URL template) and an initial autogenerated migration was created and applied, producing real `users`, `resumes`, `jobs`, `matches` tables. Since no Postgres or Docker was available locally, Postgres 16 was installed via Homebrew and started as a background service (`brew services start postgresql@16`) to actually run the migration against.

**Why:** Models alone don't create database tables — a migration tool is needed both to create the schema and to evolve it safely later without hand-writing `ALTER TABLE` statements. Homebrew Postgres (vs. Docker or a hosted free tier) was chosen because it was the fastest path to a locally running instance with no extra setup, matching how the project is being run right now (no Docker installed).
**Tradeoff:** Local dev now depends on a machine-level Postgres service rather than a disposable container — reinstalling/resetting the DB isn't as clean as `docker compose down -v`, and this local setup won't automatically match a production environment the way a containerized one would.

### 2026-09-09 — Pydantic schema layer: Create/Read split per resource, most Create schemas are internal-only
Every resource gets separate `*Create` and `*Read` Pydantic schemas rather than one shared schema, and reusing the SQLAlchemy models directly as API request/response types was ruled out.

**Why:** Separating request shape from response shape keeps server-generated fields (`id`, timestamps, `password_hash`) out of what a client is allowed to submit, and lets the two contracts evolve independently. Walking through it resource by resource surfaced that most `Create` schemas aren't actually filled out by a client at all: `JobCreate` is used internally by the Adzuna sync service to validate/shape Adzuna's response before insert (catching a malformed upstream field at a clear boundary instead of a raw DB failure), `MatchCreate` is used internally by the matching service to validate the LLM's structured JSON output before insert (directly addressing the batched-LLM-call risk logged earlier), and `ResumeCreate` is also internal — the client uploads a file via `multipart/form-data` (`UploadFile`, not a Pydantic body), the server extracts the text, and only then is `ResumeCreate(user_id, raw_text)` constructed pre-insert. Only `UserCreate` is a true client-facing request body (signup).
**Tradeoff:** More files/classes than a single shared schema per resource, and the internal-only `Create` schemas add a validation step that could be skipped by writing directly to the ORM model — accepted because the point is to fail loudly at the boundary (bad Adzuna data, malformed LLM JSON) rather than let bad data reach Postgres silently.

### 2026-09-09 — Proper auth added: password_hash column, bcrypt + PyJWT
While designing `UserCreate`, decided the API needs real authentication rather than a bare email-only user record. Added `password_hash` (String, not null) to the `User` model via a new Alembic migration, and picked `passlib[bcrypt]` for hashing and `PyJWT` for tokens (over `python-jose`, which is less actively maintained).

**Why:** `UserCreate` needed a `password` field, which meant somewhere to store it — storing it raw was never on the table. bcrypt is the standard adaptive password-hashing choice; PyJWT was picked over `python-jose` for being more actively maintained and having a simpler API for issuing/verifying stateless bearer tokens.
**Tradeoff:** JWT is stateless, so there's no built-in server-side revocation (a leaked/stolen token stays valid until it expires) — acceptable for now given the project's scope, but worth knowing if asked about session invalidation.

### 2026-09-09 — Client never sends raw resume text or a raw LLM score
Two related boundary decisions: (1) `ResumeCreate.raw_text` is never populated from client input directly — clients upload a file, and text extraction happens server-side first. (2) `Match.score` lives only as a plain column, not duplicated inside `analysis_json`, after briefly considering storing it in both places.

**Why:** (1) Accepting raw pasted text from a client would skip the file-upload/parsing step entirely and is also just a worse UX than a file upload for a resume. (2) A single source of truth for `score` avoids the two values silently drifting apart; the column form is also what enables SQL-level sorting/filtering by score without touching the JSON blob.
**Tradeoff:** (2) means `score` is invisible if you only look at `analysis_json` in isolation — reading a full match always requires both the column and the JSON blob together, not just one artifact.

### 2026-09-09 — Bug: passlib + bcrypt 5.0.0 incompatibility, pinned bcrypt==4.0.1
`hash_password()` crashed on first real test with `AttributeError: module 'bcrypt' has no attribute '__about__'`, immediately followed by `ValueError: password cannot be longer than 72 bytes`. Root cause: `passlib` (last released 2020, effectively unmaintained) probes `bcrypt.__about__.__version__` to detect the backend version; `bcrypt` 4.1+ removed that attribute, so passlib's version-detection path breaks and falls through to a broken code path that mishandles the 72-byte bcrypt input limit.

**Why:** Pinned `bcrypt==4.0.1` (last version before `__about__` was removed) in `requirements.txt` rather than dropping `passlib` — passlib's `CryptContext` API is still the simplest way to hash/verify and handles algorithm-migration bookkeeping (e.g. `deprecated="auto"`) that would otherwise be hand-rolled.
**Tradeoff:** `requirements.txt` now pins bcrypt below its latest release, so a future `pip install -U` on `bcrypt` alone (without also updating passlib) will silently reintroduce this bug — worth remembering if passlib ever gets a maintained fork/replacement.

### 2026-09-09 — Auth core implemented: hashing + JWT helpers in app/core/security.py
`app/core/security.py` added: `hash_password`/`verify_password` (via `passlib` `CryptContext(schemes=["bcrypt"])`), and `create_access_token`/`decode_access_token` (via `PyJWT`, `HS256`, 24-hour expiry, `sub` claim = user email). `SECRET_KEY` added to `app/core/config.py`, read from a new `.env` var (random 32-byte hex generated for local dev, placeholder added to `.env.example`).

**Why:** `create_access_token` takes a generic `data: dict` (not a narrow `email: str` signature) so more claims can be added later without changing the function's shape. `decode_access_token` catches `jwt.PyJWTError` internally and returns `None` on any failure (expired, tampered, malformed) rather than raising, so the future "get current user" FastAPI dependency can do a simple `if not payload: raise 401` instead of a try/except around every call site.
**Tradeoff:** JWT remains stateless (noted in the earlier auth entry) — swallowing decode errors into `None` also means the caller loses the specific reason a token failed (expired vs. tampered vs. malformed) unless it's logged separately, which matters if you ever want to give a user a "your session expired" message versus a generic "invalid token."

### 2026-09-09 — Auth routes: /auth/signup and /auth/login, layered as routes → services → security
Implemented `POST /auth/signup` and `POST /auth/login` in `app/api/auth.py`, with the logic split across layers: `app/services/user_service.py` owns DB access (`get_user_by_email`, `create_user`), `app/core/security.py` owns hashing/JWT (already built), `app/api/deps.py` owns `get_current_user` (decodes the bearer token and loads the user, for protecting future routes), and the route functions in `auth.py` stay thin — just HTTP wiring calling into those layers. Signup auto-logs the user in (returns a `Token` immediately, not just the created user). Login uses FastAPI's standard `OAuth2PasswordRequestForm` (form-encoded `username`/`password`, `username` holds the email) instead of a custom JSON body schema.

**Why:** Splitting DB logic (services) from token/hashing logic (core) from HTTP logic (api) follows single-responsibility — each layer can be tested or swapped independently (e.g. business logic in `user_service.py` doesn't know or care that it's being called from an HTTP route). `OAuth2PasswordRequestForm` was chosen over a custom schema specifically so `/auth/login` plugs directly into Swagger UI's built-in "Authorize" button and FastAPI's OAuth2 tooling without custom wiring.
**Tradeoff:** `OAuth2PasswordRequestForm` forces the field name `username` even though this project has no concept of a username, only email — a minor naming mismatch that has to be explained/remembered at the call site. Auto-login on signup also means there's no separate "email verification before first use" step, which is fine for a portfolio project but would need revisiting for anything real-world facing.

### 2026-09-09 — Bug: OAuth2PasswordRequestForm needs python-multipart, not installed by default
The app crashed on import (`RuntimeError: Form data requires "python-multipart" to be installed`) as soon as the `/auth/login` route using `OAuth2PasswordRequestForm` was added — FastAPI's form-parsing dependency requires the `python-multipart` package, which isn't pulled in automatically by `fastapi` or `python-multipart`'s absence isn't caught until the route is actually defined (import time), not just when installing FastAPI.

**Why:** Added `python-multipart` to `requirements.txt`. No alternative considered — it's a hard requirement for any FastAPI form/file upload handling (this will also matter later for the resume file upload endpoint).
**Tradeoff:** None — straightforward missing dependency, not a design tradeoff. Worth remembering as a checklist item: any FastAPI route using `Form(...)`, `OAuth2PasswordRequestForm`, or `UploadFile` needs this package.

Verified end-to-end against the real local Postgres DB: signup creates a user with a bcrypt hash (not plaintext) and returns a token; duplicate-email signup is rejected with 400; login with correct credentials returns a token; login with a wrong password is rejected with 401.

### 2026-09-09 — Resume upload: PDF/DOCX, extracted server-side, protected route
Implemented `POST /resumes/upload` in `app/api/resumes.py`, sitting behind `get_current_user` so `Resume.user_id` always comes from the authenticated token, never a client-supplied field. Multiple resumes per user are allowed (no overwrite/replace — upload just inserts a new row, giving upload history). Extraction logic lives in `app/services/resume_service.py`: `pypdf` for PDF, `python-docx` for DOCX, dispatched by file extension. Rejects anything over 5MB.

**Why:** Same layering principle as auth — route stays thin, `resume_service.py` owns parsing/validation, `ResumeCreate`/`create_resume` handle the DB boundary (as already decided when designing schemas). `pypdf` was picked over `pdfplumber` for being lighter weight with no layout-preservation needs for plain text extraction.
**Tradeoff:** Keeping every historical resume means the "match against the newest resume" logic (referenced in the lazy-caching decision) needs to explicitly pick the most recent `Resume` row by `uploaded_at` rather than assuming one-resume-per-user — a query detail to remember when the matching service gets built.

### 2026-09-09 — File-type validation hardened: magic-byte check added alongside content-type/extension check
Initial upload validation only checked the file extension and the client-supplied `Content-Type` header. Both are attacker-controlled — a client can rename any file to `.pdf` and set the `Content-Type` header to `application/pdf` regardless of actual content. Added a second check against the real file bytes: PDF files must start with the `%PDF` magic bytes, and DOCX files (which are ZIP archives internally) must start with the ZIP signature `PK\x03\x04`.

**Why:** Extension/content-type checks stay as a fast, cheap initial reject (catches accidental wrong uploads with a clear error before even reading the full file), but the magic-byte check against actual content is the real security boundary, run after the size check. Verified live: a plain-text file renamed to `fake.pdf` with a spoofed `Content-Type: application/pdf` header passed the header check but was correctly rejected by the magic-byte check with a 400.
**Tradeoff:** Magic-byte sniffing only proves "this is really a PDF/ZIP container," not that the internal structure is fully well-formed or safe — a malformed-but-technically-valid PDF could still fail later inside `pypdf`'s parser (that failure just wouldn't be a clean validation error, worth hardening further if this were production-facing).

Verified end-to-end: valid PDF upload extracts text correctly, valid DOCX upload extracts text correctly, unauthenticated upload rejected with 401, wrong-extension upload rejected with 400, and the spoofed-file attack above rejected with 400 — all against the real Postgres DB with resulting rows inspected via psql, then cleaned up.

### 2026-09-09 — Adzuna sync service implemented: layered clients, APScheduler on a 4-hour interval
Built the job sync pipeline across three files, following the same layering as auth/resumes: `app/services/adzuna_client.py` (raw HTTP call to Adzuna's search endpoint via `httpx`, country=`in`, keywords="software engineer"), `app/services/job_service.py` (DB access: lookup/create), `app/services/job_sync_service.py` (orchestration: fetch → map raw Adzuna JSON into `JobCreate` → skip if malformed → skip if duplicate → insert). `app/core/scheduler.py` wires this into APScheduler's `BackgroundScheduler`, triggered every `JOB_SYNC_INTERVAL_HOURS` (4), started/stopped via FastAPI's `lifespan` hook in `app/main.py`. A malformed individual Adzuna record (missing field, fails `JobCreate` validation) is logged and skipped rather than aborting the whole sync run.

**Why:** Same single-responsibility split as the auth/resume services — `adzuna_client.py` only knows about talking to Adzuna, `job_service.py` only knows about the DB, `job_sync_service.py` only knows about combining them; each can be tested or replaced independently. Using `httpx` synchronously inside the scheduled job is correct because APScheduler's `BackgroundScheduler` runs jobs in worker threads, not the async event loop. Skip-and-continue on a malformed record (rather than aborting the batch) mirrors the reasoning already logged for the batched-LLM-call risk — one bad record shouldn't sacrifice an otherwise-good sync of ~50 jobs.
**Tradeoff:** APScheduler running in-process ties job syncing to the API process's lifecycle, as already noted in the original APScheduler decision entry. Skip-and-continue also means partial/silent data loss for malformed records is possible without someone checking logs — acceptable for a portfolio project, would need alerting in a real deployment.

### 2026-09-09 — Bug: dedup-by-URL was structurally broken; Adzuna's redirect_url includes a per-request tracking token
First live test of the sync (against the real Adzuna API and real Postgres) ran twice and produced 100 rows instead of staying at 50 — the dedup check (by `Job.url`, `UNIQUE` constraint added earlier) never matched. Root cause, confirmed by inspecting the raw response: Adzuna's `redirect_url` field embeds a per-API-call tracking token (`se=...`) that changes on every request, even for the exact same job listing (verified: same Adzuna ad ID `5876027648` had two different `url` values across the two sync runs). URL was never a valid identity key for a job — it was assumed to be stable without checking Adzuna's actual response shape first.

**Why:** Added a new `external_id` column to `Job` (Adzuna's raw `id` field, e.g. `"5876027648"`, confirmed stable across repeated calls to the same listing), moved the `UNIQUE` constraint from `url` to `external_id`, and dedup now checks `external_id` instead. `url` itself is kept (still needed to link out to the actual posting) but is no longer treated as an identity/dedup key.
**Tradeoff:** Required a second migration and a second live re-test cycle so soon after the first (`url` uniqueness) turned out to be the wrong design — a reminder that a DB-level uniqueness decision should be validated against a real sample of upstream data before committing to a migration, not just assumed from the field's name. Verified the fix by running the sync twice in a row: 50 inserted on run 1, 0 inserted / 50 skipped as duplicates on run 2.

### 2026-09-09 — Matching pipeline implemented: embeddings, Chroma retrieval, batched Groq call, cache-as-history
Built the full `GET /matches` flow across several layers: `app/services/embedding_service.py` (`sentence-transformers`, `all-MiniLM-L6-v2`, loaded once at module import), `app/db/chroma.py` (persistent Chroma client, `jobs` collection), job embedding happens live inside `job_service.create_job` (title+company+description embedded, Chroma doc id = Postgres job id as a string, `title`/`company` also stored as Chroma metadata), `app/services/groq_client.py` (batched call to Groq, `response_format={"type": "json_object"}`, parsed and validated into `BatchAnalysisResponse` before use), `app/services/match_service.py` (DB layer: latest resume, latest job-sync time, current-matches-for-user, create), and `app/services/matching_service.py` (orchestration: staleness check → Chroma top-5 retrieval → batched Groq call → store).

Two decisions worth calling out: (1) matches are kept as **history**, not overwritten — each recompute stamps all 5 new `Match` rows with one shared `calculated_at` timestamp (captured once in Python, not per-row via the DB's `server_default=func.now()`), which makes "current matches for a user" a clean query (`WHERE calculated_at = MAX(calculated_at) for that user`) without needing a separate batch-id column. (2) The matching service raises plain `ValueError`s rather than FastAPI's `HTTPException`, keeping it framework-agnostic; the route layer (`app/api/matches.py`) is what translates those into HTTP 400s.

**Why:** Stamping one shared timestamp per batch was the key trick that let "keep old matches as history" (your choice) coexist with a simple staleness/current-batch query, without extra schema (like a `batch_id` FK) or a more complex windowed query. Framework-agnostic service errors keep `matching_service.py` testable and reusable outside an HTTP context.
**Tradeoff:** Because timestamps must be assigned in application code (not the DB default) to guarantee they match exactly across 5 rows inserted via separate `commit()` calls, the service layer now owns a responsibility (time-stamping) that's normally the DB's job — a subtle coupling to remember if match creation logic is ever refactored.

Verified live end-to-end against real Postgres, real Chroma, real Groq: signup → upload resume → `GET /matches` returned 5 real, distinct-scored (15–80) analyses with genuine reasoning tied to the actual resume content; second call returned instantly (0.02s vs 4.2s) with identical match IDs and `calculated_at`, confirming the cache path skips re-embedding/re-calling Groq; a user with no resume correctly got a 400 with a clear message.

### 2026-09-09 — Bug: Groq deprecated llama-3.1-8b-instant; model lineup changed entirely
The first live call to `/matches` failed with `groq.NotFoundError: 404 — model 'llama-3.1-8b-instant' does not exist`. Querying Groq's live `/models` list showed their catalog has shifted away from Llama models entirely toward models like `openai/gpt-oss-20b`/`openai/gpt-oss-120b`, `qwen/*`, and `groq/compound*` — the model chosen during planning (before implementation) no longer existed by the time the code was actually run.

**Why:** Switched `GROQ_MODEL` to `openai/gpt-oss-20b`, the closest match to the original "speed over quality" preference (smaller model, same reasoning as picking 8b over 70b originally) among what Groq currently serves.
**Tradeoff:** None design-wise, but a good real-world lesson: free-tier hosted LLM providers can deprecate/rename models between when you plan against documentation and when you actually run the code — a hardcoded model string is a single point of future breakage. Worth remembering as an answer to "what would you improve" — e.g. validating the configured model against `client.models.list()` at startup, or making it env-configurable instead of a hardcoded constant, to fail fast with a clear error instead of only discovering it at first real request.

### 2026-09-09 — Remaining read endpoints added: /users/me, /resumes (list), /jobs, /jobs/{id}
Rounded out the API surface: `GET /users/me` (protected, returns the authenticated user), `GET /resumes` (protected, current user's resume history ordered newest-first), `GET /jobs` (public, paginated with `skip`/`limit` query params, 20 default / 100 max per page) and `GET /jobs/{id}` (public, 404 if not found).

**Why:** Jobs were made public (no `get_current_user` dependency) since job listings aren't user-specific or sensitive — unlike resumes, matches, or the user's own profile, which all stay behind auth. Pagination on `GET /jobs` defaults to a small page size to avoid accidentally returning the whole `jobs` table in one response as the sync job keeps growing it every 4 hours.
**Tradeoff:** None significant — these were straightforward reads following the same layered pattern (route → service → DB) as everything else.

Verified live: `/users/me` returns the correct profile and 401s without a token; `/resumes` correctly returns `[]` before any upload and the new row after uploading; `/jobs` returns paginated real synced jobs; `/jobs/{id}` returns a specific job and 404s on a nonexistent id.

### 2026-09-09 — Test suite added: real Postgres test DB, mocked external services, transaction-rollback isolation
Built out `tests/` (pytest) covering security (hash/JWT round-trips), auth (signup/login/duplicate-email/wrong-password), resume upload (valid PDF/DOCX, wrong extension, spoofed-file rejection via magic bytes, history listing), jobs (list/paginate/get/404, public no-auth), job sync (insert, dedup-by-external_id even when `url` changes — a direct regression test for the earlier live bug, malformed-record skip), and matching (no-resume/no-jobs errors, recompute-when-no-matches, cache-hit-when-fresh, recompute-when-resume-is-newer). 35 tests, all passing.

Infra decisions: a **separate real Postgres database** (`jobfit_rag_test`) rather than SQLite, created fresh via `Base.metadata.create_all()`/`drop_all()` (not Alembic — tests don't need migration history, just a clean schema); each test runs inside its own DB transaction that's rolled back afterward (via a `db` fixture wrapping a connection+transaction, with `get_db` overridden to yield that same session) for fast, fully-isolated tests without needing to `TRUNCATE` between runs; **external services are mocked** (Adzuna's `fetch_jobs`, Groq's `analyze_resume_against_jobs`, the embedding model, and Chroma's `.add`/`.query`) rather than called for real, since the manual live testing already proved those integrations work — the automated suite's job is to catch regressions in this project's own logic, not to re-verify third-party APIs (and cost quota) on every run. A `TESTING` env var added to `app/main.py`'s `lifespan` skips starting the real APScheduler background thread during tests.

**Why:** Real Postgres over SQLite for fidelity to the actual constraints in use (`UNIQUE` on `external_id`, the `JSON` column) without behavioral surprises from a different DB engine. Transaction rollback (not truncate-after-each-test) is the standard fast-isolation pattern and avoids sequence/ID drift between tests. Mocking external services keeps the suite fast, deterministic, free, and runnable without real API keys (e.g. in CI).
**Tradeoff:** A `TESTING` env check inside production `main.py` is a small compromise — mixing test-awareness into app code rather than a cleaner dependency-injection approach — accepted for simplicity given the project's scope. Mocking also means the test suite can't catch a real third-party contract change (like the Groq model-deprecation bug found earlier) — that class of bug can only be caught by the kind of manual live testing already done, not by an automated suite that never talks to the real API.

Verified: full suite passes twice in a row with no state leakage between runs (confirming rollback isolation actually works, not just "happens to pass once").

### 2026-09-10 — Frontend built: Next.js 16 (App Router, TypeScript, Tailwind), httpOnly-cookie auth via server-side proxy routes
Built `frontend/` as a separate Next.js app: `/`, `/signup`, `/login`, `/upload` (resume upload + history), `/matches` (scored job dashboard), `/jobs` (public paginated browse). Auth uses a JWT stored in an `httpOnly` cookie rather than `localStorage` — the browser never touches the token directly. To make that work, the browser talks only to Next.js's own Route Handlers under `frontend/src/app/api/*` (`auth/signup`, `auth/login`, `auth/logout`, `auth/me`, `resumes`, `resumes/upload`, `matches`, `jobs`), which run server-side, read the `httpOnly` cookie via `next/headers`'s `cookies()`, and forward the request to the FastAPI backend with an `Authorization: Bearer` header attached. Route protection (`/upload`, `/matches` require auth; `/login`, `/signup` redirect away if already authenticated) is implemented in `frontend/src/proxy.ts`.

**Why:** Browser-only-talks-to-Next.js means the FastAPI backend never needs CORS configuration — all backend calls are server-to-server. `httpOnly` cookie over `localStorage` was the user's explicit choice for stronger XSS resistance, accepting the added complexity of a full proxy layer instead of the browser calling FastAPI directly with a header it manages itself.
**Tradeoff:** Every backend call now round-trips through an extra Next.js hop (browser → Next.js route handler → FastAPI) instead of browser → FastAPI directly — added latency and more code (10 proxy route files) versus the `localStorage` alternative. Login's proxy route also has to translate JSON `{email, password}` into the form-encoded `username`/`password` shape FastAPI's `OAuth2PasswordRequestForm` expects, since the two layers use different request shapes by design.

### 2026-09-10 — Bug/gotcha: Next.js 16 renamed middleware.js to proxy.js; docs in training data were stale
Scaffolding with `create-next-app` produced a `node_modules/next/dist/docs/` bundle and an `AGENTS.md` explicitly warning that this Next.js version has breaking changes from prior knowledge. Confirmed by checking the actual shipped docs before writing route-protection code: `middleware.js` (the file convention used in all prior Next.js versions for request interception/redirects) is deprecated in Next.js 16 and renamed to `proxy.js` — same `NextRequest`/`NextResponse` API, different file name and export (`proxy` instead of `middleware`). Also confirmed `cookies()` from `next/headers` is async (`await cookies()`) in this version, not sync.

**Why:** Checked the version-shipped docs (`node_modules/next/dist/docs/`) instead of relying on prior knowledge of Next.js conventions, specifically because the scaffold's own `AGENTS.md` flagged that this version has undocumented-in-training-data breaking changes. Writing `middleware.ts` would have silently failed to protect any routes (wrong file name = Next.js never loads it) rather than raising a clear error.
**Tradeoff:** None — this was purely a "verify against the actual installed version before writing code" catch, not a design tradeoff. Good example for an interview of why checking a fast-moving framework's actual shipped docs matters more than "how it's always worked."

Verified end-to-end in a real headless-Chromium browser session (Playwright), not just curl: fresh signup through the actual UI form → httpOnly cookie set → nav bar correctly switches to authenticated state → resume upload through the real file input → `/matches` correctly shows the "upload a resume first" state before any resume exists, then renders real, distinct, color-coded scored matches (sorted highest-first) with genuine LLM-generated matching/missing skills reasoning after upload. Also verified server-side via curl with a cookie jar: multipart file upload proxying, `/api/auth/me`, unauthenticated 401s on `/api/matches` and `/api/resumes/upload`, and all four `proxy.ts` redirect cases (protected page without cookie → redirect to `/login`; protected page with cookie → 200; auth page with cookie → redirect to `/matches`; auth page without cookie → 200).

### 2026-09-10 — Deployed: Railway (backend + Postgres + persistent Chroma volume) + Vercel (frontend)
Backend deployed to Railway: a `backend` service (FastAPI), a managed `Postgres` add-on, and a persistent volume mounted at `/app/chroma_data` attached to `backend` so Chroma's index survives restarts/redeploys. Frontend deployed to Vercel, connected to the GitHub repo, with `BACKEND_URL` set as a production environment variable pointing at the Railway service's public domain. Verified live end-to-end through the real public URLs (not just locally): landing/jobs pages load, signup through `jobfit-rag.vercel.app` correctly proxies to the Railway backend and sets the auth cookie, `/api/auth/me` returns the right user.

**Why:** Railway (not a more "serverless-first" host) was chosen specifically because two backend requirements rule out most free PaaS tiers: the in-process APScheduler job-sync loop needs a long-running process, not a serverless function that scales to zero; and Chroma writes its index to local disk, which needs to survive restarts/redeploys, not the ephemeral filesystem most free web-service tiers provide. Vercel was the natural fit for the frontend specifically because it's stateless (a pure proxy layer to the backend) and gets Next.js's first-party host for free.
**Tradeoff:** Two separate platforms/accounts to manage instead of one, and Railway's free allowance is a trial credit rather than a permanently free tier (unlike the local-dev cost-free constraint that shaped the embeddings/LLM choices earlier) — production hosting costs money past that trial, which is an explicit, accepted departure from "fully cost-free" for local dev.

### 2026-09-10 — Bugs/gotchas hit deploying to Railway
Several real issues surfaced only once actually deploying, not during local development:

1. **Config file rename**: `railway.toml` is deprecated in favor of `railpack.json` (Railway's build system is now called Railpack, not Nixpacks) — the first deploy attempt failed with "No start command detected" because the deprecated config format wasn't being read for the start command. Fixed by checking Railpack's actual docs and switching to `railpack.json` with `{"deploy": {"startCommand": "..."}}`.
2. **`railway volume add` CLI panic**: the CLI command to attach a persistent volume crashed with a Rust panic (`Option::unwrap() on a None value`) on every attempt, including with an explicit `--environment` flag. Worked around by using `railway api` to call the underlying `volumeCreate` GraphQL mutation directly, bypassing the broken CLI subcommand entirely.
3. **Double-triggered redeploy left the service down**: attaching the volume (or the follow-up `railway redeploy` call, or both together) triggered two concurrent builds for the same service; both got stuck `BUILDING` far longer than the original deploy, and the previously-running instance was torn down in the meantime — the backend was actually offline (404) for several minutes with no active deployment. Recovered by running a fresh `railway up` (not `redeploy`), which completed normally using cached image layers and came back up with the volume correctly mounted (confirmed via a `Mounting volume on: ...` log line before `Starting Container`).

**Why:** All three were verified by checking actual CLI output/docs/logs in the moment rather than assuming prior Railway knowledge still held — consistent with the Next.js `middleware`→`proxy` rename and the Groq model deprecation found earlier in this project. Platform CLIs and build systems change fast enough that "how it used to work" isn't a safe assumption to deploy against.
**Tradeoff:** None design-wise — these were tooling reliability issues, not application bugs. Worth remembering for an interview: real deployments surface a different class of problem (CLI bugs, build-system renames, race conditions between concurrent deploys) than local development or automated tests ever will, which is part of why "it works on my machine" isn't the same claim as "it's deployed and verified."

---

*Going forward: every real bug, design decision, or tradeoff discovered while building gets a dated entry here — what happened, why we chose the solution we did, and what the tradeoff was.*
