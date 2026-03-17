# 环境配置说明

本文档详细介绍宠物品种识别系统的环境配置步骤，包括 Python 依赖、MySQL 数据库配置等。

---

## 1. 系统要求

### 1.1 硬件要求

| 配置 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 4 核心 | 8 核心及以上 |
| 内存 | 8 GB | 16 GB 及以上 |
| 存储 | 20 GB | 50 GB 及以上 |
| GPU | 可选 | NVIDIA GPU (用于加速推理) |

### 1.2 软件要求

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.8+ | 推荐 3.9 |
| MySQL | 5.7+ | 推荐 8.0 |
| Node.js | 14+ | 用于前端开发 |
| Conda | 最新版 | 环境管理工具 |
| PowerShell | 5.1+ | Windows 终端 |

---

## 2. Python 环境配置

### 2.1 安装 Anaconda/Miniconda

访问 [Anaconda 官网](https://www.anaconda.com/) 下载安装包，或使用 Miniconda：

```powershell
# 使用 winget 安装 Miniconda
winget install Miniconda3.Miniconda3
```

### 2.2 创建 Conda 环境

```powershell
# 创建名为 yolo 的环境，指定 Python 版本
conda create -n yolo python=3.9

# 激活环境
conda activate yolo

# 验证 Python 版本
python --version
```

### 2.3 安装 Python 依赖

#### 2.3.1 基础依赖

```powershell
# 进入后端目录
cd system/back

# 安装 requirements.txt 中的依赖
pip install -r requirements.txt
```

`requirements.txt` 内容：

```
fastapi
uvicorn
sqlalchemy
pydantic
python-jose
passlib[bcrypt]
python-multipart
pymysql
```

#### 2.3.2 额外依赖

```powershell
# 安装 YOLOv5 相关依赖
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 安装图像处理和验证码依赖
pip install opencv-python captcha fastapi-mail

# 安装 JWT 支持
pip install python-jose[cryptography]

# 安装图片类型检测
pip install imghdr
```

> 注意：如果需要 GPU 加速，请访问 [PyTorch 官网](https://pytorch.org/) 获取对应的 CUDA 版本安装命令。

---

## 3. MySQL 数据库配置

### 3.1 安装 MySQL

#### Windows 安装

1. 下载 [MySQL Installer](https://dev.mysql.com/downloads/installer/)
2. 运行安装程序，选择 "Developer Default" 或 "Server only"
3. 设置 root 密码（建议使用 `abc&123` 或自定义）
4. 完成安装

#### 验证 MySQL 服务

```powershell
# 检查 MySQL 服务状态
Get-Service MySQL*

# 启动 MySQL 服务（如果未启动）
Start-Service MySQL80
```

### 3.2 创建数据库

#### 3.2.1 命令行方式

```powershell
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE yolo_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 退出
EXIT;
```

#### 3.2.2 应用程序自动创建

系统启动时会自动检查并创建数据库（需要在 `database.py` 中配置正确的凭据）。

### 3.3 数据库配置说明

编辑 `system/back/.env` 文件：

```env
# 数据库主机地址
DB_HOST=localhost

# 数据库端口
DB_PORT=3306

# 数据库用户名
DB_USER=root

# 数据库密码
DB_PASSWORD=abc&123

# 数据库名称
DB_NAME=yolo_system
```

> 注意：密码中的特殊字符（如 `@`, `:`, `&` 等）会被自动 URL 编码，无需手动处理。

---

## 4. 前端环境配置

### 4.1 安装 Node.js

```powershell
# 使用 winget 安装 Node.js LTS 版本
winget install OpenJS.NodeJS.LTS
```

### 4.2 安装前端依赖

```powershell
# 进入前端目录
cd system/pre

# 安装项目依赖
npm install
```

### 4.3 前端依赖说明

`package.json` 主要依赖：

```json
{
  "dependencies": {
    "vue": "^3.x",
    "uni-app": "^3.x",
    "uni-ui": "^1.x"
  },
  "devDependencies": {
    "vite": "^4.x",
    "@dcloudio/uni-cli-shared": "^3.x"
  }
}
```

---

## 5. YOLOv5 模型配置

### 5.1 模型文件位置

模型文件应放置在项目根目录的 `runs/pets_breed_detection_large12/weights/` 目录下：

```
yolov5-5.0/
└── runs/
    └── pets_breed_detection_large12/
        └── weights/
            └── best.pt    # 训练好的模型权重
```

### 5.2 模型配置参数

在 `system/back/routers/predict.py` 中配置：

```python
# 模型权重路径
WEIGHTS_PATH = os.path.join(project_root, "runs", "pets_breed_detection_large12", "weights", "best.pt")

# 输入图像尺寸
IMG_SIZE = 640

# 置信度阈值
CONF_THRES = 0.25

# IOU 阈值
IOU_THRES = 0.45
```

---

## 6. 邮件服务配置

### 6.1 配置说明

系统使用 QQ 邮箱发送验证码，配置在 `system/back/routers/auth.py` 中：

```python
# 邮件用户名（QQ 邮箱）
MAIL_USERNAME = "2669177036@qq.com"

# 邮件授权码（需要在 QQ 邮箱设置中获取）
MAIL_PASSWORD = "evypfvbfoxtadjaa"

# 发件人地址
MAIL_FROM = "2669177036@qq.com"

# 邮件服务器
MAIL_SERVER = "smtp.qq.com"

# 邮件端口（SSL）
MAIL_PORT = 465
```

### 6.2 获取 QQ 邮箱授权码

1. 登录 QQ 邮箱
2. 进入 "设置" -> "账户"
3. 找到 "POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务"
4. 开启 "SMTP 服务"
5. 点击 "生成授权码" 并保存

---

## 7. 启动服务

### 7.1 启动后端服务

```powershell
# 激活 conda 环境
conda activate yolo

# 进入后端目录
cd system/back

# 启动 FastAPI 服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后：
- API 文档：http://localhost:8000/docs
- API 根路径：http://localhost:8000/

### 7.2 启动前端开发服务器

```powershell
# 进入前端目录
cd system/pre

# 启动开发服务器
npm run dev
```

### 7.3 验证服务

```powershell
# 测试 API 根路径
curl http://localhost:8000/

# 测试登录接口
curl -X POST http://localhost:8000/api/v1/login `
     -H "Content-Type: application/json" `
     -d '{"username":"admin","password":"admin","captcha_key":"","captcha_code":""}'
```

---

## 8. 常见问题

### 8.1 Python 包安装失败

```powershell
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 8.2 MySQL 连接失败

1. 检查 MySQL 服务是否启动
2. 验证用户名和密码是否正确
3. 检查防火墙是否允许 3306 端口

```powershell
# 测试 MySQL 连接
mysql -u root -p -h localhost
```

### 8.3 YOLOv5 模型加载失败

1. 确认模型文件 `best.pt` 存在
2. 检查 PyTorch 是否正确安装
3. 确认 CUDA 版本与 PyTorch 匹配（如使用 GPU）

```python
# 测试 PyTorch
python -c "import torch; print(torch.__version__)"
```

### 8.4 端口被占用

```powershell
# 查看 8000 端口占用
netstat -ano | findstr :8000

# 终止占用进程
taskkill /PID <PID> /F
```

---

## 9. 环境变量汇总

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DB_HOST | localhost | 数据库主机 |
| DB_PORT | 3306 | 数据库端口 |
| DB_USER | root | 数据库用户名 |
| DB_PASSWORD | abc&123 | 数据库密码 |
| DB_NAME | yolo_system | 数据库名称 |

---

## 10. 目录结构说明

```
yolov5-5.0/
├── system/
│   ├── back/                    # 后端代码
│   │   ├── static/              # 静态文件（上传图片、识别结果）
│   │   │   ├── uploads/         # 用户上传文件
│   │   │   └── results/         # 识别结果
│   │   └── ...                  # 其他后端文件
│   └── pre/                     # 前端代码
├── models/                      # YOLOv5 模型定义
├── utils/                       # YOLOv5 工具函数
├── petsdata/                    # 宠物数据集
└── runs/                        # 训练结果和模型权重
```