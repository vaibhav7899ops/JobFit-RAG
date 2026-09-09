import json

from groq import Groq
from pydantic import ValidationError

from app.core.config import GROQ_API_KEY, GROQ_MODEL
from app.schemas.match import BatchAnalysisResponse

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a resume-to-job matching assistant. You will be given one resume and a list of \
candidate jobs. For EACH job, evaluate how well the resume fits it and return a score from 0 to 100.

Respond with ONLY a JSON object of this exact shape, no other text:
{
  "analyses": [
    {
      "job_id": <int, the job's id from the input>,
      "score": <int, 0-100>,
      "matching_skills": [{"name": "<skill>", "reason": "<why it matches>"}],
      "missing_skills": [{"name": "<skill>", "reason": "<why the resume lacks it>"}],
      "summary": "<2-3 sentence summary of the fit>"
    }
  ]
}

You MUST return exactly one analysis object per job given, in any order, using the given job_id values."""


def analyze_resume_against_jobs(resume_text: str, jobs: list[dict]) -> BatchAnalysisResponse:
    jobs_block = "\n\n".join(
        f"Job id: {job['id']}\nTitle: {job['title']}\nCompany: {job['company']}\nDescription: {job['description']}"
        for job in jobs
    )
    user_prompt = f"RESUME:\n{resume_text}\n\nJOBS:\n{jobs_block}"

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    raw_content = response.choices[0].message.content

    try:
        parsed = json.loads(raw_content)
        return BatchAnalysisResponse.model_validate(parsed)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Groq returned a malformed batch analysis response: {e}") from e
