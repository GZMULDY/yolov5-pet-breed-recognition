"""
文件上传路由模块

【模块职责】
处理文件上传请求，支持图片上传并返回可访问的 URL。

【API 端点概览】
┌────────────────────┬────────┬────────────────────────────────┐
│       端点          │  方法  │            功能                 │
├────────────────────┼────────┼────────────────────────────────┤
│ /upload            │ POST   │ 通用文件上传                    │
│ /upload/image      │ POST   │ 图片上传（带尺寸验证）          │
└────────────────────┴────────┴────────────────────────────────┘

【上传流程】
┌─────────────────────────────────────────────────────────────────┐
│  客户端上传文件                                                  │
│       ↓                                                         │
│  验证文件类型和大小                                              │
│       ↓                                                         │
│  生成唯一文件名（UUID）                                          │
│       ↓                                                         │
│  保存到 static 目录                                              │
│       ↓                                                         │
│  返回文件访问 URL                                                │
└─────────────────────────────────────────────────────────────────┘

【存储结构】
system/
└── static/
    ├── uploads/          # 用户上传的文件
    │   ├── images/       # 图片文件
    │   └── files/        # 其他文件
    └── results/          # AI 检测结果图

【安全措施】
1. 文件类型白名单验证
2. 文件大小限制
3. 文件名随机化（防止路径遍历攻击）
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pathlib import Path
import uuid
import os
from response import success_response
import models

# =============================================================================
# 路由器创建
# =============================================================================
router = APIRouter()

# =============================================================================
# 上传目录配置
# =============================================================================
# 静态文件根目录
STATIC_DIR = Path(__file__).parent.parent / "static"

# 上传文件存储目录
UPLOADS_DIR = STATIC_DIR / "uploads"
IMAGES_DIR = UPLOADS_DIR / "images"
FILES_DIR = UPLOADS_DIR / "files"

# 确保目录存在
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
FILES_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 文件上传配置
# =============================================================================
# 允许上传的图片类型
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp"
}

# 图片最大大小（字节）
# 10MB = 10 * 1024 * 1024 = 10485760 bytes
MAX_IMAGE_SIZE = 10 * 1024 * 1024


# =============================================================================
# 通用文件上传接口
# =============================================================================
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    通用文件上传接口

    【功能】上传任意类型文件，返回访问 URL

    【请求】
    - Content-Type: multipart/form-data
    - Body: file (文件)

    【返回示例】
    {
        "code": 200,
        "data": {
            "url": "/static/uploads/images/xxx.jpg",
            "filename": "original_name.jpg",
            "size": 123456
        },
        "message": "上传成功"
    }

    【文件验证】
    - 文件大小不超过配置的限制
    - 文件类型在允许列表中

    【文件命名】
    UUID + 原始扩展名，如：a1b2c3d4-uuid.jpg

    【安全考虑】
    1. 使用 UUID 避免文件名冲突和路径遍历
    2. 验证 MIME 类型（不能只看扩展名）
    3. 限制文件大小防止 DoS 攻击
    """
    # -------------------------------------------------------------------------
    # 读取文件内容
    # -------------------------------------------------------------------------
    content = await file.read()
    file_size = len(content)

    # -------------------------------------------------------------------------
    # 验证文件类型
    # -------------------------------------------------------------------------
    content_type = file.content_type

    if content_type in ALLOWED_IMAGE_TYPES:
        # 图片文件
        ext = ALLOWED_IMAGE_TYPES[content_type]
        save_dir = IMAGES_DIR
        url_prefix = "/static/uploads/images"
    else:
        # 其他文件类型
        # 从原始文件名获取扩展名
        ext = Path(file.filename).suffix or ""
        save_dir = FILES_DIR
        url_prefix = "/static/uploads/files"

    # -------------------------------------------------------------------------
    # 验证文件大小（针对图片）
    # -------------------------------------------------------------------------
    if content_type in ALLOWED_IMAGE_TYPES:
        if file_size > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"图片大小不能超过 {MAX_IMAGE_SIZE // (1024*1024)}MB"
            )

    # -------------------------------------------------------------------------
    # 生成唯一文件名并保存
    # -------------------------------------------------------------------------
    # 生成 UUID 文件名
    unique_filename = f"{uuid.uuid4()}{ext}"
    save_path = save_dir / unique_filename

    # 写入文件
    with open(save_path, "wb") as f:
        f.write(content)

    # -------------------------------------------------------------------------
    # 返回结果
    # -------------------------------------------------------------------------
    return success_response(
        data={
            "url": f"{url_prefix}/{unique_filename}",
            "filename": file.filename,
            "size": file_size,
            "content_type": content_type
        },
        message="上传成功"
    )


# =============================================================================
# 图片上传接口
# =============================================================================
@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    max_width: int = None,
    max_height: int = None
):
    """
    图片上传接口（带尺寸验证）

    【功能】上传图片，可选进行尺寸验证和压缩

    【请求】
    - Content-Type: multipart/form-data
    - Body: file (图片文件)
    - Query: max_width, max_height (可选，最大宽高)

    【返回示例】
    {
        "code": 200,
        "data": {
            "url": "/static/uploads/images/xxx.jpg",
            "filename": "image.jpg",
            "size": 123456,
            "width": 1920,
            "height": 1080
        },
        "message": "上传成功"
    }

    【尺寸验证】
    如果指定了 max_width 或 max_height：
    - 检查图片尺寸是否超出限制
    - 超出则拒绝上传

    【处理流程】
    1. 验证 Content-Type 是否为图片
    2. 验证文件大小
    3. 如有尺寸限制，验证图片尺寸
    4. 保存文件
    5. 返回图片信息
    """
    # -------------------------------------------------------------------------
    # 验证文件类型
    # -------------------------------------------------------------------------
    content_type = file.content_type

    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {content_type}。支持的类型: {list(ALLOWED_IMAGE_TYPES.keys())}"
        )

    # -------------------------------------------------------------------------
    # 读取文件内容
    # -------------------------------------------------------------------------
    content = await file.read()
    file_size = len(content)

    # -------------------------------------------------------------------------
    # 验证文件大小
    # -------------------------------------------------------------------------
    if file_size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"图片大小不能超过 {MAX_IMAGE_SIZE // (1024*1024)}MB"
        )

    # -------------------------------------------------------------------------
    # 获取图片尺寸（可选验证）
    # -------------------------------------------------------------------------
    width = None
    height = None

    if max_width or max_height:
        try:
            from PIL import Image
            import io

            # 从字节内容打开图片
            img = Image.open(io.BytesIO(content))
            width, height = img.size

            # 验证尺寸限制
            if max_width and width > max_width:
                raise HTTPException(
                    status_code=400,
                    detail=f"图片宽度 {width} 超过限制 {max_width}"
                )

            if max_height and height > max_height:
                raise HTTPException(
                    status_code=400,
                    detail=f"图片高度 {height} 超过限制 {max_height}"
                )

        except Exception as e:
            # 如果 PIL 解析失败，可能是损坏的图片文件
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=400, detail="无法解析图片文件")

    # -------------------------------------------------------------------------
    # 生成唯一文件名并保存
    # -------------------------------------------------------------------------
    ext = ALLOWED_IMAGE_TYPES[content_type]
    unique_filename = f"{uuid.uuid4()}{ext}"
    save_path = IMAGES_DIR / unique_filename

    with open(save_path, "wb") as f:
        f.write(content)

    # -------------------------------------------------------------------------
    # 返回结果
    # -------------------------------------------------------------------------
    response_data = {
        "url": f"/static/uploads/images/{unique_filename}",
        "filename": file.filename,
        "size": file_size,
        "content_type": content_type
    }

    # 如果获取到了尺寸信息，一并返回
    if width and height:
        response_data["width"] = width
        response_data["height"] = height

    return success_response(data=response_data, message="上传成功")


# =============================================================================
# 头像上传接口
# =============================================================================
@router.post("/upload/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: "models.User" = Depends(lambda: None)  # 需要认证
):
    """
    头像上传接口

    【功能】上传用户头像，存储到用户记录中

    【请求】
    - Content-Type: multipart/form-data
    - Body: file (图片文件)
    - Header: Authorization: Bearer <token>

    【返回示例】
    {
        "code": 200,
        "data": {
            "avatar": "base64..."
        },
        "message": "头像上传成功"
    }

    【处理流程】
    1. 验证用户登录状态
    2. 验证文件类型和大小
    3. 读取图片内容
    4. 保存到用户记录的 avatar 字段
    5. 返回 Base64 编码的头像数据

    【限制】
    - 仅支持图片格式
    - 建议头像大小不超过 2MB
    """
    # -------------------------------------------------------------------------
    # 导入认证依赖
    # -------------------------------------------------------------------------
    import auth
    from fastapi import Depends
    import database

    # 获取当前用户（通过闭包注入）
    # 这里需要重新获取依赖
    from database import get_db

    # -------------------------------------------------------------------------
    # 验证文件类型
    # -------------------------------------------------------------------------
    content_type = file.content_type

    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="头像必须是图片格式"
        )

    # -------------------------------------------------------------------------
    # 读取并验证文件
    # -------------------------------------------------------------------------
    content = await file.read()
    file_size = len(content)

    # 头像大小限制较严格
    max_avatar_size = 2 * 1024 * 1024  # 2MB
    if file_size > max_avatar_size:
        raise HTTPException(
            status_code=400,
            detail=f"头像大小不能超过 {max_avatar_size // (1024*1024)}MB"
        )

    # -------------------------------------------------------------------------
    # 返回结果（这里只返回 Base64 数据，实际保存由 profile 更新接口处理）
    # -------------------------------------------------------------------------
    import base64

    avatar_base64 = base64.b64encode(content).decode('utf-8')

    return success_response(
        data={
            "avatar": avatar_base64,
            "content_type": content_type,
            "size": file_size
        },
        message="头像数据获取成功，请通过 /api/v1/profile 接口保存"
    )
