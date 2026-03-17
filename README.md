# 宠物品种识别系统 (YOLO Pet Breed Recognition System)

## 项目简介

这是一个基于 YOLOv5 的宠物品种识别系统，采用前后端分离架构设计。

### 技术栈

- **后端**: FastAPI (Python Web 框架)
- **前端**: UniApp (跨平台应用框架)
- **数据库**: MySQL
- **目标检测**: YOLOv5
- **认证**: JWT Token

### 功能特性

- 用户注册与登录（含图形验证码和邮箱验证）
- 宠物图片/视频智能识别
- 宠物品种百科查询
- 管理员用户管理
- RESTful API 设计

---

## 项目结构

```
yolov5-5.0/
├── system/                      # 系统代码目录
│   ├── back/                    # FastAPI 后端
│   │   ├── routers/             # API 路由模块
│   │   │   ├── auth.py          # 认证接口
│   │   │   ├── pets.py          # 宠物品种接口
│   │   │   ├── predict.py       # 预测识别接口
│   │   │   ├── upload.py        # 文件上传接口
│   │   │   └── articles.py      # 文章接口
│   │   ├── main.py              # 应用入口
│   │   ├── models.py            # 数据库模型
│   │   ├── schemas.py           # Pydantic 数据模型
│   │   ├── database.py          # 数据库配置
│   │   ├── auth.py              # 认证工具
│   │   ├── response.py          # 统一响应格式
│   │   ├── requirements.txt     # Python 依赖
│   │   └── .env.example         # 环境变量示例
│   ├── pre/                     # UniApp 前端
│   │   ├── src/
│   │   │   ├── api/             # API 请求封装
│   │   │   ├── pages/           # 页面组件
│   │   │   ├── router/          # 路由配置
│   │   │   └── utils/           # 工具函数
│   │   └── package.json         # 前端依赖
│   └── static/                  # 静态文件目录
│       ├── uploads/             # 上传文件
│       └── results/             # 识别结果
├── models/                      # YOLOv5 模型代码
├── utils/                       # YOLOv5 工具代码
├── petsdata/                    # 宠物数据集
│   └── dataset/
│       ├── images/              # 训练/测试图片
│       └── labels/              # 标注文件
└── detect.py                    # YOLOv5 检测脚本
```

---

## 快速开始

### 1. 环境要求

- Python 3.8+
- MySQL 5.7+
- Node.js 14+ (用于前端开发)
- Conda (推荐用于环境管理)

### 2. 后端安装与运行

#### 2.1 创建并激活 Conda 环境

```powershell
# 创建名为 yolo 的环境
conda create -n yolo python=3.9

# 激活环境
conda activate yolo
```

#### 2.2 安装 Python 依赖

```powershell
# 进入后端目录
cd system/back

# 安装依赖
pip install -r requirements.txt

# 额外安装 YOLOv5 相关依赖
pip install torch torchvision opencv-python
pip install captcha fastapi-mail python-jose[cryptography]
```

#### 2.3 配置数据库

确保 MySQL 服务已启动，并创建数据库：

```sql
CREATE DATABASE yolo_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 2.4 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=abc&123
DB_NAME=yolo_system
```

#### 2.5 启动后端服务

```powershell
# 在 system/back 目录下运行
cd system/back
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后，访问 http://localhost:8000 查看 API 文档。

### 3. 前端安装与运行

#### 3.1 安装 Node.js 依赖

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
| admin  | admin | 管理员 |
| user   | user  | 普通用户 |

---

## API 接口概览

### 认证接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/register | 用户注册 |
| POST | /api/v1/login | 用户登录 |
| GET | /api/v1/me | 获取当前用户信息 |
| GET | /api/v1/profile | 获取用户资料 |
| PUT | /api/v1/profile | 更新用户资料 |
| GET | /api/v1/captcha/{key} | 获取验证码图片 |
| POST | /api/v1/send-email-code | 发送邮箱验证码 |
| POST | /api/v1/verify-email-code | 验证邮箱验证码 |

### 宠物品种接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/categories | 获取宠物分类 |
| GET | /api/v1/categories/{id}/children | 获取子分类 |
| GET | /api/v1/breeds | 获取品种列表 |
| GET | /api/v1/breeds/{id} | 获取品种详情 |
| GET | /api/v1/breeds/by-name/{name} | 按英文名获取品种 |

### 预测接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/predict | 上传图片/视频进行识别 |

### 上传接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/upload/image | 上传图片 |

详细 API 文档请参阅 [API.md](API.md)

---

## 开发说明

### 代码规范

- 后端遵循 RESTful API 设计规范
- 统一响应格式，详见 [response.py](system/back/response.py)
- 所有接口都有详细的中文注释

### 统一响应格式

```json
{
    "code": "200",
    "message": "success",
    "data": {...},
    "timestamp": 1234567890
}
```

### 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 许可证

MIT License