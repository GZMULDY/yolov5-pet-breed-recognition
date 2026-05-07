"""
Pydantic 数据验证模式定义模块

【模块职责】
定义 API 请求和响应的数据结构，实现自动验证、序列化和文档生成。

【核心功能】
1. 请求数据验证：确保客户端提交的数据格式正确
2. 响应数据序列化：控制返回给客户端的数据格式
3. OpenAPI 文档生成：FastAPI 自动根据 Schema 生成 API 文档

【设计模式】
采用类继承模式组织 Schema：
- Base: 公共字段基类
- Create: 创建请求 Schema
- Update: 更新请求 Schema
- Response: 响应 Schema

【数据流向】
客户端请求 JSON → Pydantic 验证 → Python 对象 → 路由处理
路由返回对象 → Pydantic 序列化 → JSON 响应 → 客户端

【验证规则】
- Optional[T]: 字段可选，可为 None
- EmailStr: 自动验证邮箱格式
- from_attributes = True: 允许从 ORM 模型转换
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


# =============================================================================
# 枚举定义
# =============================================================================
class UserRole(str, Enum):
    """
    用户角色枚举

    【继承 str】
    继承 str 使得枚举值可以像字符串一样使用，便于 JSON 序列化

    【角色说明】
    - ADMIN: 管理员，拥有所有权限（用户管理、文章管理等）
    - USER: 普通用户，权限受限（只能管理自己的数据）

    【使用示例】
    if user.role == UserRole.ADMIN:
        # 执行管理员操作
        pass
    """
    ADMIN = "admin"
    USER = "user"


# =============================================================================
# 认证相关 Schema
# =============================================================================
class LoginRequest(BaseModel):
    """
    登录请求 Schema

    【字段说明】
    - username: 用户名，必填
    - password: 密码，必填
    - captcha_key: 验证码标识，可选（用于获取对应的验证码图片）
    - captcha_code: 用户输入的验证码，可选

    【验证流程】
    1. 如果提供了 captcha_key 和 captcha_code
    2. 后端从缓存中查找 key 对应的验证码
    3. 对比用户输入是否正确

    【数据流向】
    客户端 POST /api/v1/login → LoginRequest → 验证 → 返回 Token
    """
    username: str
    password: str
    captcha_key: Optional[str] = None
    captcha_code: Optional[str] = None


class TokenResponse(BaseModel):
    """
    登录成功响应 Schema

    【字段说明】
    - access_token: JWT 访问令牌，客户端需保存在本地
    - token_type: 令牌类型，固定为 "bearer"
    - role: 用户角色，前端根据角色显示不同界面

    【客户端处理】
    1. 保存 token 到本地存储（localStorage/sessionStorage）
    2. 后续请求在 Authorization 头携带此 token
    3. 格式: Authorization: Bearer <access_token>
    """
    access_token: str
    token_type: str
    role: str  # 返回角色以便前端判断


# =============================================================================
# 用户相关 Schema
# =============================================================================
class UserBase(BaseModel):
    """
    用户基础 Schema

    【用途】
    作为其他用户 Schema 的基类，包含公共字段

    【继承关系】
    UserBase → UserCreate（创建用户）
    UserBase → User（响应数据）
    """
    username: str
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    """
    用户创建请求 Schema

    【继承】UserBase

    【额外字段】
    - password: 明文密码，后端会自动哈希存储

    【验证】
    - EmailStr 会自动验证邮箱格式
    - 如果 email 已存在会返回 400 错误

    【数据流向】
    客户端 → UserCreate → 后端哈希密码 → 存入数据库
    """
    password: str


class UserUpdate(BaseModel):
    """
    用户更新请求 Schema（管理员使用）

    【特点】
    所有字段都是 Optional，允许部分更新

    【使用场景】
    1. 修改用户邮箱
    2. 修改用户角色
    3. 重置用户密码
    4. 修改用户昵称或头像

    【验证逻辑】
    只有提供的字段会被更新，未提供的字段保持不变
    """
    email: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """
    用户个人资料更新 Schema（用户自己使用）

    【权限】
    普通用户只能修改自己的昵称和头像

    【限制】
    不包含 role 和 email 字段，用户不能自己修改角色和邮箱
    """
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class UserProfile(BaseModel):
    """
    用户资料响应 Schema

    【用途】
    返回当前登录用户的详细信息

    【字段说明】
    - id: 用户ID
    - username: 用户名
    - email: 邮箱地址
    - nickname: 昵称
    - avatar: 头像（Base64 编码）
    - role: 角色
    - created_at: 注册时间
    - last_login: 最后登录时间
    - is_verified: 是否已验证

    【ORM 转换】
    from_attributes = True 允许直接从 User ORM 模型转换
    """
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
        # 允许从 ORM 模型转换
        # 实现: User ORM 对象 → UserProfile Pydantic 对象
        from_attributes = True


class User(UserBase):
    """
    用户完整信息响应 Schema

    【用途】
    管理员获取用户列表时返回的用户信息

    【与 UserProfile 的区别】
    User 不包含 nickname 和 avatar，结构更简单
    """
    id: int
    created_at: Optional[datetime]
    last_login: Optional[datetime]
    is_verified: bool

    class Config:
        from_attributes = True


# =============================================================================
# 邮箱验证相关 Schema
# =============================================================================
class EmailSchema(BaseModel):
    """
    邮箱 Schema

    【字段说明】
    - email: 邮箱列表，支持批量发送

    【用途】
    发送验证码时使用
    """
    email: List[EmailStr]


class VerifyCodeRequest(BaseModel):
    """
    验证码验证请求 Schema

    【字段说明】
    - email: 要验证的邮箱
    - code: 用户输入的验证码

    【验证流程】
    1. 后端从缓存中获取该邮箱对应的验证码
    2. 检查验证码是否过期
    3. 对比用户输入是否正确
    """
    email: EmailStr
    code: str


# =============================================================================
# 文章相关 Schema
# =============================================================================
class ArticleBase(BaseModel):
    """
    文章基础 Schema

    【用途】
    作为其他文章 Schema 的基类
    """
    title: str
    content: str
    cover_image: Optional[str] = None


class ArticleCreate(ArticleBase):
    """
    文章创建请求 Schema

    【验证】
    - title: 必填，文章标题
    - content: 必填，文章正文

    【数据流向】
    客户端 → ArticleCreate → 存入数据库 → 返回 Article
    """
    pass


class ArticleUpdate(ArticleBase):
    """
    文章更新请求 Schema

    【特点】
    title 和 content 都是 Optional，允许多部分更新

    【使用场景】
    只更新标题、只更新内容、或同时更新
    """
    title: Optional[str] = None
    content: Optional[str] = None


class Article(ArticleBase):
    """
    文章响应 Schema

    【字段说明】
    - id: 文章ID
    - author_id: 作者ID
    - created_at: 创建时间
    - updated_at: 更新时间

    【ORM 转换】
    从 Article ORM 模型转换，包含所有字段
    """
    id: int
    author_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
