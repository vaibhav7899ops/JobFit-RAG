from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeCreate(BaseModel):
    user_id: int
    raw_text: str


class ResumeRead(BaseModel):
    id: int
    user_id: int
    raw_text: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
