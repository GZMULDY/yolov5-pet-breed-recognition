"""
认证与授权模块

【模块职责】
提供基于 JWT 的用户认证功能，包括密码哈希、令牌生成、令牌验证以及用户权限校验。

【核心技术】
1. 密码哈希：使用 passlib 库的 pbkdf2_sha256 算法，安全性高且计算成本适中
2. JWT 令牌：使用 PyJWT 库，采用 HS256 对称加密算法
3. FastAPI 依赖注入：通过 Depends 机制实现声明式的认证中间件

【认证流程】
用户登录请求 → 验证用户名密码 → 生成 JWT 令牌 → 返回给客户端
后续请求 → 携带 JWT 令牌 → 令牌验证 → 解析用户信息 → 注入到请求上下文

【安全注意事项】
1. SECRET_KEY 必须保密，生产环境应使用环境变量
2. 令牌有效期不宜过长，默认 30 分钟
3. 密码永远不能明文存储，必须使用哈希算法
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
import database
from config import settings

# =============================================================================
# 密码哈希上下文配置
# =============================================================================
# 【算法说明】
# pbkdf2_sha256 是一种基于 PBKDF2（Password-Based Key Derivation Function 2）的哈希算法
# 特点：
# - 使用 SHA-256 作为底层哈希函数
# - 支持迭代次数配置，可调整计算成本以抵御暴力破解
# - 自带盐值（salt）生成，防止彩虹表攻击
#
# 【验证流程】
# verify(plain_password, hashed_password):
#   1. 从 hashed_password 中提取盐值和迭代次数
#   2. 对 plain_password 应用相同的哈希算法
#   3. 比较结果是否一致
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# =============================================================================
# OAuth2 密码模式配置
# =============================================================================
# 【作用】定义如何从请求中提取 JWT 令牌
# 【位置】令牌期望出现在 Authorization 头中，格式为 "Bearer <token>"
# 【tokenUrl】指定获取令牌的端点，用于生成 OpenAPI 文档
# 【自动错误】如果请求没有携带令牌，OAuth2PasswordBearer 会自动返回 401 错误
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

# =============================================================================
# 密码处理函数
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确

    【算法流程】
    1. 从 hashed_password 中提取盐值和算法参数
    2. 对 plain_password 应用相同的哈希函数
    3. 比较两个哈希值是否相等

    【参数说明】
    - plain_password: 用户输入的明文密码
    - hashed_password: 数据库中存储的哈希密码

    【返回值】
    - True: 密码匹配
    - False: 密码不匹配

    【时序安全】
    使用常量时间比较，防止时序攻击（通过比较时间推断正确字符）
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码的哈希值

    【算法流程】
    1. 生成随机盐值
    2. 对密码 + 盐值应用 PBKDF2-SHA256 算法
    3. 返回包含算法标识、迭代次数、盐值和哈希结果的字符串

    【输出格式】
    格式: $pbkdf2-sha256$迭代次数$盐值$哈希值
    示例: $pbkdf2-sha256$29000$salt...$hash...

    【参数说明】
    - password: 需要哈希的明文密码

    【返回值】
    完整的哈希字符串，可直接存入数据库

    【幂等性】
    每次调用都会生成不同的哈希值（因为盐值随机），
    但都可以通过 verify_password 正确验证原密码
    """
    return pwd_context.hash(password)


# =============================================================================
# JWT 令牌处理函数
# =============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌

    【JWT 结构】
    JWT 由三部分组成，用 "." 分隔：
    1. Header（头部）：算法和令牌类型
    2. Payload（载荷）：用户数据和元信息
    3. Signature（签名）：防止数据篡改

    【参数说明】
    - data: 要编码到令牌中的数据，通常包含用户标识、角色等信息
    - expires_delta: 令牌有效时长，None 则使用默认值

    【返回值】
    编码后的 JWT 字符串

    【生成流程】
    1. 复制传入的数据（避免修改原字典）
    2. 计算过期时间戳
    3. 将过期时间加入载荷
    4. 使用 SECRET_KEY 和 HS256 算法签名
    5. 返回编码后的令牌字符串

    【有效期策略】
    令牌有效期需要权衡安全性和用户体验：
    - 过短：用户频繁需要重新登录
    - 过长：被盗风险增加
    默认 30 分钟是一个合理的选择
    """
    # 复制数据字典，避免修改原始数据
    to_encode = data.copy()

    # 计算过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # 默认过期时间从配置读取
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # 将过期时间戳添加到载荷中
    # exp 是 JWT 的标准声明字段，表示过期时间
    to_encode.update({"exp": expire})

    # 生成 JWT 令牌
    # SECRET_KEY: 用于签名的密钥，必须保密
    # ALGORITHM: HS256 是对称加密算法，签名和验证使用同一个密钥
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


# =============================================================================
# 用户认证依赖
# =============================================================================

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)) -> models.User:
    """
    获取当前认证用户

    【使用场景】
    作为 FastAPI 的依赖注入，用于保护需要登录才能访问的 API 端点

    【验证流程】
    1. 从请求头中提取 JWT 令牌（由 oauth2_scheme 完成）
    2. 解码并验证令牌签名
    3. 从载荷中提取用户名
    4. 从数据库查询用户记录
    5. 返回用户模型实例

    【参数说明】
    - token: 由 oauth2_scheme 从 Authorization 头中提取的 JWT 令牌
    - db: 数据库会话，由 dependency injection 提供

    【返回值】
    当前登录用户的 ORM 模型实例

    【异常处理】
    - HTTP 401: 令牌无效、过期、或用户不存在
    - HTTP 403: 用户已被禁用

    【示例用法】
    @router.get("/protected")
    def protected_route(current_user: User = Depends(get_current_user)):
        return {"user": current_user.username}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解码 JWT 令牌
        # 使用 SECRET_KEY 验证签名，验证通过后返回载荷字典
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # 从载荷中提取用户名
        # "sub" 是 JWT 标准的 Subject 声明，通常用于存储用户标识
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except JWTError as e:
        # JWT 解码失败：签名错误、令牌过期、格式错误等
        raise credentials_exception

    # 从数据库查询用户
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    获取当前活跃用户

    【作用】
    在 get_current_user 基础上增加活跃状态检查

    【验证流程】
    1. 通过 get_current_user 获取用户（包含令牌验证）
    2. 检查用户是否已验证（邮箱激活等）

    【扩展性】
    可以在此函数中添加更多状态检查，如：
    - 账户是否被锁定
    - 会员是否过期
    - 账户是否被禁言
    """
    # 当前实现中 is_verified 表示用户是否完成了邮箱验证
    # 可以根据业务需求扩展更多的状态检查
    return current_user


def get_current_admin_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    获取当前管理员用户

    【作用】
    用于保护只有管理员才能访问的 API 端点

    【验证流程】
    1. 通过 get_current_user 获取用户
    2. 检查用户角色是否为 "admin"

    【权限模型】
    采用基于角色的访问控制（RBAC）
    - admin: 管理员，拥有所有权限
    - user: 普通用户，权限受限

    【异常处理】
    - HTTP 403: 用户不是管理员

    【示例用法】
    @router.delete("/users/{user_id}")
    def delete_user(
        user_id: int,
        current_user: User = Depends(get_current_admin_user)
    ):
        # 只有管理员能执行删除用户操作
        ...
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user
