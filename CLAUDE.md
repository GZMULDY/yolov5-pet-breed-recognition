# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pet breed recognition system built on YOLOv5 v5.0, with a FastAPI backend, MySQL database, and Vue 3 frontend. The system detects and classifies 144 pet breeds (cats and dogs) from images/video.

## Runtime Environment

- Python runs in local conda `yolo` virtual environment: `conda activate yolo`
- Terminal is PowerShell on Windows
- Frontend uses UniApp conventions (use `uni.*` APIs, `uni.navigateTo` for routing)
- All API responses follow RESTful conventions with unified response format: `{code, message, data, timestamp}`

## Commands

### YOLOv5 Training & Inference

```bash
# Train (fine-tune from pretrained)
python train.py --data petsdata/dataset/pets_breeds.yaml --weights yolov5m.pt --img 640 --epochs 100

# Train from scratch
python train.py --data petsdata/dataset/pets_breeds.yaml --cfg models/yolov5m.yaml --weights '' --img 640 --epochs 300 --batch-size 16

# Resume training
python train.py --resume runs/pets_breed_detection_large12/weights/last.pt

# Detect/inference
python detect.py --weights runs/pets_breed_detection_large12/weights/best.pt --source petsdata/mytest/ --img 640

# Validate (mAP, precision, recall)
python test.py --data petsdata/dataset/pets_breeds.yaml --weights runs/pets_breed_detection_large12/weights/best.pt

# Export model
python export.py --weights runs/pets_breed_detection_large12/weights/best.pt --include onnx

# Split dataset into train/val/test
python petsdata/split_dataset_811.py --src "petsdata/images" --seed 42 --convert-xml --xml-dir "petsdata/annotations/xmls"
```

### Backend (FastAPI)

```bash
cd system/back
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Vue 3 + Vite)

```bash
cd system/pre
npm install
npm run dev      # Dev server
npm run build    # Production build
```

## Architecture

### YOLOv5 Pipeline

- `train.py` → training loop with EMA, AMP, OneCycleLR scheduler, optional hyperparameter evolution
- `detect.py` → inference on images/video/webcam
- `test.py` → validation (mAP@0.5, mAP@0.5:0.95, precision, recall)
- `export.py` → export to ONNX/TensorRT/CoreML/etc.
- `models/yolo.py` → `Model` class parses YAML architecture and builds `nn.Sequential`; `Detect` layer handles 3-scale anchor-based detection (P3/8, P4/16, P5/32)
- `utils/loss.py` → `ComputeLoss` with 3 components: CIoU box loss, BCE objectness loss, BCE classification loss
- `utils/datasets.py` → dataset loading, mosaic augmentation, letterbox resizing

### Configuration System

Three layers of YAML configs control training:
1. **Data config** (`petsdata/dataset/pets_breeds.yaml`): dataset paths, 144 class names, `nc: 144`
2. **Model config** (`models/yolov5{s,m,l,x}.yaml`): network architecture via depth/width multipliers
3. **Hyperparameter config** (`data/hyp.scratch.yaml`, `data/hyp.finetune.yaml`): lr, augmentation, loss gains

Model size variants differ only in `depth_multiple` and `width_multiple` (yolov5m: 0.67/0.75).

### Backend (system/back/)

```
main.py           → FastAPI app, CORS, startup init (default users, pet data seeding)
auth.py           → JWT (HS256, 30min expiry), password hashing (pbkdf2_sha256)
database.py       → SQLAlchemy + PyMySQL, MySQL at localhost:3306/yolo_system
models.py         → ORM: pet_categories (self-referential hierarchy), pet_breeds, users, articles
schemas.py        → Pydantic request/response validation
response.py       → Unified response helpers: success_response(), error_response(), paginated_response()
init_pets.py      → Seeds ~80+ breeds from hardcoded data (hierarchical: Cat/Dog → subcategory → breed)
routers/
  auth.py         → /api/v1/login, register, captcha, profile, user CRUD
  predict.py      → /api/v1/predict (image/video → YOLOv5 detection; model lazy-loaded)
  pets.py         → /api/v1/pets (breed CRUD, search, category tree)
  articles.py     → /api/v1/articles (CRUD, admin-only create/update/delete)
  upload.py       → /api/v1/upload (file upload)
```

Auth dependency levels: `get_current_user` (any authenticated), `get_current_active_user`, `get_current_admin_user` (admin only).

The prediction model loads lazily on first `/predict` request from `runs/pets_breed_detection_large12/weights/best.pt` with CONF_THRES=0.25, IOU_THRES=0.45.

### Frontend (system/pre/)

Vue 3 Composition API with `<script setup>`, UniApp adapter layer for potential mobile deployment. Pages configured in `src/pages.json` and `src/router/index.js`.

Key pages: login → dashboard → recognize (AI detection), encyclopedia (breed browser), articles, profile, admin (users/articles management).

HTTP client (`src/utils/request.js`): base URL `http://127.0.0.1:8000/api/v1`, auto JWT injection, 401 redirect to login.

### Database

MySQL with 4 tables: `pet_categories` (self-referential tree for Cat/Dog hierarchy), `pet_breeds` (breed details with LONGBLOB images), `users` (with LONGBLOB avatars, role-based admin/user), `articles`. Auto-created on startup. Default credentials: admin/admin, user/user.

## Key Conventions

- YOLOv5 training output goes to `runs/<experiment_name>/weights/` (best.pt, last.pt)
- Dataset format: images in `petsdata/images/`, labels in `petsdata/labels/` (YOLO format .txt), XML annotations in `petsdata/annotations/xmls/`
- The `system/static/` directory stores uploaded and result images at runtime
- Backend code must have complete, logically clear comments and follow RESTful API design
- Frontend must follow UniApp conventions and use unified request/response patterns
