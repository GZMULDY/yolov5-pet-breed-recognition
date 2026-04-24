from sqlalchemy.orm import Session
import models
from response import success_response, created_response, ResponseCode
from fastapi import HTTPException
import base64
import imghdr


class PetService:
    @staticmethod
    def get_categories(db: Session):
        categories = db.query(models.PetCategory).filter(models.PetCategory.parent_id == None).all()
        return [_build_category_tree(c) for c in categories]

    @staticmethod
    def get_category_by_id(db: Session, category_id: int):
        category = db.query(models.PetCategory).filter(models.PetCategory.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        return _build_category_tree(category)

    @staticmethod
    def get_breeds(db: Session, category_id: int = None, skip: int = 0, limit: int = 100):
        query = db.query(models.PetBreed)
        if category_id:
            query = query.filter(models.PetBreed.category_id == category_id)
        breeds = query.offset(skip).limit(limit).all()
        return [_format_breed(b) for b in breeds]

    @staticmethod
    def get_breed_by_id(db: Session, breed_id: int):
        breed = db.query(models.PetBreed).filter(models.PetBreed.id == breed_id).first()
        if not breed:
            raise HTTPException(status_code=404, detail="品种不存在")
        return _format_breed(breed)

    @staticmethod
    def get_breed_by_name(db: Session, name_en: str):
        breed = db.query(models.PetBreed).filter(models.PetBreed.name_en == name_en).first()
        if not breed:
            raise HTTPException(status_code=404, detail="品种不存在")
        return _format_breed(breed)

    @staticmethod
    def search_breeds(db: Session, keyword: str):
        breeds = db.query(models.PetBreed).filter(
            (models.PetBreed.name.contains(keyword)) |
            (models.PetBreed.name_en.contains(keyword))
        ).all()
        return [_format_breed(b) for b in breeds]


IMAGE_FORMAT_MIME_MAP = {
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
    'png': 'image/png'
}

def _format_breed(b: models.PetBreed) -> dict:
    image_base64 = None
    if b.image:
        image_format = imghdr.what(None, h=b.image)
        if image_format not in IMAGE_FORMAT_MIME_MAP:
            image_format = 'jpeg'
        mime_type = IMAGE_FORMAT_MIME_MAP.get(image_format, 'image/jpeg')
        encoded = base64.b64encode(b.image).decode('utf-8')
        image_base64 = f"data:{mime_type};base64,{encoded}"
    return {
        "id": b.id,
        "name": b.name,
        "name_en": b.name_en,
        "category_id": b.category_id,
        "image": image_base64,
        "description": b.description,
        "origin": b.origin,
        "personality": b.personality,
        "care_tips": b.care_tips,
        "diet_needs": b.diet_needs,
        "health_issues": b.health_issues,
        "exercise_needs": b.exercise_needs,
        "size": b.size,
        "lifespan": b.lifespan,
    }


def _build_category_tree(category: models.PetCategory) -> dict:
    result = {
        "id": category.id,
        "name": category.name,
        "name_en": category.name_en,
        "icon": category.icon,
        "sort_order": category.sort_order,
    }
    if category.children:
        result["children"] = [_build_category_tree(c) for c in category.children]
    return result
