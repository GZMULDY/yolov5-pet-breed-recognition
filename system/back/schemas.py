from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class LoginRequest(BaseModel):
    username: str
    password: str
    captcha_key: Optional[str] = None
    captcha_code: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str  # 返回角色以便前端判断

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None

class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None

class UserProfile(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    role: str
    created_at: Optional[datetime]
    last_login: Optional[datetime]
    is_verified: bool

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    created_at: Optional[datetime]
    last_login: Optional[datetime]
    is_verified: bool

    class Config:
        from_attributes = True

# Email Verification
class EmailSchema(BaseModel):
    email: List[EmailStr]

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

# Article Schemas
class ArticleBase(BaseModel):
    title: str
    content: str
    cover_image: Optional[str] = None

class ArticleCreate(ArticleBase):
    pass

class ArticleUpdate(ArticleBase):
    title: Optional[str] = None
    content: Optional[str] = None

class Article(ArticleBase):
    id: int
    author_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
