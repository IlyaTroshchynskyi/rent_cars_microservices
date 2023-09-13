from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class UpdatePassword(BaseModel):
    old_password: str
    new_password: str
