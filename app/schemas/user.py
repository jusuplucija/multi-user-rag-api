from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., max_length=72)

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password should have at least 6 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=72)

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password should have at least 6 characters")
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str