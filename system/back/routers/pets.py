import base64
import imghdr
import io
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from jose import JWTError, jwt

import database
import models
from response import success_response, created_response, error_response, ResponseCode

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# 图片处理配置常量
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_FORMATS = {'jpeg', 'jpg', 'png'}
IMAGE_FORMAT_MIME_MAP = {
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
    'png': 'image/png'
}

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="未授权，请先登录")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="无效的认证方案")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role", "user")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的token")
        
        return {"username": username, "role": role}
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的授权头格式")
    except JWTError:
        raise HTTPException(status_code=401, detail="token已过期或无效")

def verify_admin(authorization: Optional[str] = Header(None)):
    user_info = verify_token(authorization)
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="权限不足，需要管理员权限")
    return user_info

def image_to_base64(image_bytes: bytes) -> Optional[str]:
    """将图片bytes转换为Base64编码字符串"""
    if not image_bytes:
        return None
    try:
        # 检测图片格式
        image_format = imghdr.what(None, h=image_bytes)
        if image_format not in IMAGE_FORMAT_MIME_MAP:
            image_format = 'jpeg'  # 默认使用jpeg
        
        mime_type = IMAGE_FORMAT_MIME_MAP.get(image_format, 'image/jpeg')
        encoded = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
    except Exception:
        return None


def validate_image(image_bytes: bytes) -> Tuple[bool, str, Optional[str]]:
    """
    验证图片数据
    
    Returns:
        Tuple[bool, str, Optional[str]]: (是否有效, 错误信息, 图片格式)
    """
    # 检查图片大小
    if len(image_bytes) > MAX_IMAGE_SIZE:
        size_mb = len(image_bytes) / (1024 * 1024)
        return False, f"图片大小超出限制，当前大小: {size_mb:.2f}MB，最大允许: {MAX_IMAGE_SIZE / (1024 * 1024):.0f}MB", None
    
    # 检查图片格式
    image_format = imghdr.what(None, h=image_bytes)
    if image_format is None:
        return False, "无法识别图片格式，请确保上传的是有效的图片文件", None
    
    if image_format not in ALLOWED_IMAGE_FORMATS:
        return False, f"不支持的图片格式: {image_format}，仅支持: {', '.join(sorted(ALLOWED_IMAGE_FORMATS))}", None
    
    return True, "", image_format


def base64_to_bytes(base64_str: str) -> Tuple[Optional[bytes], Optional[str]]:
    """
    将Base64字符串解码为bytes，并进行验证
    
    Args:
        base64_str: Base64编码的字符串，可以包含data URI scheme前缀
        
    Returns:
        Tuple[Optional[bytes], Optional[str]]: (解码后的bytes, 错误信息)
    """
    if not base64_str:
        return None, "Base64字符串为空"
    
    try:
        # 处理data URI scheme格式 (data:image/jpeg;base64,xxxxx)
        if ',' in base64_str:
            header, base64_data = base64_str.split(',', 1)
            # 可选：验证MIME类型
            if 'base64' not in header.lower():
                return None, "无效的Base64数据格式，缺少base64标识"
        else:
            base64_data = base64_str
        
        # 清理Base64字符串（移除空白字符）
        base64_data = base64_data.strip()
        
        # 验证Base64字符串格式
        if not base64_data:
            return None, "Base64数据为空"
        
        # 检查Base64字符串长度是否为4的倍数
        if len(base64_data) % 4 != 0:
            return None, "无效的Base64格式：字符串长度不正确"
        
        # 解码Base64
        try:
            image_bytes = base64.b64decode(base64_data, validate=True)
        except Exception as decode_error:
            return None, f"Base64解码失败: {str(decode_error)}"
        
        # 验证图片
        is_valid, error_msg, image_format = validate_image(image_bytes)
        if not is_valid:
            return None, error_msg
        
        return image_bytes, None
        
    except Exception as e:
        return None, f"图片处理失败: {str(e)}"


def get_compression_suggestion(image_bytes: bytes) -> Optional[str]:
    """
    如果图片过大，返回压缩建议
    """
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > 3:  # 超过3MB时给出建议
        return (
            f"当前图片大小为 {size_mb:.2f}MB，建议进行压缩处理：\n"
            "1. 使用图片压缩工具（如TinyPNG、Squoosh）压缩图片\n"
            "2. 降低图片分辨率（建议宽度不超过1920像素）\n"
            "3. 适当降低图片质量（JPEG质量建议80-90）\n"
            "4. 考虑使用WebP格式以获得更好的压缩率"
        )
    return None

class PetCategoryResponse(BaseModel):
    id: int
    name: str
    name_en: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    sort_order: int
    children: List["PetCategoryResponse"] = []

class PetBreedResponse(BaseModel):
    id: int
    name: str
    name_en: str
    category_id: int
    image: Optional[str] = None
    description: Optional[str] = None
    origin: Optional[str] = None
    personality: Optional[str] = None
    care_tips: Optional[str] = None
    diet_needs: Optional[str] = None
    health_issues: Optional[str] = None
    exercise_needs: Optional[str] = None
    size: Optional[str] = None
    lifespan: Optional[str] = None

class BreedUpdateRequest(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    category_id: Optional[int] = None
    image_base64: Optional[str] = None
    description: Optional[str] = None
    origin: Optional[str] = None
    personality: Optional[str] = None
    care_tips: Optional[str] = None
    diet_needs: Optional[str] = None
    health_issues: Optional[str] = None
    exercise_needs: Optional[str] = None
    size: Optional[str] = None
    lifespan: Optional[str] = None

def build_breed_response(breed: models.PetBreed) -> dict:
    return {
        "id": breed.id,
        "name": breed.name,
        "name_en": breed.name_en,
        "category_id": breed.category_id,
        "image": image_to_base64(breed.image),
        "description": breed.description,
        "origin": breed.origin,
        "personality": breed.personality,
        "care_tips": breed.care_tips,
        "diet_needs": breed.diet_needs,
        "health_issues": breed.health_issues,
        "exercise_needs": breed.exercise_needs,
        "size": breed.size,
        "lifespan": breed.lifespan
    }

@router.get("/categories")
def get_categories(current_user: dict = Depends(verify_token), db: Session = Depends(get_db)):
    categories = db.query(models.PetCategory).filter(
        models.PetCategory.parent_id == None
    ).order_by(models.PetCategory.sort_order).all()
    
    def build_tree(cat):
        return {
            "id": cat.id,
            "name": cat.name,
            "name_en": cat.name_en,
            "parent_id": cat.parent_id,
            "icon": cat.icon,
            "sort_order": cat.sort_order,
            "children": [build_tree(child) for child in cat.children]
        }
    
    return success_response(data=[build_tree(cat) for cat in categories])

@router.get("/categories/{category_id}/children")
def get_category_children(category_id: int, current_user: dict = Depends(verify_token), db: Session = Depends(get_db)):
    categories = db.query(models.PetCategory).filter(
        models.PetCategory.parent_id == category_id
    ).order_by(models.PetCategory.sort_order).all()
    
    def build_tree(cat):
        return {
            "id": cat.id,
            "name": cat.name,
            "name_en": cat.name_en,
            "parent_id": cat.parent_id,
            "icon": cat.icon,
            "sort_order": cat.sort_order,
            "children": [build_tree(child) for child in cat.children]
        }
    
    return success_response(data=[build_tree(cat) for cat in categories])

@router.get("/breeds")
def get_breeds(category_id: Optional[int] = None, current_user: dict = Depends(verify_token), db: Session = Depends(get_db)):
    query = db.query(models.PetBreed)
    if category_id:
        query = query.filter(models.PetBreed.category_id == category_id)
    breeds = query.all()
    return success_response(data=[build_breed_response(breed) for breed in breeds])

@router.get("/breeds/{breed_id}")
def get_breed(breed_id: int, current_user: dict = Depends(verify_token), db: Session = Depends(get_db)):
    breed = db.query(models.PetBreed).filter(models.PetBreed.id == breed_id).first()
    if not breed:
        raise HTTPException(status_code=404, detail="品种不存在")
    return success_response(data=build_breed_response(breed))

@router.get("/breeds/by-name/{name_en}")
def get_breed_by_name(name_en: str, db: Session = Depends(get_db)):
    breed = db.query(models.PetBreed).filter(
        models.PetBreed.name_en.ilike(name_en)
    ).first()
    if not breed:
        raise HTTPException(status_code=404, detail="品种不存在")
    return success_response(data=build_breed_response(breed))

@router.post("/categories")
def create_category(
    name: str,
    name_en: Optional[str] = None,
    parent_id: Optional[int] = None,
    icon: Optional[str] = None,
    db: Session = Depends(get_db)
):
    max_order = db.query(models.PetCategory).filter(
        models.PetCategory.parent_id == parent_id
    ).count()
    
    category = models.PetCategory(
        name=name,
        name_en=name_en,
        parent_id=parent_id,
        icon=icon,
        sort_order=max_order
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return created_response(
        data={
            "id": category.id,
            "name": category.name,
            "name_en": category.name_en,
            "parent_id": category.parent_id,
            "icon": category.icon,
            "sort_order": category.sort_order
        },
        message="分类创建成功"
    )

@router.post("/breeds")
def create_breed(
    name: str,
    name_en: str,
    category_id: int,
    image_base64: Optional[str] = None,
    description: Optional[str] = None,
    origin: Optional[str] = None,
    personality: Optional[str] = None,
    care_tips: Optional[str] = None,
    diet_needs: Optional[str] = None,
    health_issues: Optional[str] = None,
    exercise_needs: Optional[str] = None,
    size: Optional[str] = None,
    lifespan: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # 处理图片Base64数据
    image_bytes = None
    if image_base64:
        image_bytes, error_msg = base64_to_bytes(image_base64)
        if error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
    
    breed = models.PetBreed(
        name=name,
        name_en=name_en,
        category_id=category_id,
        image=image_bytes,
        description=description,
        origin=origin,
        personality=personality,
        care_tips=care_tips,
        diet_needs=diet_needs,
        health_issues=health_issues,
        exercise_needs=exercise_needs,
        size=size,
        lifespan=lifespan
    )
    db.add(breed)
    db.commit()
    db.refresh(breed)
    
    response = build_breed_response(breed)
    return created_response(data=response, message="品种创建成功")

@router.put("/breeds/{breed_id}")
def update_breed(
    breed_id: int,
    body: BreedUpdateRequest,
    current_user: dict = Depends(verify_admin),
    db: Session = Depends(get_db)
):
    breed = db.query(models.PetBreed).filter(models.PetBreed.id == breed_id).first()
    if not breed:
        raise HTTPException(status_code=404, detail="品种不存在")
    
    update_fields = {
        'name': body.name,
        'name_en': body.name_en,
        'category_id': body.category_id,
        'description': body.description,
        'origin': body.origin,
        'personality': body.personality,
        'care_tips': body.care_tips,
        'diet_needs': body.diet_needs,
        'health_issues': body.health_issues,
        'exercise_needs': body.exercise_needs,
        'size': body.size,
        'lifespan': body.lifespan
    }
    
    for field, value in update_fields.items():
        if value is not None:
            setattr(breed, field, value)
    
    # 处理图片更新
    if body.image_base64 is not None:
        if body.image_base64 == '':
            # 空字符串表示清除图片
            breed.image = None
        else:
            # 解码并验证图片
            image_bytes, error_msg = base64_to_bytes(body.image_base64)
            if error_msg:
                raise HTTPException(status_code=400, detail=error_msg)
            if image_bytes:
                breed.image = image_bytes
                
                compression_suggestion = get_compression_suggestion(image_bytes)
                if compression_suggestion:
                    logger.warning(f"Large image uploaded for breed {breed_id}: {compression_suggestion}")
    
    db.commit()
    db.refresh(breed)
    
    return success_response(data=build_breed_response(breed), message="品种更新成功")
