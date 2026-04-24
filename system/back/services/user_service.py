from sqlalchemy.orm import Session
import models, schemas, auth
from response import success_response, created_response, ResponseCode
from fastapi import HTTPException, status
from datetime import datetime
import base64


class UserService:
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100, username: str = None):
        query = db.query(models.User)
        if username:
            query = query.filter(models.User.username.contains(username))
        users = query.offset(skip).limit(limit).all()
        return [_format_user(u) for u in users]

    @staticmethod
    def create_user(db: Session, user: schemas.UserCreate):
        if db.query(models.User).filter(models.User.username == user.username).first():
            raise HTTPException(status_code=400, detail="用户名已注册")
        db_user = models.User(
            username=user.username,
            email=user.email,
            password_hash=auth.get_password_hash(user.password),
            role=user.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"id": db_user.id, "username": db_user.username, "email": db_user.email, "role": db_user.role}

    @staticmethod
    def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
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
            if user_update.avatar == "":
                db_user.avatar = None
            else:
                avatar_data = base64.b64decode(user_update.avatar)
                if len(avatar_data) > 5 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="头像图片大小不能超过5MB")
                db_user.avatar = avatar_data

        db.commit()
        db.refresh(db_user)
        return _format_user(db_user)

    @staticmethod
    def delete_user(db: Session, user_id: int):
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        db.delete(db_user)
        db.commit()

    @staticmethod
    def update_profile(db: Session, current_user: models.User, profile_update: schemas.UserProfileUpdate):
        if profile_update.nickname is not None:
            if len(profile_update.nickname) > 50:
                raise HTTPException(status_code=400, detail="昵称长度不能超过50个字符")
            current_user.nickname = profile_update.nickname

        if profile_update.avatar is not None and profile_update.avatar != "":
            try:
                avatar_data = base64.b64decode(profile_update.avatar)
                if len(avatar_data) > 5 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="头像图片大小不能超过5MB")
                current_user.avatar = avatar_data
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"头像格式错误: {str(e)}")

        db.commit()
        db.refresh(current_user)
        return _format_user(current_user)


def _format_user(u: models.User) -> dict:
    avatar_base64 = None
    if u.avatar:
        avatar_base64 = base64.b64encode(u.avatar).decode('utf-8')
    return {
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "nickname": u.nickname,
        "avatar": avatar_base64,
        "role": u.role,
        "is_verified": u.is_verified,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "last_login": u.last_login.isoformat() if u.last_login else None
    }
