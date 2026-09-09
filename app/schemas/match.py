from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SkillMatch(BaseModel):
    name: str
    reason: str


class MatchAnalysis(BaseModel):
    matching_skills: list[SkillMatch]
    missing_skills: list[SkillMatch]
    summary: str


class JobAnalysisResult(BaseModel):
    job_id: int
    score: int = Field(ge=0, le=100)
    matching_skills: list[SkillMatch]
    missing_skills: list[SkillMatch]
    summary: str


class BatchAnalysisResponse(BaseModel):
    analyses: list[JobAnalysisResult]


class MatchCreate(BaseModel):
    user_id: int
    job_id: int
    score: int = Field(ge=0, le=100)
    analysis_json: MatchAnalysis


class MatchRead(BaseModel):
    id: int
    user_id: int
    job_id: int
    score: int
    analysis_json: MatchAnalysis
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)
