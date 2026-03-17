from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from jose import jwt, JWTError
import os
import uuid
import base64
from pathlib import Path
from typing import Optional
from response import success_response, error_response, ResponseCode

router = APIRouter()

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"

UPLOAD_DIR = Path(__file__).parent.parent / "static" / "uploads" / "pets"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="未授权，请先登录")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="无效的认证方案")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的token")
        
        return username
    except Exception:
        raise HTTPException(status_code=401, detail="token无效")

@router.post("/upload/image")
async def upload_image(
    request: Request,
    current_user: str = Depends(verify_token)
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