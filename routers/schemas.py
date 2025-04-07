from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Новые модели для генераций
class GenerationCreate(BaseModel):
    title: str
    content: str

class GenerationPublish(BaseModel):
    published: bool
    publication_platform: Optional[str] = None
    social_network_url: Optional[str] = None

class Generation(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    generation_date: datetime
    published: bool
    publication_platform: Optional[str] = None
    publication_date: Optional[datetime] = None
    social_network_url: Optional[str] = None
