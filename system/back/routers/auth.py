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

router = APIRouter()

# 存储验证码的简单内存缓存 (实际生产建议用 Redis)
captcha_store = {}
email_code_store = {} # 格式: {email: {"code": "123456", "expire": datetime, "verified": False}}

# 邮件配置 - 从 config 读取
mail_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

@router.post("/send-email-code")
async def send_email_code(email_schema: schemas.EmailSchema, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    print(f"Received email code request for: {email_schema.email}")

    email = email_schema.email[0]

    # 检查邮箱是否已被注册
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        print("Email already registered")
        raise HTTPException(status_code=400, detail="Email already registered")

    # 生成 6 位数字验证码
    code = ''.join(random.choices(string.digits, k=6))

    # 存储验证码 (5分钟有效)
    expire_time = datetime.now() + timedelta(minutes=5)
    email_code_store[email] = {
        "code": code,
        "expire": expire_time,
        "verified": False
    }

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
        print(f"Failed to send email: {str(e)}")
        print(f"=== FALLBACK DEBUG CODE for {email}: {code} ===")
        return success_response(
            message="验证码已生成(调试模式)",
            data={"debug_code": code}
        )

@router.post("/verify-email-code")
def verify_email_code(req: schemas.VerifyCodeRequest):
    print(f"Verifying code for {req.email}: {req.code}")
    record = email_code_store.get(req.email)

    if not record:
        raise HTTPException(status_code=400, detail="请先获取验证码")

    if datetime.now() > record["expire"]:
        del email_code_store[req.email]
        raise HTTPException(status_code=400, detail="验证码已过期")

    if record["code"] != req.code:
        raise HTTPException(status_code=400, detail="验证码错误")

    # 标记为已验证
    record["verified"] = True
    return success_response(message="邮箱验证成功")

@router.get("/captcha")
def get_captcha():
    return success_response(message="请提供 key 查询参数")

@router.get("/captcha/{key}")
def get_captcha_img(key: str):
    image = ImageCaptcha(width=150, height=50, fonts=None)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

    captcha_store[key] = code.lower()
    print(f"Generated CAPTCHA: {code} (stored as {code.lower()}) for key: {key}")
    print(f"Current captcha_store size: {len(captcha_store)}")

    data = image.generate(code)
    return StreamingResponse(data, media_type="image/png")

@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    if user.email:
        record = email_code_store.get(user.email)
        if not record or not record.get("verified"):
             raise HTTPException(status_code=400, detail="请先验证邮箱")

        del email_code_store[user.email]

    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已注册")

    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=schemas.UserRole.USER,
        is_verified=True if user.email else False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return created_response(data={
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role
    }, message="注册成功")

@router.post("/login")
def login(request: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    captcha_key = request.captcha_key
    captcha_code = request.captcha_code
    print(f"Login attempt: username={request.username}, captcha_key={captcha_key}, captcha_code={captcha_code}")

    if captcha_key and captcha_code:
        stored_code = captcha_store.get(captcha_key)
        print(f"Stored captcha code: {stored_code} for key: {captcha_key}")

        if not stored_code:
            print(f"CAPTCHA key not found: {captcha_key}")
            raise HTTPException(status_code=400, detail="验证码已过期，请刷新后重试")

        if stored_code != captcha_code.lower():
            print(f"CAPTCHA mismatch: stored={stored_code}, input={captcha_code.lower()}")
            raise HTTPException(status_code=400, detail="验证码错误，请重新输入")

        del captcha_store[captcha_key]
        print("CAPTCHA verified successfully")
    else:
        print("No CAPTCHA provided")

    user = db.query(models.User).filter(models.User.username == request.username).first()
    if not user or not auth.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.last_login = datetime.now()
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={
            "sub": user.username,
            "id": user.id,
            "role": user.role
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

@router.get("/me")
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
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

@router.put("/profile")
def update_user_profile(
    profile_update: schemas.UserProfileUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    data = UserService.update_profile(db, current_user, profile_update)
    return success_response(data=data, message="个人信息更新成功")

@router.get("/avatar/{user_id}")
def get_user_avatar(user_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not user.avatar:
        raise HTTPException(status_code=404, detail="用户未设置头像")

    return StreamingResponse(io.BytesIO(user.avatar), media_type="image/jpeg")

# --- 管理员接口 ---

@router.get("/users")
def read_users(
    skip: int = 0,
    limit: int = 100,
    username: str = None,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    return success_response(data=UserService.get_users(db, skip=skip, limit=limit, username=username))

@router.post("/users")
def create_user(
    user: schemas.UserCreate,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    data = UserService.create_user(db, user)
    return created_response(data=data, message="用户创建成功")

@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    data = UserService.update_user(db, user_id, user_update)
    return success_response(data=data, message="用户更新成功")

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    UserService.delete_user(db, user_id)
    return success_response(message="用户删除成功")
