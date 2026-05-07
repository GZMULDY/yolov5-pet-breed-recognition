"""
AI 图像识别路由模块

【模块职责】
提供基于 YOLOv5 的宠物品种识别功能，支持图像和视频检测。

【API 端点概览】
┌────────────────────┬────────┬────────────────────────────────┐
│       端点          │  方法  │            功能                 │
├────────────────────┼────────┼────────────────────────────────┤
│ /predict           │ POST   │ 图像识别（返回检测框）          │
│ /predict/video     │ POST   │ 视频识别（逐帧检测）            │
└────────────────────┴────────┴────────────────────────────────┘

【技术架构】
┌─────────────────────────────────────────────────────────────────┐
│                        请求处理流程                              │
├─────────────────────────────────────────────────────────────────┤
│  客户端上传图片/视频                                             │
│       ↓                                                         │
│  保存到临时文件                                                  │
│       ↓                                                         │
│  加载 YOLOv5 模型（懒加载）                                      │
│       ↓                                                         │
│  执行检测（detect.py）                                           │
│       ↓                                                         │
│  绘制检测框并保存结果图                                          │
│       ↓                                                         │
│  返回检测结果 JSON                                               │
└─────────────────────────────────────────────────────────────────┘

【模型加载策略】
- 懒加载：首次请求时加载模型，减少启动时间
- 单例模式：模型只加载一次，后续请求复用
- 模型位置：runs/pets_breed_detection_large12/weights/best.pt
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import database
import models
import schemas
import auth
from response import success_response
import os
import uuid
from pathlib import Path
import sys
import base64

# =============================================================================
# 路径配置
# =============================================================================
# 将 YOLOv5 根目录添加到 Python 路径
# 【原因】需要导入 YOLOv5 的 detect 模块
# 【注意】假设 backend 运行在 system/back/ 目录下
YOLOV5_ROOT = Path(__file__).parent.parent.parent.parent
if str(YOLOV5_ROOT) not in sys.path:
    sys.path.insert(0, str(YOLOV5_ROOT))

# =============================================================================
# 路由器创建
# =============================================================================
router = APIRouter()

# =============================================================================
# 全局模型变量（懒加载）
# =============================================================================
# 【设计模式】单例模式 + 懒加载
# 【原理】
# 1. 模型变量初始为 None
# 2. 首次请求时检查并加载模型
# 3. 后续请求直接使用已加载的模型
#
# 【优点】
# - 减少启动时间：不需要在启动时加载模型
# - 减少内存占用：如果预测功能不用，就不加载模型
# - 模型复用：避免每次请求重新加载模型
_model = None

# 模型配置
MODEL_PATH = "runs/pets_breed_detection_large12/weights/best.pt"
CONF_THRES = 0.25  # 置信度阈值：低于此值的检测框被过滤
IOU_THRES = 0.45   # IoU 阈值：用于 NMS 非极大值抑制


def get_model():
    """
    获取 YOLOv5 模型实例（懒加载）

    【懒加载策略】
    第一次调用时加载模型，后续调用返回已加载的模型

    【加载流程】
    1. 检查全局 _model 变量
    2. 如果为 None，加载模型
    3. 存储到 _model 变量
    4. 返回模型实例

    【返回】
    加载后的 PyTorch 模型实例

    【异常】
    如果模型文件不存在，抛出 FileNotFoundError
    """
    global _model
    if _model is None:
        import torch
        print(f"Loading YOLOv5 model from {MODEL_PATH}")

        # 检查模型文件是否存在
        model_path = YOLOV5_ROOT / MODEL_PATH
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # 临时移除 system/back/models.py 的缓存，避免与 YOLOv5 models/ 目录冲突
        cached_models = sys.modules.pop('models', None)

        try:
            # 使用 torch.hub.load 加载自定义训练的模型
            # 【注意】模型路径作为位置参数传递，不能使用 path= 关键字参数
            _model = torch.hub.load(
                str(YOLOV5_ROOT),
                'custom',
                str(model_path),
                source='local'
            )
        finally:
            # 恢复后端 ORM models 模块
            if cached_models is not None:
                sys.modules['models'] = cached_models

        print("Model loaded successfully")

    return _model


# =============================================================================
# 静态文件目录配置
# =============================================================================
# 确保结果图片存储目录存在
# 【目录结构】
# system/
# └── static/
#     ├── uploads/     # 原始上传文件
#     └── results/     # 检测结果图片
STATIC_DIR = Path(__file__).parent.parent.parent / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
RESULTS_DIR = STATIC_DIR / "results"

# 创建目录（如果不存在）
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 图像检测接口
# =============================================================================
@router.post("/predict")
async def predict_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    图像宠物品种识别

    【功能】上传图片，返回检测到的宠物品种和位置

    【请求】
    - Content-Type: multipart/form-data
    - Body: file (图片文件)

    【认证】需要 JWT 令牌

    【处理流程】
    1. 验证文件类型（仅支持图片）
    2. 生成唯一文件名并保存上传文件
    3. 加载 YOLOv5 模型
    4. 执行目标检测
    5. 绘制检测框并保存结果图
    6. 返回检测结果

    【返回数据】
    {
        "results": [
            {
                "class": "英国短毛猫",
                "confidence": 0.95,
                "bbox": [x1, y1, x2, y2]
            }
        ],
        "image_url": "/static/results/xxx.jpg",
        "original_image": "/static/uploads/xxx.jpg"
    }

    【支持的图片格式】
    - JPEG (.jpg, .jpeg)
    - PNG (.png)
    - BMP (.bmp)
    """
    # -------------------------------------------------------------------------
    # 文件类型验证
    # -------------------------------------------------------------------------
    # 检查文件扩展名
    allowed_extensions = [".jpg", ".jpeg", ".png", ".bmp"]
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}。支持: {allowed_extensions}"
        )

    # -------------------------------------------------------------------------
    # 保存上传文件
    # -------------------------------------------------------------------------
    # 生成唯一文件名：UUID + 原始扩展名
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    upload_path = UPLOADS_DIR / unique_filename

    # 写入文件内容
    content = await file.read()
    with open(upload_path, "wb") as f:
        f.write(content)

    # -------------------------------------------------------------------------
    # 执行检测
    # -------------------------------------------------------------------------
    try:
        # 获取模型实例（懒加载）
        model = get_model()

        # 执行推理
        # 设置 NMS 阈值（autoShape 类属性，通过实例设置）
        model.conf = CONF_THRES
        model.iou = IOU_THRES
        results = model(str(upload_path))

        # -------------------------------------------------------------------------
        # 解析检测结果
        # -------------------------------------------------------------------------
        # results.pandas().xyxy[0] 返回包含检测框信息的 DataFrame
        # 列包括: xmin, ymin, xmax, ymax, confidence, class, name
        detections = results.pandas().xyxy[0]

        detection_results = []
        for _, row in detections.iterrows():
            detection_results.append({
                "class": str(row['name']),           # 类别名称
                "confidence": float(row['confidence']), # 置信度
                "bbox": [
                    int(row['xmin']),  # 左上角 x
                    int(row['ymin']),  # 左上角 y
                    int(row['xmax']),  # 右下角 x
                    int(row['ymax'])   # 右下角 y
                ]
            })

        # -------------------------------------------------------------------------
        # 保存检测结果图
        # -------------------------------------------------------------------------
        # 结果图文件名：result_原文件名
        result_filename = f"result_{unique_filename}"
        result_path = RESULTS_DIR / result_filename

        # 使用 YOLOv5 内置方法绘制检测框并保存结果图
        # OpenCV 绘制需要可写数组，先确保 imgs 可写
        for i in range(len(results.imgs)):
            results.imgs[i] = results.imgs[i].copy()
        results.render()

        # 保存结果图
        import cv2
        rendered = results.imgs[0]  # RGB 格式 numpy 数组
        cv2.imwrite(str(result_path), cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR))

        # -------------------------------------------------------------------------
        # 返回结果
        # -------------------------------------------------------------------------
        return success_response(
            data={
                "results": detection_results,
                "image_url": f"/static/results/{result_filename}",
                "original_image": f"/static/uploads/{unique_filename}"
            },
            message="识别完成"
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"模型加载失败: {str(e)}")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        # 将错误写入日志文件方便排查
        try:
            with open(Path(__file__).parent.parent / "error.log", "a") as f:
                import datetime
                f.write(f"\n[{datetime.datetime.now()}] PREDICT ERROR\n")
                f.write(tb)
                f.write("\n" + "="*60 + "\n")
        except:
            pass
        raise HTTPException(status_code=500, detail=f"识别过程出错: {str(e)}")


# =============================================================================
# 视频检测接口
# =============================================================================
@router.post("/predict/video")
async def predict_video(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    视频宠物品种识别

    【功能】上传视频，逐帧检测宠物品种

    【请求】
    - Content-Type: multipart/form-data
    - Body: file (视频文件)

    【认证】需要 JWT 令牌

    【处理流程】
    1. 验证文件类型（仅支持视频）
    2. 保存上传文件
    3. 逐帧读取视频
    4. 对每一帧执行检测
    5. 汇总结果返回

    【注意】
    视频检测较耗时，建议限制视频时长

    【支持的格式】
    - MP4 (.mp4)
    - AVI (.avi)
    - MOV (.mov)
    """
    # -------------------------------------------------------------------------
    # 文件类型验证
    # -------------------------------------------------------------------------
    allowed_extensions = [".mp4", ".avi", ".mov"]
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的视频格式: {file_ext}"
        )

    # -------------------------------------------------------------------------
    # 保存上传文件
    # -------------------------------------------------------------------------
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    upload_path = UPLOADS_DIR / unique_filename

    content = await file.read()
    with open(upload_path, "wb") as f:
        f.write(content)

    try:
        # -------------------------------------------------------------------------
        # 读取视频并逐帧检测
        # -------------------------------------------------------------------------
        import cv2

        # 打开视频文件
        cap = cv2.VideoCapture(str(upload_path))
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="无法打开视频文件")

        # 获取模型
        model = get_model()

        # 结果收集
        all_detections = {}  # {类别: 出现次数}
        frame_count = 0

        # 逐帧处理
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # 每 5 帧检测一次（提高性能）
            if frame_count % 5 != 0:
                continue

            # 执行检测
            model.conf = CONF_THRES
            model.iou = IOU_THRES
            results = model(frame)
            detections = results.pandas().xyxy[0]

            # 统计检测结果
            for _, row in detections.iterrows():
                class_name = str(row['name'])
                if class_name not in all_detections:
                    all_detections[class_name] = 0
                all_detections[class_name] += 1

        cap.release()

        # -------------------------------------------------------------------------
        # 汇总结果
        # -------------------------------------------------------------------------
        # 对检测结果按出现次数降序排列
        sorted_detections = sorted(
            all_detections.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 取出现次数最多的作为主要识别结果
        main_result = sorted_detections[0] if sorted_detections else None

        return success_response(
            data={
                "total_frames": frame_count,
                "main_detection": {
                    "class": main_result[0],
                    "appearances": main_result[1]
                } if main_result else None,
                "all_detections": dict(sorted_detections),
                "video_url": f"/static/uploads/{unique_filename}"
            },
            message="视频分析完成"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"视频分析出错: {str(e)}")
