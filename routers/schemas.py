from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str
