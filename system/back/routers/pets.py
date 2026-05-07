"""
宠物品种管理路由模块

【模块职责】
提供宠物分类和品种的查询、管理功能，支持层级分类浏览。

【API 端点概览】
┌────────────────────────┬────────┬────────────────────────────────┐
│        端点            │  方法  │            功能                 │
├────────────────────────┼────────┼────────────────────────────────┤
│ /pets/categories       │ GET    │ 获取分类树                      │
│ /pets/categories/tree  │ GET    │ 获取完整分类树结构              │
│ /pets/breeds           │ GET    │ 获取品种列表                    │
│ /pets/breeds/{id}      │ GET    │ 获取品种详情                    │
│ /pets/breeds/search    │ GET    │ 搜索品种                        │
│ /pets/breeds           │ POST   │ 创建品种（管理员）              │
│ /pets/breeds/{id}      │ PUT    │ 更新品种（管理员）              │
│ /pets/breeds/{id}      │ DELETE │ 删除品种（管理员）              │
└────────────────────────┴────────┴────────────────────────────────┘

【数据模型】
宠物数据采用三层分类结构：
┌─────────────────────────────────────────────────────────────────┐
│  PetCategory (分类)                                              │
│  ├── 猫类 (parent_id=NULL)                                       │
│  │   ├── 短毛猫 (parent_id=猫类.id)                              │
│  │   │   ├── 英国短毛猫 (parent_id=短毛猫.id)                    │
│  │   │   └── 东方短毛猫 (parent_id=短毛猫.id)                    │
│  │   └── 长毛猫 (parent_id=猫类.id)                              │
│  │       └── ...                                                 │
│  └── 狗类 (parent_id=NULL)                                       │
│      └── ...                                                     │
└─────────────────────────────────────────────────────────────────┘

PetBreed (品种)
- 属于某个最底层分类
- 包含品种详情：描述、产地、性格等
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import database
import models
import schemas
import auth
from response import success_response, created_response
from services.pet_service import PetService

# =============================================================================
# 路由器创建
# =============================================================================
router = APIRouter()


# =============================================================================
# 分类相关接口
# =============================================================================
@router.get("/pets/categories")
def get_categories(
    parent_id: Optional[int] = None,
    db: Session = Depends(database.get_db)
):
    """
    获取指定父分类下的子分类列表

    【功能】查询某个分类下的所有直接子分类

    【参数】
    - parent_id: 父分类ID
        - None: 返回顶级分类（猫类、狗类）
        - 具体ID: 返回该分类的直接子分类

    【返回示例】
    {
        "code": 200,
        "data": [
            {"id": 1, "name": "猫类", "icon": "🐱"},
            {"id": 8, "name": "狗类", "icon": "🐕"}
        ]
    }

    【数据流向】
    请求参数 → PetService.get_categories_by_parent → 数据库查询 → 返回结果
    """
    categories = PetService.get_categories_by_parent(db, parent_id)
    return success_response(data=categories)


@router.get("/pets/categories/tree")
def get_category_tree(db: Session = Depends(database.get_db)):
    """
    获取完整的分类树结构

    【功能】返回包含所有层级的分类树，用于前端树形组件

    【返回示例】
    {
        "code": 200,
        "data": [
            {
                "id": 1,
                "name": "猫类",
                "icon": "🐱",
                "children": [
                    {
                        "id": 2,
                        "name": "短毛猫",
                        "children": [...]
                    }
                ]
            }
        ]
    }

    【算法流程】
    1. 查询所有分类
    2. 构建 ID → 分类 的映射
    3. 遍历分类，建立父子关系
    4. 返回顶级分类列表

    【前端使用】
    用于树形选择器、导航菜单等组件
    """
    tree = PetService.get_category_tree(db)
    return success_response(data=tree)


# =============================================================================
# 品种相关接口
# =============================================================================
@router.get("/pets/breeds")
def get_breeds(
    category_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(database.get_db)
):
    """
    获取品种列表

    【功能】分页查询品种列表，可按分类过滤

    【参数】
    - category_id: 分类ID（可选）
        - None: 返回所有品种
        - 具体ID: 返回该分类下的品种
    - skip: 跳过记录数（分页偏移）
    - limit: 返回记录数

    【返回示例】
    {
        "code": 200,
        "data": {
            "items": [...],
            "total": 100
        }
    }

    【数据流向】
    请求参数 → PetService.get_breeds → 数据库分页查询 → 格式化返回
    """
    breeds, total = PetService.get_breeds(
        db,
        category_id=category_id,
        skip=skip,
        limit=limit
    )

    return success_response(
        data=breeds,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/pets/breeds/search")
def search_breeds(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    db: Session = Depends(database.get_db)
):
    """
    搜索品种

    【功能】根据关键词模糊搜索品种名称

    【参数】
    - keyword: 搜索关键词（中文名称或英文名称）
    - limit: 返回数量限制（1-50）

    【搜索逻辑】
    同时在中文名称和英文名称中搜索：
    WHERE name LIKE '%keyword%' OR name_en LIKE '%keyword%'

    【返回示例】
    {
        "code": 200,
        "data": [
            {"id": 1, "name": "英国短毛猫", "name_en": "british_shorthair"},
            {"id": 2, "name": "美国短毛猫", "name_en": "american_shorthair"}
        ]
    }

    【使用场景】
    搜索框自动补全、品种快速查找
    """
    breeds = PetService.search_breeds(db, keyword, limit)
    return success_response(data=breeds)


@router.get("/pets/breeds/by-name/{name_en}")
def get_breed_by_name_en(
    name_en: str,
    db: Session = Depends(database.get_db)
):
    """根据英文名获取品种详情（供 AI 识别结果查询）"""
    breed = PetService.get_breed_by_name_en(db, name_en)
    if not breed:
        raise HTTPException(status_code=404, detail="品种不存在")
    return success_response(data=breed)


@router.get("/pets/breeds/{breed_id}/image")
def get_breed_image(
    breed_id: int,
    db: Session = Depends(database.get_db)
):
    """获取品种图片"""
    breed = db.query(models.PetBreed).filter(models.PetBreed.id == breed_id).first()
    if not breed or not breed.image:
        raise HTTPException(status_code=404, detail="图片不存在")
    from fastapi.responses import Response
    return Response(content=breed.image, media_type="image/jpeg")


@router.get("/pets/breeds/{breed_id}")
def get_breed_detail(
    breed_id: int,
    db: Session = Depends(database.get_db)
):
    """
    获取品种详情

    【功能】查询指定品种的完整信息

    【参数】
    - breed_id: 品种ID

    【返回示例】
    {
        "code": 200,
        "data": {
            "id": 1,
            "name": "英国短毛猫",
            "name_en": "british_shorthair",
            "description": "...",
            "origin": "英国",
            "personality": "温顺安静...",
            "care_tips": "...",
            "diet_needs": "...",
            "health_issues": "...",
            "size": "中型到大型",
            "lifespan": "12-17年",
            "image": "base64..."
        }
    }

    【错误情况】
    - 404: 品种不存在

    【数据流向】
    breed_id → PetService.get_breed_by_id → 数据库查询 → 返回详情
    """
    breed = PetService.get_breed_by_id(db, breed_id)

    if not breed:
        raise HTTPException(status_code=404, detail="品种不存在")

    return success_response(data=breed)


# =============================================================================
# 管理员接口 - 品种管理
# =============================================================================
@router.post("/pets/breeds")
def create_breed(
    breed_data: dict = Body(...),
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    创建品种（管理员）

    【功能】添加新的宠物品种

    【权限】管理员

    【请求体】
    {
        "name": "新品种名称",
        "name_en": "english_name",
        "category_id": 1,
        "description": "品种描述",
        "origin": "原产地",
        "personality": "性格特点",
        "care_tips": "饲养建议",
        "diet_needs": "饮食需求",
        "health_issues": "健康问题",
        "size": "体型",
        "lifespan": "寿命",
        "image": "base64..."
    }

    【处理流程】
    1. 验证请求者权限（管理员）
    2. 验证分类ID是否存在
    3. 处理图片 Base64 解码
    4. 创建品种记录
    5. 返回新品种信息
    """
    # 处理图片数据（前端发送 image_base64 或 image 字段）
    image_data = breed_data.get("image_base64") or breed_data.get("image")
    if image_data:
        import base64
        breed_data["image"] = base64.b64decode(image_data)

    breed = PetService.create_breed(db, breed_data)
    return created_response(data=breed, message="品种创建成功")


@router.put("/pets/breeds/{breed_id}")
def update_breed(
    breed_id: int,
    breed_data: dict = Body(...),
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    更新品种信息（管理员）

    【功能】修改品种的详细信息

    【权限】管理员

    【参数】
    - breed_id: 品种ID

    【请求体】
    只需包含要更新的字段：
    {
        "description": "新的描述",
        "care_tips": "新的饲养建议"
    }
    """
    # 处理图片数据（前端发送 image_base64 或 image 字段）
    image_data = breed_data.get("image_base64") or breed_data.get("image")
    if image_data:
        import base64
        breed_data["image"] = base64.b64decode(image_data)
        breed_data.pop("image_base64", None)

    breed = PetService.update_breed(db, breed_id, breed_data)

    if not breed:
        raise HTTPException(status_code=404, detail="品种不存在")

    return success_response(data=breed, message="品种更新成功")


@router.delete("/pets/breeds/{breed_id}")
def delete_breed(
    breed_id: int,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    删除品种（管理员）

    【功能】删除指定品种

    【权限】管理员

    【参数】
    - breed_id: 品种ID

    【错误情况】
    - 404: 品种不存在
    """
    PetService.delete_breed(db, breed_id)
    return success_response(message="品种删除成功")


# =============================================================================
# 分类管理接口（管理员）
# =============================================================================
@router.post("/pets/categories")
def create_category(
    category_data: dict = Body(...),
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    创建分类（管理员）

    【功能】添加新的宠物分类

    【权限】管理员

    【请求体】
    {
        "name": "分类名称",
        "name_en": "english_name",
        "parent_id": 1,     // 可选，父分类ID
        "icon": "🐱"        // 可选，图标
    }
    """
    category = PetService.create_category(db, category_data)
    return created_response(data=category, message="分类创建成功")


@router.delete("/pets/categories/{category_id}")
def delete_category(
    category_id: int,
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    """
    删除分类（管理员）

    【功能】删除指定分类

    【权限】管理员

    【注意】
    - 删除分类会级联删除其下所有子分类和品种
    - 操作不可逆
    """
    PetService.delete_category(db, category_id)
    return success_response(message="分类删除成功")



