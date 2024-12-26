from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str

from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"