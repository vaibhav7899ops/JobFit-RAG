import httpx

from app.core.config import ADZUNA_APP_ID, ADZUNA_APP_KEY, ADZUNA_COUNTRY, ADZUNA_KEYWORDS

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


def fetch_jobs(page: int = 1, results_per_page: int = 50) -> list[dict]:
    url = f"{ADZUNA_BASE_URL}/{ADZUNA_COUNTRY}/search/{page}"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": ADZUNA_KEYWORDS,
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }
    response = httpx.get(url, params=params, timeout=10.0)
    response.raise_for_status()
    return response.json().get("results", [])
