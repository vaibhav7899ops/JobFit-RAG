from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class JobCreate(BaseModel):
    external_id: str
    title: str
    company: str
    description: str
    url: HttpUrl


class JobRead(BaseModel):
    id: int
    external_id: str
    title: str
    company: str
    description: str
    url: HttpUrl
    fetched_at: datetime

    model_config = ConfigDict(from_attributes=True)
