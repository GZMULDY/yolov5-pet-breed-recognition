from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
import os
import base64
from pathlib import Path
from typing import Optional
import models, auth
from response import success_response

router = APIRouter()

UPLOAD_DIR = Path(__file__).parent.parent / "static" / "uploads" / "pets"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload/image")
async def upload_image(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user)
):
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        body = await request.json()

        if "image" in body:
            try:
                image_data = base64.b64decode(body["image"])
                filename = body.get("filename", "image.jpg")
                file_ext = os.path.splitext(filename)[1] or ".jpg"
                if not file_ext.startswith("."):
                    file_ext = ".jpg"

                mime_type = f"image/{file_ext[1:]}" if file_ext[1:] else "image/jpeg"
                base64_data = f"data:{mime_type};base64,{body['image']}"

                return success_response(
                    data={
                        "url": base64_data,
                        "data": body["image"],
                        "filename": filename
                    },
                    message="图片上传成功"
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"图片解码失败: {str(e)}")

    raise HTTPException(status_code=400, detail="请提供图片文件")
