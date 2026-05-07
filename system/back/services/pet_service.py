"""
宠物品种服务层模块

【模块职责】
封装宠物分类和品种相关的业务逻辑，提供数据查询和管理服务。

【服务方法概览】
┌────────────────────────────────┬────────────────────────────────────┐
│             方法               │              功能                   │
├────────────────────────────────┼────────────────────────────────────┤
│ get_categories_by_parent       │ 获取指定父分类的子分类              │
│ get_category_tree              │ 获取完整分类树                      │
│ get_breeds                     │ 获取品种列表                        │
│ get_breed_by_id                │ 获取品种详情                        │
│ search_breeds                  │ 搜索品种                            │
│ create_breed                   │ 创建品种                            │
│ update_breed                   │ 更新品种信息                        │
│ delete_breed                   │ 删除品种                            │
│ create_category                │ 创建分类                            │
│ delete_category                │ 删除分类                            │
└────────────────────────────────┴────────────────────────────────────┘

【数据结构】
宠物分类采用树形结构：
PetCategory (分类表)
├── id: 主键
├── name: 分类名称
├── parent_id: 父分类ID（自引用外键）
└── children: 子分类列表 (ORM 关系)

PetBreed (品种表)
├── id: 主键
├── name: 品种名称
├── category_id: 所属分类ID
└── ... 其他品种详情字段
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import models
from response import success_response, created_response, ResponseCode
from fastapi import HTTPException
import base64


class PetService:
    """
    宠物服务类

    【设计模式】静态方法服务类
    不需要实例化，直接通过类调用静态方法

    【使用示例】
    breeds = PetService.get_breeds(db, category_id=1, skip=0, limit=20)
    """

    # =========================================================================
    # 分类相关服务
    # =========================================================================

    @staticmethod
    def get_categories_by_parent(
        db: Session,
        parent_id: Optional[int] = None
    ) -> List[dict]:
        """
        获取指定父分类下的直接子分类

        【功能】查询某个分类的直接子分类列表

        【参数】
        - db: 数据库会话
        - parent_id: 父分类ID
            - None: 获取顶级分类（parent_id 为 NULL）
            - 具体值: 获取该分类的直接子分类

        【算法流程】
        1. 构建基础查询
        2. 根据 parent_id 是否为 None 添加过滤条件
        3. 执行查询
        4. 格式化返回数据

        【返回格式】
        [
            {
                "id": 1,
                "name": "猫类",
                "name_en": "cats",
                "icon": "🐱",
                "parent_id": null
            },
            ...
        ]

        【SQL 示例】
        -- 获取顶级分类
        SELECT * FROM pet_categories WHERE parent_id IS NULL;

        -- 获取指定分类的子分类
        SELECT * FROM pet_categories WHERE parent_id = 1;
        """
        query = db.query(models.PetCategory)

        if parent_id is None:
            # 获取顶级分类：parent_id 为 NULL
            query = query.filter(models.PetCategory.parent_id.is_(None))
        else:
            # 获取指定父分类的子分类
            query = query.filter(models.PetCategory.parent_id == parent_id)

        # 按 sort_order 排序
        categories = query.order_by(models.PetCategory.sort_order).all()

        # 格式化返回
        return [
            {
                "id": cat.id,
                "name": cat.name,
                "name_en": cat.name_en,
                "icon": cat.icon,
                "parent_id": cat.parent_id
            }
            for cat in categories
        ]

    @staticmethod
    def get_category_tree(db: Session) -> List[dict]:
        """
        获取完整的分类树结构

        【功能】构建包含所有层级的分类树，用于前端树形组件

        【算法流程】
        1. 查询所有分类记录
        2. 构建 ID → 分类对象 的映射字典
        3. 遍历所有分类，建立父子关系
        4. 收集顶级分类（parent_id 为 NULL）
        5. 返回完整的树结构

        【递归结构】
        每个分类节点包含：
        - id, name, icon 等基本信息
        - children: 子分类列表（递归嵌套）

        【返回格式】
        [
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

        【时间复杂度】
        O(n)，n 为分类总数，使用字典映射避免递归查询

        【前端使用】
        - Element Plus Tree 组件
        - 导航菜单
        - 级联选择器
        """
        # -------------------------------------------------------------------------
        # 步骤1: 查询所有分类
        # -------------------------------------------------------------------------
        all_categories = db.query(models.PetCategory).order_by(
            models.PetCategory.sort_order
        ).all()

        # -------------------------------------------------------------------------
        # 步骤2: 构建映射字典和节点对象
        # -------------------------------------------------------------------------
        # id_to_category: {分类ID: 分类节点字典}
        id_to_category = {}
        for cat in all_categories:
            id_to_category[cat.id] = {
                "id": cat.id,
                "name": cat.name,
                "name_en": cat.name_en,
                "icon": cat.icon,
                "parent_id": cat.parent_id,
                "children": []  # 初始化空的子节点列表
            }

        # -------------------------------------------------------------------------
        # 步骤3: 建立父子关系
        # -------------------------------------------------------------------------
        root_nodes = []  # 顶级分类列表

        for cat_dict in id_to_category.values():
            parent_id = cat_dict["parent_id"]

            if parent_id is None:
                # 顶级分类，添加到根节点列表
                root_nodes.append(cat_dict)
            else:
                # 子分类，添加到父分类的 children 中
                parent = id_to_category.get(parent_id)
                if parent:
                    parent["children"].append(cat_dict)

        return root_nodes

    # =========================================================================
    # 品种相关服务
    # =========================================================================

    @staticmethod
    def get_breeds(
        db: Session,
        category_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple:
        """
        获取品种列表

        【功能】分页查询品种列表，可按分类过滤

        【参数】
        - db: 数据库会话
        - category_id: 分类ID（可选过滤器）
        - skip: 分页偏移
        - limit: 返回数量

        【返回】
        (品种列表, 总数)

        【算法流程】
        1. 构建基础查询
        2. 如果有分类过滤，添加条件
        3. 统计总数
        4. 分页查询
        5. 格式化数据
        """
        query = db.query(models.PetBreed)

        # 分类过滤
        if category_id:
            query = query.filter(models.PetBreed.category_id == category_id)

        # 统计总数
        total = query.count()

        # 分页查询
        breeds = query.offset(skip).limit(limit).all()

        # 格式化数据
        items = [_format_breed(breed) for breed in breeds]

        return items, total

    @staticmethod
    def get_breed_by_id(db: Session, breed_id: int) -> Optional[dict]:
        """
        获取品种详情

        【功能】查询指定品种的完整信息

        【参数】
        - db: 数据库会话
        - breed_id: 品种ID

        【返回】
        品种详情字典，不存在则返回 None

        【关联数据】
        通过 category 关系获取所属分类信息
        """
        breed = db.query(models.PetBreed).filter(
            models.PetBreed.id == breed_id
        ).first()

        if not breed:
            return None

        return _format_breed(breed, include_details=True)

    @staticmethod
    def get_breed_by_name_en(db: Session, name_en: str) -> Optional[dict]:
        """
        根据英文名精确查找品种

        【用途】AI 识别返回英文名后，查询对应的品种详细信息
        """
        breed = db.query(models.PetBreed).filter(
            models.PetBreed.name_en == name_en
        ).first()

        if not breed:
            return None

        return _format_breed(breed, include_details=True)

    @staticmethod
    def search_breeds(
        db: Session,
        keyword: str,
        limit: int = 10
    ) -> List[dict]:
        """
        搜索品种

        【功能】根据关键词模糊搜索品种名称

        【参数】
        - db: 数据库会话
        - keyword: 搜索关键词
        - limit: 返回数量限制

        【搜索逻辑】
        同时在中文名称和英文名称中搜索：
        WHERE name LIKE '%keyword%' OR name_en LIKE '%keyword%'

        【返回】
        匹配的品种简要信息列表
        """
        search_pattern = f"%{keyword}%"

        breeds = db.query(models.PetBreed).filter(
            (models.PetBreed.name.like(search_pattern)) |
            (models.PetBreed.name_en.like(search_pattern))
        ).limit(limit).all()

        return [
            {
                "id": breed.id,
                "name": breed.name,
                "name_en": breed.name_en,
                "category_id": breed.category_id
            }
            for breed in breeds
        ]

    @staticmethod
    def create_breed(db: Session, breed_data: dict) -> dict:
        """
        创建品种

        【功能】添加新的宠物品种

        【参数】
        - db: 数据库会话
        - breed_data: 品种数据字典

        【算法流程】
        1. 验证分类ID是否存在
        2. 创建品种 ORM 对象
        3. 保存到数据库
        4. 返回新品种信息
        """
        # 验证分类存在
        category_id = breed_data.get("category_id")
        if category_id:
            category = db.query(models.PetCategory).filter(
                models.PetCategory.id == category_id
            ).first()
            if not category:
                raise HTTPException(status_code=400, detail="分类不存在")

        # 创建品种
        breed = models.PetBreed(
            name=breed_data.get("name"),
            name_en=breed_data.get("name_en"),
            category_id=category_id,
            description=breed_data.get("description"),
            origin=breed_data.get("origin"),
            personality=breed_data.get("personality"),
            care_tips=breed_data.get("care_tips"),
            diet_needs=breed_data.get("diet_needs"),
            health_issues=breed_data.get("health_issues"),
            exercise_needs=breed_data.get("exercise_needs"),
            size=breed_data.get("size"),
            lifespan=breed_data.get("lifespan"),
            image=breed_data.get("image")
        )

        db.add(breed)
        db.commit()
        db.refresh(breed)

        return _format_breed(breed)

    @staticmethod
    def update_breed(db: Session, breed_id: int, breed_data: dict) -> Optional[dict]:
        """
        更新品种信息

        【功能】修改品种的详细信息

        【参数】
        - db: 数据库会话
        - breed_id: 品种ID
        - breed_data: 要更新的字段

        【部分更新】
        只更新提供的字段，未提供的字段保持不变
        """
        breed = db.query(models.PetBreed).filter(
            models.PetBreed.id == breed_id
        ).first()

        if not breed:
            return None

        # 更新提供的字段
        for field, value in breed_data.items():
            if hasattr(breed, field) and value is not None:
                setattr(breed, field, value)

        db.commit()
        db.refresh(breed)

        return _format_breed(breed)

    @staticmethod
    def delete_breed(db: Session, breed_id: int) -> None:
        """
        删除品种

        【功能】从数据库中删除品种
        """
        breed = db.query(models.PetBreed).filter(
            models.PetBreed.id == breed_id
        ).first()

        if not breed:
            raise HTTPException(status_code=404, detail="品种不存在")

        db.delete(breed)
        db.commit()

    @staticmethod
    def create_category(db: Session, category_data: dict) -> dict:
        """
        创建分类

        【功能】添加新的宠物分类
        """
        category = models.PetCategory(
            name=category_data.get("name"),
            name_en=category_data.get("name_en"),
            parent_id=category_data.get("parent_id"),
            icon=category_data.get("icon"),
            sort_order=category_data.get("sort_order", 0)
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        return {
            "id": category.id,
            "name": category.name,
            "name_en": category.name_en,
            "parent_id": category.parent_id,
            "icon": category.icon
        }

    @staticmethod
    def delete_category(db: Session, category_id: int) -> None:
        """
        删除分类

        【功能】删除分类及其所有子分类和品种

        【级联删除】
        由于配置了 cascade="all, delete-orphan"
        删除分类时会自动删除：
        - 所有子分类
        - 该分类下的所有品种
        """
        category = db.query(models.PetCategory).filter(
            models.PetCategory.id == category_id
        ).first()

        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        db.delete(category)
        db.commit()


# =============================================================================
# 辅助函数
# =============================================================================
def _format_breed(breed: models.PetBreed, include_details: bool = False) -> dict:
    """
    格式化品种数据

    【功能】将 ORM 对象转换为字典格式

    【参数】
    - breed: 品种 ORM 对象
    - include_details: 是否包含详细信息（用于详情页）

    【返回】
    品种数据字典
    """
    result = {
        "id": breed.id,
        "name": breed.name,
        "name_en": breed.name_en,
        "category_id": breed.category_id,
        "size": breed.size,
        "lifespan": breed.lifespan
    }

    # 添加详细信息
    if include_details:
        result.update({
            "description": breed.description,
            "origin": breed.origin,
            "personality": breed.personality,
            "care_tips": breed.care_tips,
            "diet_needs": breed.diet_needs,
            "health_issues": breed.health_issues,
            "exercise_needs": breed.exercise_needs
        })

    # 处理图片
    if breed.image:
        result["image"] = base64.b64encode(breed.image).decode('utf-8')

    return result
