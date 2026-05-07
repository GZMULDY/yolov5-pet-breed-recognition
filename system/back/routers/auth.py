"""
用户认证路由模块

【模块职责】
处理用户认证相关的 HTTP 请求，包括登录、注册、验证码、用户管理等功能。

【API 端点概览】
┌────────────────────────┬────────┬────────────────────────────────┐
│        端点            │  方法  │            功能                 │
├────────────────────────┼────────┼────────────────────────────────┤
│ /send-email-code       │ POST   │ 发送邮箱验证码                  │
│ /verify-email-code     │ POST   │ 验证邮箱验证码                  │
│ /captcha               │ GET    │ 验证码提示                      │
│ /captcha/{key}         │ GET    │ 生成图形验证码                  │
│ /register              │ POST   │ 用户注册                        │
│ /login                 │ POST   │ 用户登录                        │
│ /me                    │ GET    │ 获取当前用户信息                │
│ /profile               │ GET    │ 获取用户资料                    │
│ /profile               │ PUT    │ 更新用户资料                    │
│ /avatar/{user_id}      │ GET    │ 获取用户头像                    │
│ /users                 │ GET    │ 获取用户列表（管理员）          │
│ /users                 │ POST   │ 创建用户（管理员）              │
│ /users/{user_id}       │ PUT    │ 更新用户（管理员）              │
│ /users/{user_id}       │ DELETE │ 删除用户（管理员）              │
└────────────────────────┴────────┴────────────────────────────────┘

【认证流程】
1. 图形验证码流程：前端获取 key → 请求验证码图片 → 用户输入 → 登录时验证
2. 邮箱验证流程：请求验证码 → 发送邮件 → 用户输入 → 验证 → 注册
3. 登录流程：验证码校验 → 账号密码校验 → 生成 JWT → 返回令牌
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import schemas, models, database, auth
from response import success_response, created_response, error_response, ResponseCode
from services.user_service import UserService
from datetime import timedelta, datetime
from typing import List
import io
import random
import string
from captcha.image import ImageCaptcha
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from config import settings

# =============================================================================
# 路由器创建
# =============================================================================
# 创建 APIRouter 实例，用于注册路由
# 在 main.py 中通过 include_router 挂载到 /api/v1 前缀
router = APIRouter()

# =============================================================================
# 内存缓存（验证码存储）
# =============================================================================
# 【警告】生产环境建议使用 Redis 替代内存存储
# 【原因】
# 1. 内存存储在多实例部署时无法共享
# 2. 服务重启后数据丢失
# 3. 缺少过期自动清理机制

# 存储图形验证码：{key: code}
# key: 前端生成的唯一标识
# code: 4位字母数字验证码（小写）
captcha_store = {}

# 存储邮箱验证码：{email: {"code": "123456", "expire": datetime, "verified": False}}
# code: 6位数字验证码
# expire: 过期时间
# verified: 是否已验证
email_code_store = {}

# =============================================================================
# 邮件服务配置
# =============================================================================
# 创建邮件连接配置，用于发送验证码邮件
mail_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,      # 发件人邮箱
    MAIL_PASSWORD=settings.MAIL_PASSWORD,      # 邮箱授权码
    MAIL_FROM=settings.MAIL_FROM,              # 发件人显示地址
    MAIL_PORT=settings.MAIL_PORT,              # SMTP 端口
    MAIL_SERVER=settings.MAIL_SERVER,          # SMTP 服务器
    MAIL_STARTTLS=settings.MAIL_STARTTLS,      # STARTTLS 加密
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,        # SSL/TLS 加密
    USE_CREDENTIALS=True,                      # 使用认证
    VALIDATE_CERTS=True                        # 验证证书
)


# =============================================================================
# 邮箱验证码相关接口
# =============================================================================
@router.post("/send-email-code")
async def send_email_code(
    email_schema: schemas.EmailSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db)
):
    """
    发送邮箱验证码

    【功能】向指定邮箱发送 6 位数字验证码，用于注册验证

    【请求体】
    {
        "email": ["user@example.com"]
    }

    【处理流程】
    1. 检查邮箱是否已被注册
    2. 生成 6 位随机数字验证码
    3. 存储验证码到内存（5分钟有效期）
    4. 异步发送邮件
    5. 返回成功响应

    【参数说明】
    - email_schema: 包含邮箱列表的请求体
    - background_tasks: FastAPI 后台任务，用于异步发送邮件
    - db: 数据库会话

    【错误情况】
    - 400: 邮箱已被注册

    【安全措施】
    - 验证码 5 分钟后过期
    - 验证码使用后立即删除
    """
    print(f"Received email code request for: {email_schema.email}")

    # 获取第一个邮箱地址（支持批量发送但实际只取第一个）
    email = email_schema.email[0]

    # -------------------------------------------------------------------------
    # 检查邮箱是否已被注册
    # -------------------------------------------------------------------------
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        print("Email already registered")
        raise HTTPException(status_code=400, detail="Email already registered")

    # -------------------------------------------------------------------------
    # 生成并存储验证码
    # -------------------------------------------------------------------------
    # 生成 6 位纯数字验证码
    code = ''.join(random.choices(string.digits, k=6))

    # 计算过期时间：当前时间 + 5 分钟
    expire_time = datetime.now() + timedelta(minutes=5)

    # 存储到内存缓存
    email_code_store[email] = {
        "code": code,
        "expire": expire_time,
        "verified": False    # 初始未验证
    }

    # -------------------------------------------------------------------------
    # 构建并发送邮件
    # -------------------------------------------------------------------------
    message = MessageSchema(
        subject="[YOLO System] 注册验证码",
        recipients=[email],
        body=f"您的注册验证码是：{code}，有效期 5 分钟。请勿泄露给他人。",
        subtype=MessageType.html
    )

    fm = FastMail(mail_conf)

    try:
        await fm.send_message(message)
        print(f"Email sent successfully to {email}")
        return success_response(message="验证码已发送")
    except Exception as e:
        # 发送失败时返回调试信息（生产环境应移除）
        print(f"Failed to send email: {str(e)}")
        print(f"=== FALLBACK DEBUG CODE for {email}: {code} ===")
        return success_response(
            message="验证码已生成(调试模式)",
            data={"debug_code": code}
        )


@router.post("/verify-email-code")
def verify_email_code(req: schemas.VerifyCodeRequest):
    """
    验证邮箱验证码

    【功能】验证用户输入的验证码是否正确

    【请求体】
    {
        "email": "user@example.com",
        "code": "123456"
    }

    【处理流程】
    1. 从缓存获取该邮箱的验证码记录
    2. 检查验证码是否存在
    3. 检查验证码是否过期
    4. 对比验证码是否正确
    5. 标记为已验证

    【错误情况】
    - 400: 请先获取验证码（缓存中没有记录）
    - 400: 验证码已过期
    - 400: 验证码错误
    """
    print(f"Verifying code for {req.email}: {req.code}")
    record = email_code_store.get(req.email)

    # 验证码不存在
    if not record:
        raise HTTPException(status_code=400, detail="请先获取验证码")

    # 验证码已过期
    if datetime.now() > record["expire"]:
        del email_code_store[req.email]  # 清理过期记录
        raise HTTPException(status_code=400, detail="验证码已过期")

    # 验证码不匹配
    if record["code"] != req.code:
        raise HTTPException(status_code=400, detail="验证码错误")

    # 标记为已验证，允许注册
    record["verified"] = True
    return success_response(message="邮箱验证成功")


# =============================================================================
# 图形验证码相关接口
# =============================================================================
@router.get("/captcha")
def get_captcha():
    """
    验证码入口提示

    【说明】不带 key 参数的请求，返回提示信息
    实际使用时应带上 key 参数：/captcha/{key}
    """
    return success_response(message="请提供 key 查询参数")


@router.get("/captcha/{key}")
def get_captcha_img(key: str):
    """
    生成图形验证码

    【功能】生成并返回图形验证码图片

    【参数】
    - key: 验证码唯一标识，由前端生成（如 UUID）

    【处理流程】
    1. 创建验证码生成器（150x50 像素）
    2. 生成 4 位字母数字验证码
    3. 存储验证码（key -> code 映射）
    4. 生成 PNG 图片流
    5. 返回图片响应

    【返回内容】
    Content-Type: image/png
    图片内容：包含扭曲文字的验证码图片

    【前端使用】
    <img src="/api/v1/captcha/uuid-xxx" />

    【安全措施】
    - 验证码存储为小写，比对时忽略大小写
    - 每次请求生成新验证码，旧的被覆盖
    """
    # 创建验证码图片生成器
    image = ImageCaptcha(width=150, height=50, fonts=None)

    # 生成 4 位验证码（大写字母 + 数字）
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

    # 存储验证码（转为小写，便于比对）
    captcha_store[key] = code.lower()
    print(f"Generated CAPTCHA: {code} (stored as {code.lower()}) for key: {key}")
    print(f"Current captcha_store size: {len(captcha_store)}")

    # 生成图片数据流
    data = image.generate(code)

    # 返回 PNG 图片流
    return StreamingResponse(data, media_type="image/png")


# =============================================================================
# 用户注册接口
# =============================================================================
@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """
    用户注册

    【功能】创建新用户账户

    【请求体】
    {
        "username": "test",
        "password": "123456",
        "email": "test@example.com"  // 可选
    }

    【处理流程】
    1. 如果提供了邮箱，检查是否已验证
    2. 检查用户名是否已存在
    3. 对密码进行哈希处理
    4. 创建新用户记录
    5. 返回用户信息

    【验证规则】
    - 邮箱注册：必须先验证邮箱验证码
    - 用户名：唯一，不能重复
    - 密码：会被哈希存储，不明文保存

    【错误情况】
    - 400: 请先验证邮箱
    - 400: 用户名已注册
    """
    # -------------------------------------------------------------------------
    # 邮箱验证检查
    # -------------------------------------------------------------------------
    if user.email:
        record = email_code_store.get(user.email)
        if not record or not record.get("verified"):
            raise HTTPException(status_code=400, detail="请先验证邮箱")

        # 删除已使用的验证码记录
        del email_code_store[user.email]

    # -------------------------------------------------------------------------
    # 用户名唯一性检查
    # -------------------------------------------------------------------------
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已注册")

    # -------------------------------------------------------------------------
    # 创建新用户
    # -------------------------------------------------------------------------
    # 对密码进行哈希处理
    hashed_password = auth.get_password_hash(user.password)

    # 创建用户 ORM 对象
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=schemas.UserRole.USER,           # 新注册用户默认为普通用户
        is_verified=True if user.email else False  # 邮箱注册则已验证
    )

    # 保存到数据库
    db.add(db_user)
    db.commit()
    db.refresh(db_user)  # 刷新以获取自增 ID

    return created_response(
        data={
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "role": db_user.role
        },
        message="注册成功"
    )


# =============================================================================
# 用户登录接口
# =============================================================================
@router.post("/login")
def login(request: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    """
    用户登录

    【功能】验证用户身份并返回 JWT 令牌

    【请求体】
    {
        "username": "admin",
        "password": "admin",
        "captcha_key": "uuid-xxx",     // 可选
        "captcha_code": "AB12"         // 可选
    }

    【处理流程】
    1. 如果提供了验证码，进行验证码校验
    2. 查询用户记录
    3. 验证密码
    4. 更新最后登录时间
    5. 生成 JWT 令牌
    6. 返回令牌和用户信息

    【错误情况】
    - 400: 验证码已过期/错误
    - 401: 用户名或密码错误

    【返回数据】
    {
        "access_token": "eyJ0eXAi...",
        "token_type": "bearer",
        "role": "admin",
        "username": "admin",
        "id": 1
    }
    """
    captcha_key = request.captcha_key
    captcha_code = request.captcha_code
    print(f"Login attempt: username={request.username}, captcha_key={captcha_key}, captcha_code={captcha_code}")

    # -------------------------------------------------------------------------
    # 验证码校验（可选）
    # -------------------------------------------------------------------------
    if captcha_key and captcha_code:
        stored_code = captcha_store.get(captcha_key)
        print(f"Stored captcha code: {stored_code} for key: {captcha_key}")

        # 验证码不存在（可能已过期或 key 错误）
        if not stored_code:
            print(f"CAPTCHA key not found: {captcha_key}")
            raise HTTPException(status_code=400, detail="验证码已过期，请刷新后重试")

        # 验证码不匹配（忽略大小写）
        if stored_code != captcha_code.lower():
            print(f"CAPTCHA mismatch: stored={stored_code}, input={captcha_code.lower()}")
            raise HTTPException(status_code=400, detail="验证码错误，请重新输入")

        # 验证通过，删除验证码（一次性使用）
        del captcha_store[captcha_key]
        print("CAPTCHA verified successfully")
    else:
        print("No CAPTCHA provided")

    # -------------------------------------------------------------------------
    # 用户身份验证
    # -------------------------------------------------------------------------
    # 查询用户
    user = db.query(models.User).filter(models.User.username == request.username).first()

    # 验证用户存在且密码正确
    if not user or not auth.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # -------------------------------------------------------------------------
    # 更新登录时间
    # -------------------------------------------------------------------------
    user.last_login = datetime.now()
    db.commit()

    # -------------------------------------------------------------------------
    # 生成 JWT 令牌
    # -------------------------------------------------------------------------
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={
            "sub": user.username,    # Subject: 用户标识
            "id": user.id,           # 用户 ID
            "role": user.role        # 用户角色
        },
        expires_delta=access_token_expires
    )

    return success_response(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.role,
            "username": user.username,
            "id": user.id
        },
        message="登录成功"
    )


# =============================================================================
# 用户信息获取接口
# =============================================================================
@router.get("/me")
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """
    获取当前登录用户信息

    【功能】返回当前登录用户的详细信息

    【认证】需要 JWT 令牌

    【返回数据】
    {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "nickname": "管理员",
        "avatar": "base64...",
        "role": "admin",
        "is_verified": true,
        "created_at": "2024-01-01T00:00:00",
        "last_login": "2024-01-15T10:30:00"
    }
    """
    # 处理头像 Base64 编码
    avatar_base64 = None
    if current_user.avatar:
        import base64
        avatar_base64 = base64.b64encode(current_user.avatar).decode('utf-8')

    return success_response(
        data={
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "nickname": current_user.nickname,
            "avatar": avatar_base64,
            "role": current_user.role,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        },
        message="success"
    )


@router.get("/profile")
def get_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    """
    获取用户个人资料

    【功能】获取当前用户的个人资料（与 /me 类似，用于 profile 页面）

    【认证】需要 JWT 令牌
    """
    import base64

    avatar_base64 = None
    if current_user.avatar:
        avatar_base64 = base64.b64encode(current_user.avatar).decode('utf-8')

    return success_response(
        data={
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "nickname": current_user.nickname,
            "avatar": avatar_base64,
            "role": current_user.role,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        },
        message="获取用户信息成功"
    )


# =============================================================================
# 用户资料更新接口
# =============================================================================
@router.put("/profile")
def update_user_profile(
    profile_update: schemas.UserProfileUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    更新用户个人资料

    【功能】用户更新自己的资料（昵称、头像）

    【请求体】
    {
        "nickname": "新昵称",
        "avatar": "base64..."
    }

    【权限】只能修改自己的资料

    【处理】
    - nickname: 直接更新
    - avatar: Base64 解码后存储为二进制
    """
    data = UserService.update_profile(db, current_user, profile_update)
    return success_response(data=data, message="个人信息更新成功")


@router.get("/avatar/{user_id}")
def get_user_avatar(user_id: int, db: Session = Depends(database.get_db)):
    """
    获取用户头像

    【功能】返回用户的头像图片

    【参数】
    - user_id: 用户 ID

    【返回】
    - Content-Type: image/jpeg
    - 图片二进制数据

    【错误情况】
    - 404: 用户不存在
    - 404: 用户未设置头像
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not user.avatar:
        raise HTTPException(status_code=404, detail="用户未设置头像")

    return StreamingResponse(io.BytesIO(user.avatar), media_type="image/jpeg")


# =============================================================================
# 管理员接口 - 用户管理
# =============================================================================
@router.get("/users")
def read_users(
    skip: int = 0,
    limit: int = 100,
    username: str = None,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    获取用户列表（管理员）

    【功能】分页查询用户列表，支持用户名搜索

    【权限】管理员

    【参数】
    - skip: 跳过记录数（分页偏移）
    - limit: 返回记录数
    - username: 用户名过滤（模糊匹配）
    """
    return success_response(
        data=UserService.get_users(db, skip=skip, limit=limit, username=username)
    )


@router.post("/users")
def create_user(
    user: schemas.UserCreate,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    创建用户（管理员）

    【功能】管理员创建新用户

    【权限】管理员

    【请求体】
    {
        "username": "newuser",
        "password": "123456",
        "email": "newuser@example.com",
        "role": "user"  // 可选，默认 user
    }
    """
    data = UserService.create_user(db, user)
    return created_response(data=data, message="用户创建成功")


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    更新用户信息（管理员）

    【功能】管理员更新任意用户的信息

    【权限】管理员

    【参数】
    - user_id: 要更新的用户 ID

    【可更新字段】
    - email: 邮箱
    - role: 角色
    - password: 密码
    - nickname: 昵称
    - avatar: 头像
    """
    data = UserService.update_user(db, user_id, user_update)
    return success_response(data=data, message="用户更新成功")


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    删除用户（管理员）

    【功能】管理员删除用户

    【权限】管理员

    【参数】
    - user_id: 要删除的用户 ID

    【注意】
    - 删除用户会级联删除该用户的所有文章
    - 不能删除自己
    """
    UserService.delete_user(db, user_id)
    return success_response(message="用户删除成功")
