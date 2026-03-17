from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import schemas, models, database, auth
from response import success_response, created_response, error_response, ResponseCode
from datetime import timedelta, datetime
from typing import List
import io
import random
import string
from captcha.image import ImageCaptcha
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
import os

router = APIRouter()

# 存储验证码的简单内存缓存 (实际生产建议用 Redis)
captcha_store = {}
email_code_store = {} # 格式: {email: {"code": "123456", "expire": datetime, "verified": False}}

# 邮件配置 - 使用您提供的真实凭据
MAIL_USERNAME = "2669177036@qq.com" # 您的 QQ 邮箱
MAIL_PASSWORD = "evypfvbfoxtadjaa"  # 您的授权码
MAIL_FROM = "2669177036@qq.com"
MAIL_SERVER = "smtp.qq.com"

# 初始化 ConnectionConfig
# QQ 邮箱推荐使用 SSL (465)
mail_conf = ConnectionConfig(
    MAIL_USERNAME = MAIL_USERNAME,
    MAIL_PASSWORD = MAIL_PASSWORD,
    MAIL_FROM = MAIL_FROM,
    MAIL_PORT = 465, # 改为 465 SSL
    MAIL_SERVER = MAIL_SERVER,
    MAIL_STARTTLS = False, # SSL 模式下关闭 STARTTLS
    MAIL_SSL_TLS = True,   # 开启 SSL
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

@router.post("/send-email-code")
async def send_email_code(email_schema: schemas.EmailSchema, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    print(f"Received email code request for: {email_schema.email}") # Debug log
    
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
        # 暂时改为同步发送以便捕获错误 (调试用)
        await fm.send_message(message)
        print(f"Email sent successfully to {email}")
        return success_response(message="验证码已发送")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        # 回退到模拟模式，以便在邮件服务不可用时也能注册
        # 在生产环境中不应这样做，但在演示/开发环境中很有用
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
        # 后门逻辑保留
        if req.code == "888888":
             # 这里需要特殊处理：如果使用了后门码，我们需要在内存中伪造一个通过验证的记录，
             # 否则后续 register 接口检查 verified 状态时会失败
             email_code_store[req.email] = {
                 "code": "888888",
                 "expire": datetime.now() + timedelta(minutes=5),
                 "verified": True
             }
             return success_response(message="邮箱验证成功(后门)")
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
    # 生成 4 位随机验证码
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return success_response(message="请提供 key 查询参数")

@router.get("/captcha/{key}")
def get_captcha_img(key: str):
    # 调整验证码图片尺寸以适应显示
    image = ImageCaptcha(width=150, height=50, fonts=None)
    # 生成 4 位随机验证码
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    # 存入内存
    captcha_store[key] = code.lower()
    print(f"Generated CAPTCHA: {code} (stored as {code.lower()}) for key: {key}")
    print(f"Current captcha_store size: {len(captcha_store)}")
    
    # 生成图片
    data = image.generate(code)
    return StreamingResponse(data, media_type="image/png")

@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # 检查是否验证过邮箱 (只有提供了邮箱才检查)
    if user.email:
        record = email_code_store.get(user.email)
        # 必须验证通过
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
    
    # 验证码校验
    if captcha_key and captcha_code:
        stored_code = captcha_store.get(captcha_key)
        print(f"Stored captcha code: {stored_code} for key: {captcha_key}")
        
        if not stored_code:
            print(f"CAPTCHA key not found: {captcha_key}")
            raise HTTPException(status_code=400, detail="验证码已过期，请刷新后重试")
        
        if stored_code != captcha_code.lower():
            print(f"CAPTCHA mismatch: stored={stored_code}, input={captcha_code.lower()}")
            raise HTTPException(status_code=400, detail="验证码错误，请重新输入")
        
        # 验证成功后删除
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
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
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
    # 将头像二进制数据转换为 base64 字符串
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
    """获取当前用户的个人信息"""
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
    """更新当前用户的个人信息（昵称和头像）"""
    import base64
    
    print(f"Received profile update request: nickname={profile_update.nickname}, avatar_length={len(profile_update.avatar) if profile_update.avatar else 0}")
    
    # 更新昵称
    if profile_update.nickname is not None:
        # 昵称长度限制
        if len(profile_update.nickname) > 50:
            raise HTTPException(status_code=400, detail="昵称长度不能超过50个字符")
        current_user.nickname = profile_update.nickname
        print(f"Updated nickname to: {current_user.nickname}")
    
    # 更新头像
    if profile_update.avatar is not None and profile_update.avatar != "":
        try:
            # 将 base64 字符串解码为二进制数据
            avatar_data = base64.b64decode(profile_update.avatar)
            # 检查图片大小（限制为 5MB）
            if len(avatar_data) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="头像图片大小不能超过5MB")
            current_user.avatar = avatar_data
            print(f"Updated avatar, size: {len(avatar_data)} bytes")
        except Exception as e:
            print(f"Avatar decode error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"头像格式错误: {str(e)}")
    
    db.commit()
    db.refresh(current_user)
    print(f"Profile updated successfully for user: {current_user.username}")
    
    # 返回更新后的用户信息
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
            "role": current_user.role
        },
        message="个人信息更新成功"
    )

@router.get("/avatar/{user_id}")
def get_user_avatar(user_id: int, db: Session = Depends(database.get_db)):
    """获取用户头像图片"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not user.avatar:
        raise HTTPException(status_code=404, detail="用户未设置头像")
    
    # 返回图片二进制数据
    return StreamingResponse(io.BytesIO(user.avatar), media_type="image/jpeg")

# --- 管理员接口 ---

@router.get("/users", dependencies=[Depends(auth.get_current_admin_user)])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    username: str = None,
    db: Session = Depends(database.get_db)
):
    """获取用户列表，支持按用户名搜索"""
    import base64
    
    query = db.query(models.User)
    
    # 如果有搜索关键词，按用户名模糊搜索
    if username:
        query = query.filter(models.User.username.contains(username))
    
    users = query.offset(skip).limit(limit).all()
    user_list = []
    for u in users:
        avatar_base64 = None
        if u.avatar:
            avatar_base64 = base64.b64encode(u.avatar).decode('utf-8')
        
        user_list.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "nickname": u.nickname,
            "avatar": avatar_base64,
            "role": u.role,
            "is_verified": u.is_verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None
        })
    
    return success_response(data=user_list)

@router.post("/users", dependencies=[Depends(auth.get_current_admin_user)])
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已注册")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return created_response(
        data={
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "role": db_user.role
        },
        message="用户创建成功"
    )

@router.put("/users/{user_id}", dependencies=[Depends(auth.get_current_admin_user)])
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(database.get_db)):
    import base64
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user_update.email is not None and user_update.email != "":
        db_user.email = user_update.email
    if user_update.role is not None:
        db_user.role = user_update.role
    if user_update.password is not None:
        db_user.password_hash = auth.get_password_hash(user_update.password)
    if user_update.nickname is not None:
        db_user.nickname = user_update.nickname
    if user_update.avatar is not None:
        try:
            if user_update.avatar == "":
                db_user.avatar = None
            else:
                avatar_data = base64.b64decode(user_update.avatar)
                if len(avatar_data) > 5 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="头像图片大小不能超过5MB")
                db_user.avatar = avatar_data
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"头像格式错误: {str(e)}")
        
    db.commit()
    db.refresh(db_user)
    
    avatar_base64 = None
    if db_user.avatar:
        avatar_base64 = base64.b64encode(db_user.avatar).decode('utf-8')
    
    return success_response(
        data={
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "nickname": db_user.nickname,
            "avatar": avatar_base64,
            "role": db_user.role
        },
        message="用户更新成功"
    )

@router.delete("/users/{user_id}", dependencies=[Depends(auth.get_current_admin_user)])
def delete_user(user_id: int, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(db_user)
    db.commit()
    return success_response(message="用户删除成功")
