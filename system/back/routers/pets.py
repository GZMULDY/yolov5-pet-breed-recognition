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

import database
import models
import auth
from response import success_response, created_response, error_response, ResponseCode
from services.pet_service import PetService

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {'jpeg', 'jpg', 'png'}
IMAGE_FORMAT_MIME_MAP = {
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
    'png': 'image/png'
}

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

def image_to_base64(image_bytes: bytes) -> Optional[str]:
    if not image_bytes:
        return None
    try:
        image_format = imghdr.what(None, h=image_bytes)
        if image_format not in IMAGE_FORMAT_MIME_MAP:
            image_format = 'jpeg'
        mime_type = IMAGE_FORMAT_MIME_MAP.get(image_format, 'image/jpeg')
        encoded = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
    except Exception:
        return None

def base64_to_bytes(base64_str: str) -> Tuple[Optional[bytes], Optional[str]]:
    if not base64_str:
        return None, "Base64字符串为空"
    try:
        if ',' in base64_str:
            header, base64_data = base64_str.split(',', 1)
            if 'base64' not in header.lower():
                return None, "无效的Base64数据格式，缺少base64标识"
        else:
            base64_data = base64_str

        base64_data = base64_data.strip()
        if not base64_data:
            return None, "Base64数据为空"

        try:
            image_bytes = base64.b64decode(base64_data, validate=True)
        except Exception as decode_error:
            return None, f"Base64解码失败: {str(decode_error)}"

        if len(image_bytes) > MAX_IMAGE_SIZE:
            return None, f"图片大小超出限制，最大允许: {MAX_IMAGE_SIZE // (1024*1024)}MB"

        image_format = imghdr.what(None, h=image_bytes)
        if image_format and image_format not in ALLOWED_IMAGE_FORMATS:
            return None, f"不支持的图片格式: {image_format}"

        return image_bytes, None

    except Exception as e:
        return None, f"图片处理失败: {str(e)}"

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
def get_categories(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return success_response(data=PetService.get_categories(db))

@router.get("/categories/{category_id}/children")
def get_category_children(category_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return success_response(data=PetService.get_category_by_id(db, category_id))

@router.get("/breeds")
def get_breeds(category_id: Optional[int] = None, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return success_response(data=PetService.get_breeds(db, category_id=category_id))

@router.get("/breeds/{breed_id}")
def get_breed(breed_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return success_response(data=PetService.get_breed_by_id(db, breed_id))

@router.get("/breeds/by-name/{name_en}")
def get_breed_by_name(name_en: str, db: Session = Depends(database.get_db)):
    return success_response(data=PetService.get_breed_by_name(db, name_en))

@router.post("/categories")
def create_category(
    name: str,
    name_en: Optional[str] = None,
    parent_id: Optional[int] = None,
    icon: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    max_order = db.query(models.PetCategory).filter(
        models.PetCategory.parent_id == parent_id
    ).count()
    category = models.PetCategory(
        name=name, name_en=name_en, parent_id=parent_id, icon=icon, sort_order=max_order
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return created_response(
        data={"id": category.id, "name": category.name, "name_en": category.name_en, "parent_id": category.parent_id, "icon": category.icon, "sort_order": category.sort_order},
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
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    image_bytes = None
    if image_base64:
        image_bytes, error_msg = base64_to_bytes(image_base64)
        if error_msg:
            raise HTTPException(status_code=400, detail=error_msg)

    breed = models.PetBreed(
        name=name, name_en=name_en, category_id=category_id, image=image_bytes,
        description=description, origin=origin, personality=personality,
        care_tips=care_tips, diet_needs=diet_needs, health_issues=health_issues,
        exercise_needs=exercise_needs, size=size, lifespan=lifespan
    )
    db.add(breed)
    db.commit()
    db.refresh(breed)
    return created_response(data=build_breed_response(breed), message="品种创建成功")

@router.put("/breeds/{breed_id}")
def update_breed(
    breed_id: int,
    body: BreedUpdateRequest,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    breed = db.query(models.PetBreed).filter(models.PetBreed.id == breed_id).first()
    if not breed:
        raise HTTPException(status_code=404, detail="品种不存在")

    update_fields = {
        'name': body.name, 'name_en': body.name_en, 'category_id': body.category_id,
        'description': body.description, 'origin': body.origin, 'personality': body.personality,
        'care_tips': body.care_tips, 'diet_needs': body.diet_needs, 'health_issues': body.health_issues,
        'exercise_needs': body.exercise_needs, 'size': body.size, 'lifespan': body.lifespan
    }

    for field, value in update_fields.items():
        if value is not None:
            setattr(breed, field, value)

    if body.image_base64 is not None:
        if body.image_base64 == '':
            breed.image = None
        else:
            image_bytes, error_msg = base64_to_bytes(body.image_base64)
            if error_msg:
                raise HTTPException(status_code=400, detail=error_msg)
            if image_bytes:
                breed.image = image_bytes

    db.commit()
    db.refresh(breed)
    return success_response(data=build_breed_response(breed), message="品种更新成功")
