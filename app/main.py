import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.jobs import router as jobs_router
from app.api.matches import router as matches_router
from app.api.resumes import router as resumes_router
from app.api.users import router as users_router
from app.core.scheduler import scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.environ.get("TESTING"):
        start_scheduler()
    yield
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(title="JobFit-RAG", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(matches_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    return {"status": "ok"}
