import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

ADZUNA_APP_ID = os.environ["ADZUNA_APP_ID"]
ADZUNA_APP_KEY = os.environ["ADZUNA_APP_KEY"]
ADZUNA_COUNTRY = "in"
ADZUNA_KEYWORDS = "software engineer"
JOB_SYNC_INTERVAL_HOURS = 4

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = "openai/gpt-oss-20b"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_PERSIST_DIR = "./chroma_data"
CHROMA_JOBS_COLLECTION = "jobs"
MATCH_TOP_K = 5
