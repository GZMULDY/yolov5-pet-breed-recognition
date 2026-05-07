# 宠物品种识别系统 (YOLO Pet Breed Recognition System)

## 项目简介

这是一个基于 YOLOv5 的宠物品种识别系统，采用前后端分离架构设计。系统可识别 144 种宠物品种（猫和狗），支持图片和视频识别。

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + UniApp 适配层 |
| 后端 | FastAPI (Python Web 框架) |
| 数据库 | MySQL 5.7+ / SQLAlchemy ORM |
| 目标检测 | YOLOv5 v5.0 (PyTorch) |
| 认证 | JWT (HS256, 30min 过期) |
| 环境管理 | Conda |

### 功能特性

- 用户注册与登录（图形验证码 + 邮箱验证）
- 宠物图片/视频智能识别（144 种品种）
- 宠物品种百科（分层分类浏览）
- 文章资讯模块
- 管理员后台（用户管理、文章管理、品种管理）
- RESTful API 设计

---

## 项目结构

```
yolov5-5.0/
├── start.py                        # 一键启动脚本
├── requirements.txt                # 项目级依赖
├── system/                        # 系统代码目录
│   ├── back/                      # FastAPI 后端
│   │   ├── routers/               # API 路由层
│   │   │   ├── auth.py            # 认证接口
│   │   │   ├── pets.py            # 宠物品种接口
│   │   │   ├── predict.py         # 预测识别接口
│   │   │   ├── upload.py          # 文件上传接口
│   │   │   └── articles.py        # 文章接口
│   │   ├── services/              # 业务逻辑层
│   │   │   ├── user_service.py    # 用户业务
│   │   │   ├── pet_service.py     # 宠物业务
│   │   │   └── article_service.py # 文章业务
│   │   ├── main.py                # 应用入口
│   │   ├── config.py              # 统一配置管理
│   │   ├── models.py              # 数据库 ORM 模型
│   │   ├── schemas.py             # Pydantic 数据模型
│   │   ├── database.py            # 数据库连接
│   │   ├── auth.py                # JWT 认证工具
│   │   ├── response.py            # 统一响应格式
│   │   ├── init_pets.py           # 宠物数据初始化
│   │   ├── requirements.txt       # Python 依赖
│   │   └── .env.example           # 环境变量示例
│   ├── pre/                        # Vue 3 前端
│   │   ├── src/
│   │   │   ├── api/               # API 请求封装
│   │   │   ├── pages/             # 页面组件
│   │   │   ├── router/            # 路由配置
│   │   │   ├── composables/       # Vue 组合式函数
│   │   │   └── utils/             # 工具函数（uni-adapter 等）
│   │   └── package.json           # 前端依赖
│   └── static/                    # 静态文件目录
│       ├── uploads/               # 上传文件
│       └── results/               # 识别结果图片
├── models/                        # YOLOv5 模型定义
├── utils/                         # YOLOv5 工具函数
├── runs/                          # 训练输出目录
│   └── pets_breed_detection_large12/
│       └── weights/
│           ├── best.pt            # 最佳模型权重
│           └── last.pt            # 最后一次训练权重
├── petsdata/                      # 宠物数据集
│   └── dataset/
│       ├── images/                # 训练/测试图片
│       └── labels/                # 标注文件 (YOLO格式)
├── train.py                       # YOLOv5 训练脚本
├── detect.py                      # YOLOv5 检测脚本
├── test.py                        # YOLOv5 验证脚本
└── export.py                      # 模型导出脚本
```

---

## 快速开始

### 1. 环境要求

| 软件 | 版本要求 |
|------|----------|
| Python | 3.8+ |
| MySQL | 5.7+ |
| Node.js | 14+ |
| Conda | 推荐 |

### 2. 一键启动（推荐）

```powershell
# 使用 conda 环境的 Python 直接启动
D:\Annaconda\envs\yolo\python.exe start.py
```

脚本会自动清理端口残留进程，依次启动后端和前端，Ctrl+C 统一停止。

### 3. 后端手动安装与运行

#### 3.1 创建 Conda 环境

```powershell
conda create -n yolo python=3.9 -y
conda activate yolo
```

#### 3.2 安装依赖

```powershell
cd system/back
pip install -r requirements.txt

# PyTorch (根据 CUDA 版本选择)
pip install torch torchvision                      # CPU
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118  # CUDA 11.8
```

#### 3.3 配置数据库

确保 MySQL 服务已启动。数据库和表结构首次启动时自动创建。

#### 3.4 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/yolo_system
SECRET_KEY=your_secret_key_here
DEFAULT_ADMIN_PASSWORD=admin
DEFAULT_USER_PASSWORD=user
```

#### 3.5 启动后端

```powershell
cd system/back
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后：
- API 服务: http://localhost:8000
- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

### 4. 前端手动安装与运行

#### 3.1 安装依赖

```powershell
# 进入前端目录
cd system/pre

# 安装依赖
npm install
```

#### 3.2 运行开发服务器

```powershell
# 启动开发服务器
npm run dev
```

#### 3.3 构建生产版本

```powershell
# 构建 H5 版本
npm run build:h5
```

---

## 默认账户

系统启动时会自动创建以下默认账户：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin | 管理员 |
| user | user | 普通用户 |

**生产环境请务必修改默认密码！**

---

## API 接口概览

### 认证接口 `/api/v1`

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /register | 用户注册 | 公开 |
| POST | /login | 用户登录 | 公开 |
| GET | /me | 获取当前用户 | 登录 |
| GET | /profile | 获取用户资料 | 登录 |
| PUT | /profile | 更新用户资料 | 登录 |
| GET | /captcha/{key} | 获取验证码图片 | 公开 |
| POST | /send-email-code | 发送邮箱验证码 | 公开 |
| POST | /verify-email-code | 验证邮箱验证码 | 公开 |

### 宠物品种接口 `/api/v1`

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /pets/categories | 获取分类列表 | 登录 |
| GET | /pets/categories/tree | 获取完整分类树 | 登录 |
| POST | /pets/categories | 创建分类 | 管理员 |
| DELETE | /pets/categories/{id} | 删除分类 | 管理员 |
| GET | /pets/breeds | 获取品种列表 | 登录 |
| GET | /pets/breeds/search | 搜索品种 | 登录 |
| GET | /pets/breeds/by-name/{name_en} | 按英文名获取品种 | 登录 |
| GET | /pets/breeds/{id} | 获取品种详情 | 登录 |
| POST | /pets/breeds | 创建品种 | 管理员 |
| PUT | /pets/breeds/{id} | 更新品种 | 管理员 |
| DELETE | /pets/breeds/{id} | 删除品种 | 管理员 |

### 预测接口 `/api/v1`

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /predict | 上传图片/视频识别 | 登录 |

### 文章接口 `/api/v1`

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | /articles | 获取文章列表 | 登录 |
| GET | /articles/{id} | 获取文章详情 | 登录 |
| POST | /articles | 创建文章 | 管理员 |
| PUT | /articles/{id} | 更新文章 | 管理员 |
| DELETE | /articles/{id} | 删除文章 | 管理员 |

### 上传接口 `/api/v1`

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /upload/image | 上传图片 | 登录 |
| POST | /upload/avatar | 上传头像 | 登录 |

---

## 统一响应格式

所有 API 返回统一的 JSON 格式：

```json
{
    "code": 200,
    "message": "success",
    "data": { ... },
    "timestamp": 1234567890
}
```

### 响应码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token 无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## YOLOv5 训练说明

### 数据集格式

```
petsdata/dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

### 训练命令

```powershell
# 激活环境
conda activate yolo

# 从预训练模型微调 (推荐)
python train.py --data petsdata/dataset/pets_breeds.yaml --weights yolov5m.pt --img 640 --epochs 100

# 从头训练
python train.py --data petsdata/dataset/pets_breeds.yaml --cfg models/yolov5m.yaml --weights '' --img 640 --epochs 300

# 恢复训练
python train.py --resume runs/pets_breed_detection_large12/weights/last.pt
```

### 验证模型

```powershell
python test.py --data petsdata/dataset/pets_breeds.yaml --weights runs/pets_breed_detection_large12/weights/best.pt
```

### 导出模型

```powershell
python export.py --weights runs/pets_breed_detection_large12/weights/best.pt --include onnx
```

---

## 开发规范

### 后端架构

```
Router (路由层) -> Service (业务层) -> Model (数据层)
```

- **Router**: 处理 HTTP 请求，参数校验，调用 Service
- **Service**: 业务逻辑处理，数据转换
- **Model**: 数据库 ORM 映射

### 前端架构

```
Page (页面) -> API (请求封装) -> Utils (工具函数)
```

- **Page**: Vue 3 Composition API 组件
- **API**: 统一封装 uni.request 请求
- **Utils**: 通用工具函数

### 代码规范

- 后端遵循 RESTful API 设计
- 完整的中文注释
- 统一的响应格式

---

## 许可证

MIT License
