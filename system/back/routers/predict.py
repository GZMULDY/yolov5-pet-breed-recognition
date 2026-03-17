from fastapi import APIRouter, UploadFile, File, HTTPException
from response import success_response, error_response, ResponseCode
import shutil
import os
import sys
import types
import uuid
from pathlib import Path
import cv2
import torch
import numpy as np
import random
import time

router = APIRouter()

current_file_path = os.path.abspath(__file__)
system_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
project_root = os.path.dirname(system_dir)

yolo_root = project_root
if yolo_root not in sys.path:
    sys.path.insert(0, yolo_root)

print(f"[Predict] YOLO root: {yolo_root}")
print(f"[Predict] sys.path[0]: {sys.path[0]}")

UPLOAD_DIR = os.path.join(system_dir, "static", "uploads")
RESULT_DIR = os.path.join(system_dir, "static", "results")
WEIGHTS_PATH = os.path.join(project_root, "runs", "pets_breed_detection_large12", "weights", "best.pt")
IMG_SIZE = 640
CONF_THRES = 0.25
IOU_THRES = 0.45

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

device = None
model = None
stride = 32
names = []
model_loaded = False

def ensure_model_loaded():
    global device, model, stride, names, model_loaded
    
    if model_loaded and model is not None:
        return True
    
    print(f"[Predict] Loading model...")
    print(f"[Predict] Model path: {WEIGHTS_PATH}")
    print(f"[Predict] Model exists: {os.path.exists(WEIGHTS_PATH)}")
    
    import importlib.util
    
    if yolo_root not in sys.path:
        sys.path.insert(0, yolo_root)
    
    try:
        # 首先创建 models 包（空的 __init__ 模块）
        models_package = types.ModuleType('models')
        models_package.__path__ = [os.path.join(yolo_root, 'models')]
        sys.modules['models'] = models_package
        print(f"[Predict] Created models package")
        
        # 加载 models.common
        common_spec = importlib.util.spec_from_file_location(
            "models.common", 
            os.path.join(yolo_root, "models", "common.py")
        )
        yolo_common = importlib.util.module_from_spec(common_spec)
        common_spec.loader.exec_module(yolo_common)
        sys.modules['models.common'] = yolo_common
        print(f"[Predict] Registered models.common")
        
        # 加载 models.experimental（必须在 models.yolo 之前加载）
        experimental_spec = importlib.util.spec_from_file_location(
            "models.experimental", 
            os.path.join(yolo_root, "models", "experimental.py")
        )
        yolo_experimental = importlib.util.module_from_spec(experimental_spec)
        experimental_spec.loader.exec_module(yolo_experimental)
        sys.modules['models.experimental'] = yolo_experimental
        print(f"[Predict] Registered models.experimental")
        
        # 加载 models.yolo（现在 models.experimental 已经存在）
        yolo_spec = importlib.util.spec_from_file_location(
            "models.yolo", 
            os.path.join(yolo_root, "models", "yolo.py")
        )
        yolo_yolo = importlib.util.module_from_spec(yolo_spec)
        yolo_spec.loader.exec_module(yolo_yolo)
        sys.modules['models.yolo'] = yolo_yolo
        print(f"[Predict] Registered models.yolo")
        
        # 获取 attempt_load 函数
        attempt_load = yolo_experimental.attempt_load
        print(f"[Predict] Loaded attempt_load from models.experimental")
        
    except Exception as e:
        print(f"[Predict] Error loading models module: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        # 加载 utils.general
        general_spec = importlib.util.spec_from_file_location(
            "utils.general", 
            os.path.join(yolo_root, "utils", "general.py")
        )
        yolo_general = importlib.util.module_from_spec(general_spec)
        general_spec.loader.exec_module(yolo_general)
        sys.modules['utils.general'] = yolo_general
        
        non_max_suppression = yolo_general.non_max_suppression
        print(f"[Predict] Loaded non_max_suppression from utils.general")
        
    except Exception as e:
        print(f"[Predict] Error loading general module: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        # 加载 utils.torch_utils
        torch_utils_spec = importlib.util.spec_from_file_location(
            "utils.torch_utils", 
            os.path.join(yolo_root, "utils", "torch_utils.py")
        )
        yolo_torch_utils = importlib.util.module_from_spec(torch_utils_spec)
        torch_utils_spec.loader.exec_module(yolo_torch_utils)
        sys.modules['utils.torch_utils'] = yolo_torch_utils
        
        select_device = yolo_torch_utils.select_device
        print(f"[Predict] Loaded select_device from utils.torch_utils")
        
    except Exception as e:
        print(f"[Predict] Error loading torch_utils module: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        device = select_device('')
        print(f"[Predict] Device: {device}")
        
        model = attempt_load(WEIGHTS_PATH, map_location=device)
        print(f"[Predict] Model loaded: {type(model)}")
        
        stride = int(model.stride.max())
        names = model.module.names if hasattr(model, 'module') else model.names
        print(f"[Predict] Classes: {names}")
        
        if device.type != 'cpu':
            model(torch.zeros(1, 3, IMG_SIZE, IMG_SIZE).to(device).type_as(next(model.parameters())))
        
        model_loaded = True
        print(f"[Predict] Model ready!")
        return True
        
    except Exception as e:
        print(f"[Predict] Load error: {e}")
        import traceback
        traceback.print_exc()
        return False

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleFill=False, scaleup=True, stride=32):
    shape = img.shape[:2]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)
    
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:
        r = min(r, 1.0)
    
    ratio = r, r
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    
    if auto:
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)
    elif scaleFill:
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])
        ratio = new_shape[1] / shape[1], new_shape[0] / shape[0]
    
    dw /= 2
    dh /= 2
    
    if shape[::-1] != new_unpad:
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    
    return img, ratio, (dw, dh)

def scale_coords(img1_shape, coords, img0_shape, ratio_pad=None):
    if ratio_pad is None:
        gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])
        pad = (img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2
    else:
        gain = ratio_pad[0][0]
        pad = ratio_pad[1]
    
    coords[:, [0, 2]] -= pad[0]
    coords[:, [1, 3]] /= gain
    coords[:, [0, 2]] = coords[:, [0, 2]].clamp(0, img0_shape[1])
    coords[:, [1, 3]] = coords[:, [1, 3]].clamp(0, img0_shape[0])
    
    return coords

def plot_one_box(x, img, color=None, label=None, line_thickness=3):
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)

@router.post("/predict")
async def predict(file: UploadFile = File(...)):
    print(f"[Predict] Request received, loading model...")
    
    if not ensure_model_loaded():
        print(f"[Predict] Model load failed!")
        raise HTTPException(status_code=503, detail="模型加载失败，请检查YOLOv5安装")
    
    print(f"[Predict] Model ready, processing file: {file.filename}")
    
    file_ext = file.filename.split(".")[-1].lower()
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    is_video = file_ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']
    
    if is_video:
        return process_video(file_path, filename)
    else:
        return process_image(file_path, filename)

def process_image(file_path, filename):
    from utils.general import non_max_suppression
    
    img0 = cv2.imread(file_path)
    if img0 is None:
        raise HTTPException(status_code=400, detail="无效的图片文件")
    
    img = letterbox(img0, IMG_SIZE, stride=stride)[0]
    img = img.transpose(2, 0, 1)
    img = np.ascontiguousarray(img)
    
    img = torch.from_numpy(img).to(device)
    img = img.float() / 255.0
    if img.ndimension() == 3:
        img = img.unsqueeze(0)
    
    with torch.no_grad():
        pred = model(img)[0]
    
    pred = non_max_suppression(pred, CONF_THRES, IOU_THRES)
    
    results = []
    det = pred[0]
    
    if len(det):
        det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()
        
        colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]
        
        for *xyxy, conf, cls in reversed(det):
            label = f'{names[int(cls)]} {conf:.2f}'
            results.append({
                "label": names[int(cls)],
                "confidence": float(conf),
                "bbox": [float(x) for x in xyxy]
            })
            
            c = int(cls)
            plot_one_box(xyxy, img0, label=label, color=colors[c], line_thickness=3)
    
    result_filename = f"res_{filename}"
    # 确保文件扩展名正确
    if not result_filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        result_filename = result_filename.rsplit('.', 1)[0] + '.jpg'
    result_path = os.path.join(RESULT_DIR, result_filename)
    cv2.imwrite(result_path, img0)
    
    image_url = f"http://127.0.0.1:8000/static/results/{result_filename}"
    
    return success_response(
        data={
            "type": "image",
            "results": results,
            "image_url": image_url
        },
        message="识别成功"
    )

def process_video(file_path, filename):
    from utils.general import non_max_suppression
    
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="无效的视频文件")
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    result_filename = f"res_{filename}"
    result_path = os.path.join(RESULT_DIR, result_filename)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(result_path, fourcc, fps, (width, height))
    
    results_summary = {}
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        img0 = frame.copy()
        
        img = letterbox(img0, IMG_SIZE, stride=stride)[0]
        img = img.transpose(2, 0, 1)
        img = np.ascontiguousarray(img)
        
        img = torch.from_numpy(img).to(device)
        img = img.float() / 255.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)
        
        with torch.no_grad():
            pred = model(img)[0]
        
        pred = non_max_suppression(pred, CONF_THRES, IOU_THRES)
        
        det = pred[0]
        if len(det):
            det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()
            
            colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]
            
            for *xyxy, conf, cls in reversed(det):
                label_name = names[int(cls)]
                results_summary[label_name] = results_summary.get(label_name, 0) + 1
                
                label = f'{label_name} {conf:.2f}'
                c = int(cls)
                plot_one_box(xyxy, img0, label=label, color=colors[c], line_thickness=3)
        
        out.write(img0)
    
    cap.release()
    out.release()
    
    video_url = f"http://127.0.0.1:8000/static/results/{result_filename}"
    
    summary_list = [{"label": k, "count": v} for k, v in results_summary.items()]
    
    return success_response(
        data={
            "type": "video",
            "results": summary_list,
            "video_url": video_url,
            "total_frames": frame_count
        },
        message="视频识别完成"
    )