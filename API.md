# API 接口文档

本文档详细描述宠物品种识别系统的所有 API 接口，包含请求格式、响应示例和错误处理。

---

## 1. 通用说明

### 1.1 基础 URL

```
http://localhost:8000
```

### 1.2 统一响应格式

所有 API 响应都遵循以下统一格式：

```json
{
    "code": "200",
    "message": "success",
    "data": {...},
    "timestamp": 1234567890
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 状态码 |
| message | string | 响应消息 |
| data | any | 响应数据 |
| timestamp | int | 时间戳 |

### 1.3 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（需要登录） |
| 403 | 权限不足（需要管理员权限） |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 1.4 认证方式

除公开接口外，其他接口需要在请求头中携带 JWT Token：

```
Authorization: Bearer <token>
```

---

## 2. 认证接口 (Auth)

### 2.1 获取验证码 Key

获取验证码图片的唯一标识 Key。

**请求**

```http
GET /api/v1/captcha
```

**响应示例**

```json
{
    "code": "200",
    "message": "请提供 key 查询参数",
    "data": null,
    "timestamp": 1700000000
}
```

### 2.2 获取验证码图片

获取图形验证码图片。

**请求**

```http
GET /api/v1/captcha/{key}
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| key | string | 是 | 验证码 Key |

**响应**

返回 PNG 格式的图片二进制数据。

### 2.3 发送邮箱验证码

发送注册邮箱验证码。

**请求**

```http
POST /api/v1/send-email-code
Content-Type: application/json
```

**请求体**

```json
{
    "email": ["example@example.com"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | array[string] | 是 | 邮箱地址数组 |

**响应示例**

```json
{
    "code": "200",
    "message": "验证码已发送",
    "data": null,
    "timestamp": 1700000000
}
```

**错误响应**

```json
{
    "code": "400",
    "message": "Email already registered",
    "data": null,
    "timestamp": 1700000000
}
```

### 2.4 验证邮箱验证码

验证邮箱验证码是否正确。

**请求**

```http
POST /api/v1/verify-email-code
Content-Type: application/json
```

**请求体**

```json
{
    "email": "example@example.com",
    "code": "123456"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| code | string | 是 | 验证码 |

**响应示例**

```json
{
    "code": "200",
    "message": "邮箱验证成功",
    "data": null,
    "timestamp": 1700000000
}
```

### 2.5 用户注册

注册新用户账号。

**请求**

```http
POST /api/v1/register
Content-Type: application/json
```

**请求体**

```json
{
    "username": "newuser",
    "email": "example@example.com",
    "password": "password123"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（唯一） |
| email | string | 否 | 邮箱地址（可选） |
| password | string | 是 | 密码 |

**响应示例**

```json
{
    "code": "201",
    "message": "注册成功",
    "data": {
        "id": 3,
        "username": "newuser",
        "email": "example@example.com",
        "role": "user"
    },
    "timestamp": 1700000000
}
```

**错误响应**

```json
{
    "code": "400",
    "message": "用户名已注册",
    "data": null,
    "timestamp": 1700000000
}
```

### 2.6 用户登录

用户登录并获取访问令牌。

**请求**

```http
POST /api/v1/login
Content-Type: application/json
```

**请求体**

```json
{
    "username": "admin",
    "password": "admin",
    "captcha_key": "abc123",
    "captcha_code": "xyzt"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| captcha_key | string | 否 | 验证码 Key |
| captcha_code | string | 否 | 验证码 |

**响应示例**

```json
{
    "code": "200",
    "message": "登录成功",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "role": "admin",
        "username": "admin",
        "id": 1
    },
    "timestamp": 1700000000
}
```

### 2.7 获取当前用户信息

获取已登录用户的详细信息。

**请求**

```http
GET /api/v1/me
Authorization: Bearer <token>
```

**响应示例**

```json
{
    "code": "200",
    "message": "success",
    "data": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "nickname": "管理员",
        "avatar": "base64_encoded_image...",
        "role": "admin",
        "is_verified": true,
        "created_at": "2024-01-01T00:00:00",
        "last_login": "2024-01-15T10:30:00"
    },
    "timestamp": 1700000000
}
```

### 2.8 获取用户资料

获取当前用户的个人资料（与 /me 接口相同）。

**请求**

```http
GET /api/v1/profile
Authorization: Bearer <token>
```

### 2.9 更新用户资料

更新当前用户的个人资料。

**请求**

```http
PUT /api/v1/profile
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**

```json
{
    "nickname": "新昵称",
    "avatar": "base64_encoded_image_data"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | string | 否 | 昵称（最长50字符） |
| avatar | string | 否 | 头像（Base64 编码） |

**响应示例**

```json
{
    "code": "200",
    "message": "个人信息更新成功",
    "data": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "nickname": "新昵称",
        "avatar": "base64_encoded_image...",
        "role": "admin"
    },
    "timestamp": 1700000000
}
```

### 2.10 获取用户头像

获取指定用户的头像图片。

**请求**

```http
GET /api/v1/avatar/{user_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 是 | 用户 ID |

**响应**

返回 JPEG 格式的图片二进制数据。

---

## 3. 宠物品种接口 (Pets)

### 3.1 获取宠物分类

获取所有顶级宠物分类。

**请求**

```http
GET /api/v1/categories
Authorization: Bearer <token>
```

**响应示例**

```json
{
    "code": "200",
    "message": "success",
    "data": [
        {
            "id": 1,
            "name": "猫",
            "name_en": "cat",
            "parent_id": null,
            "icon": null,
            "sort_order": 0,
            "children": [
                {
                    "id": 2,
                    "name": "纯种猫",
                    "name_en": "purebred_cat",
                    "parent_id": 1,
                    "icon": null,
                    "sort_order": 0,
                    "children": []
                }
            ]
        },
        {
            "id": 3,
            "name": "狗",
            "name_en": "dog",
            "parent_id": null,
            "icon": null,
            "sort_order": 1,
            "children": []
        }
    ],
    "timestamp": 1700000000
}
```

### 3.2 获取子分类

获取指定分类的子分类。

**请求**

```http
GET /api/v1/categories/{category_id}/children
Authorization: Bearer <token>
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category_id | integer | 是 | 分类 ID |

**响应示例**

```json
{
    "code": "200",
    "message": "success",
    "data": [
        {
            "id": 2,
            "name": "纯种猫",
            "name_en": "purebred_cat",
            "parent_id": 1,
            "icon": null,
            "sort_order": 0,
            "children": []
        }
    ],
    "timestamp": 1700000000
}
```

### 3.3 获取品种列表

获取宠物品种列表，可按分类筛选。

**请求**

```http
GET /api/v1/breeds?category_id=1
Authorization: Bearer <token>
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category_id | integer | 否 | 分类 ID |

**响应示例**

```json
{
    "code": "200",
    "message": "success",
    "data": [
        {
            "id": 1,
            "name": "孟加拉豹猫",
            "name_en": "Bengal",
            "category_id": 2,
            "image": "data:image/jpeg;base64,/9j/4AAQ...",
            "description": "孟加拉豹猫是一种...",
            "origin": "美国",
            "personality": "活泼、好奇",
            "care_tips": "需要定期梳理毛发",
            "diet_needs": "高质量猫粮",
            "health_issues": "视网膜萎缩",
            "exercise_needs": "高",
            "size": "中型",
            "lifespan": "12-16年"
        }
    ],
    "timestamp": 1700000000
}
```

### 3.4 获取品种详情

获取指定品种的详细信息。

**请求**

```http
GET /api/v1/breeds/{breed_id}
Authorization: Bearer <token>
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| breed_id | integer | 是 | 品种 ID |

**响应示例**

```json
{
    "code": "200",
    "message": "success",
    "data": {
        "id": 1,
        "name": "孟加拉豹猫",
        "name_en": "Bengal",
        "category_id": 2,
        "image": "data:image/jpeg;base64,/9j/4AAQ...",
        "description": "孟加拉豹猫是一种...",
        "origin": "美国",
        "personality": "活泼、好奇",
        "care_tips": "需要定期梳理毛发",
        "diet_needs": "高质量猫粮",
        "health_issues": "视网膜萎缩",
        "exercise_needs": "高",
        "size": "中型",
        "lifespan": "12-16年"
    },
    "timestamp": 1700000000
}
```

### 3.5 按英文名获取品种

通过英文名获取品种信息。

**请求**

```http
GET /api/v1/breeds/by-name/Bengal
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name_en | string | 是 | 品种英文名 |

**响应示例**

```json
{
    "code": "200",
    "message": "success",
    "data": {
        "id": 1,
        "name": "孟加拉豹猫",
        "name_en": "Bengal",
        "category_id": 2,
        "image": "data:image/jpeg;base64,/9j/4AAQ...",
        "description": "孟加拉豹猫是一种..."
    },
    "timestamp": 1700000000
}
```

### 3.6 创建分类

创建新的宠物分类（仅管理员）。

**请求**

```http
POST /api/v1/categories
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**

```json
{
    "name": "新分类",
    "name_en": "new_category",
    "parent_id": 1,
    "icon": "icon_url"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 分类名称 |
| name_en | string | 否 | 英文名称 |
| parent_id | integer | 否 | 父分类 ID |
| icon | string | 否 | 图标 URL |

**响应示例**

```json
{
    "code": "201",
    "message": "分类创建成功",
    "data": {
        "id": 10,
        "name": "新分类",
        "name_en": "new_category",
        "parent_id": 1,
        "icon": "icon_url",
        "sort_order": 0
    },
    "timestamp": 1700000000
}
```

### 3.7 创建品种

创建新的宠物品种（仅管理员）。

**请求**

```http
POST /api/v1/breeds
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**

```json
{
    "name": "新品种",
    "name_en": "NewBreed",
    "category_id": 2,
    "image_base64": "base64_encoded_image",
    "description": "品种描述",
    "origin": "产地",
    "personality": "性格特点",
    "care_tips": "护理建议",
    "diet_needs": "饮食需求",
    "health_issues": "健康问题",
    "exercise_needs": "运动需求",
    "size": "体型",
    "lifespan": "寿命"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 品种名称 |
| name_en | string | 是 | 英文名称 |
| category_id | integer | 是 | 分类 ID |
| image_base64 | string | 否 | 品种图片（Base64） |
| description | string | 否 | 描述 |
| origin | string | 否 | 产地 |
| personality | string | 否 | 性格 |
| care_tips | string | 否 | 护理建议 |
| diet_needs | string | 否 | 饮食需求 |
| health_issues | string | 否 | 健康问题 |
| exercise_needs | string | 否 | 运动需求 |
| size | string | 否 | 体型 |
| lifespan | string | 否 | 寿命 |

**响应示例**

```json
{
    "code": "201",
    "message": "品种创建成功",
    "data": {
        "id": 20,
        "name": "新品种",
        "name_en": "NewBreed",
        "category_id": 2,
        "image": "data:image/jpeg;base64,/9j/4AAQ...",
        "description": "品种描述"
    },
    "timestamp": 1700000000
}
```

### 3.8 更新品种

更新宠物品种信息（仅管理员）。

**请求**

```http
PUT /api/v1/breeds/{breed_id}
Authorization: Bearer <token>
Content-Type: application/json
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| breed_id | integer | 是 | 品种 ID |

**请求体**

```json
{
    "name": "更新后的名称",
    "description": "更新后的描述"
}
```

**响应示例**

```json
{
    "code": "200",
    "message": "品种更新成功",
    "data": {
        "id": 20,
        "name": "更新后的名称",
        "name_en": "NewBreed",
        "category_id": 2,
        "description": "更新后的描述"
    },
    "timestamp": 1700000000
}
```

---

## 4. 预测接口 (Predict)

### 4.1 上传图片/视频进行识别

上传图片或视频文件进行宠物品种识别。

**请求**

```http
POST /api/v1/predict
Content-Type: multipart/form-data
```

**请求体 (Form Data)**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 图片或视频文件 |

**支持的图片格式**: jpg, jpeg, png, bmp
**支持的视频格式**: mp4, avi, mov, mkv, webm

**响应示例（图片识别）**

```json
{
    "code": "200",
    "message": "识别成功",
    "data": {
        "type": "image",
        "results": [
            {
                "label": "Bengal",
                "confidence": 0.95,
                "bbox": [100.5, 50.2, 300.8, 250.3]
            }
        ],
        "image_url": "http://127.0.0.1:8000/static/results/res_xxx.jpg"
    },
    "timestamp": 1700000000
}
```

**响应示例（视频识别）**

```json
{
    "code": "200",
    "message": "视频识别完成",
    "data": {
        "type": "video",
        "results": [
            {"label": "Bengal", "count": 15},
            {"label": "Pug", "count": 8}
        ],
        "video_url": "http://127.0.0.1:8000/static/results/res_xxx.mp4",
        "total_frames": 300
    },
    "timestamp": 1700000000
}
```

**结果字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 识别类型 (image/video) |
| results | array | 识别结果列表 |
| results[].label | string | 宠物品种名称 |
| results[].confidence | float | 置信度（图片识别） |
| results[].bbox | array | 边界框坐标 [x1, y1, x2, y2] |
| results[].count | int | 出现次数（视频识别） |
| image_url | string | 标注后的图片 URL |
| video_url | string | 标注后的视频 URL |
| total_frames | int | 视频总帧数 |

---

## 5. 上传接口 (Upload)

### 5.1 上传图片

上传 Base64 编码的图片文件。

**请求**

```http
POST /api/v1/upload/image
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**

```json
{
    "image": "base64_encoded_image_data",
    "filename": "image.jpg"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| image | string | 是 | Base64 编码的图片数据 |
| filename | string | 否 | 文件名 |

**响应示例**

```json
{
    "code": "200",
    "message": "图片上传成功",
    "data": {
        "url": "data:image/jpeg;base64,/9j/4AAQ...",
        "data": "base64_encoded_image_data",
        "filename": "image.jpg"
    },
    "timestamp": 1700000000
}
```

---

## 6. 管理员接口 (Admin)

### 6.1 获取用户列表

获取所有用户列表（仅管理员）。

**请求**

```http
GET /api/v1/users?skip=0&limit=100&username=admin
Authorization: Bearer <admin_token>
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | integer | 否 | 跳过记录数（分页） |
| limit | integer | 否 | 返回记录数（分页） |
| username | string | 否 | 用户名搜索关键词 |

**响应示例**

```json
{
    "code": "200",
    "message": "success",
    "data": [
        {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "nickname": "管理员",
            "avatar": "base64_encoded_image...",
            "role": "admin",
            "is_verified": true,
            "created_at": "2024-01-01T00:00:00",
            "last_login": "2024-01-15T10:30:00"
        }
    ],
    "timestamp": 1700000000
}
```

### 6.2 创建用户

创建新用户（仅管理员）。

**请求**

```http
POST /api/v1/users
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**请求体**

```json
{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "password123",
    "role": "user"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| email | string | 否 | 邮箱 |
| password | string | 是 | 密码 |
| role | string | 否 | 角色 (admin/user) |

**响应示例**

```json
{
    "code": "201",
    "message": "用户创建成功",
    "data": {
        "id": 5,
        "username": "newuser",
        "email": "newuser@example.com",
        "role": "user"
    },
    "timestamp": 1700000000
}
```

### 6.3 更新用户

更新指定用户信息（仅管理员）。

**请求**

```http
PUT /api/v1/users/{user_id}
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 是 | 用户 ID |

**请求体**

```json
{
    "email": "updated@example.com",
    "role": "admin",
    "password": "newpassword",
    "nickname": "新昵称"
}
```

**响应示例**

```json
{
    "code": "200",
    "message": "用户更新成功",
    "data": {
        "id": 5,
        "username": "newuser",
        "email": "updated@example.com",
        "nickname": "新昵称",
        "avatar": null,
        "role": "admin"
    },
    "timestamp": 1700000000
}
```

### 6.4 删除用户

删除指定用户（仅管理员）。

**请求**

```http
DELETE /api/v1/users/{user_id}
Authorization: Bearer <admin_token>
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 是 | 用户 ID |

**响应示例**

```json
{
    "code": "200",
    "message": "用户删除成功",
    "data": null,
    "timestamp": 1700000000
}
```

---

## 7. 错误响应示例

### 7.1 400 错误 - 请求参数错误

```json
{
    "code": "400",
    "message": "验证码错误，请重新输入",
    "data": null,
    "timestamp": 1700000000
}
```

### 7.2 401 错误 - 未授权

```json
{
    "code": "401",
    "message": "未授权，请先登录",
    "data": null,
    "timestamp": 1700000000
}
```

### 7.3 403 错误 - 权限不足

```json
{
    "code": "403",
    "message": "权限不足，需要管理员权限",
    "data": null,
    "timestamp": 1700000000
}
```

### 7.4 404 错误 - 资源不存在

```json
{
    "code": "404",
    "message": "品种不存在",
    "data": null,
    "timestamp": 1700000000
}
```

---

## 8. 代码示例

### 8.1 Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# 登录获取 token
def login(username, password):
    response = requests.post(
        f"{BASE_URL}/api/v1/login",
        json={
            "username": username,
            "password": password,
            "captcha_key": "",
            "captcha_code": ""
        }
    )
    return response.json()["data"]["access_token"]

# 获取用户信息
def get_profile(token):
    response = requests.get(
        f"{BASE_URL}/api/v1/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

# 上传图片进行识别
def predict(token, image_path):
    with open(image_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/api/v1/predict",
            files={"file": f},
            headers={"Authorization": f"Bearer {token}"}
        )
    return response.json()

# 使用示例
token = login("admin", "admin")
profile = get_profile(token)
print(profile)
```

### 8.2 JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:8000";

// 登录获取 token
async function login(username, password) {
    const response = await fetch(`${BASE_URL}/api/v1/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            username,
            password,
            captcha_key: "",
            captcha_code: ""
        })
    });
    const data = await response.json();
    return data.data.access_token;
}

// 获取用户信息
async function getProfile(token) {
    const response = await fetch(`${BASE_URL}/api/v1/me`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return await response.json();
}

// 上传图片进行识别
async function predict(token, file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${BASE_URL}/api/v1/predict`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
    });
    return await response.json();
}

// 使用示例
login("admin", "admin").then(token => {
    getProfile(token).then(console.log);
});
```

### 8.3 cURL

```bash
# 登录
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin","captcha_key":"","captcha_code":""}'

# 获取用户信息
curl -X GET http://localhost:8000/api/v1/me \
  -H "Authorization: Bearer <token>"

# 上传图片识别
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/image.jpg"
```

---

## 9. 接口权限一览表

| 接口 | 需要认证 | 需要管理员权限 |
|------|----------|----------------|
| GET /captcha | 否 | 否 |
| GET /captcha/{key} | 否 | 否 |
| POST /send-email-code | 否 | 否 |
| POST /verify-email-code | 否 | 否 |
| POST /register | 否 | 否 |
| POST /login | 否 | 否 |
| GET /me | 是 | 否 |
| GET /profile | 是 | 否 |
| PUT /profile | 是 | 否 |
| GET /avatar/{user_id} | 是 | 否 |
| GET /categories | 是 | 否 |
| GET /categories/{id}/children | 是 | 否 |
| GET /breeds | 是 | 否 |
| GET /breeds/{id} | 是 | 否 |
| GET /breeds/by-name/{name} | 是 | 否 |
| POST /categories | 是 | 是 |
| POST /breeds | 是 | 是 |
| PUT /breeds/{id} | 是 | 是 |
| POST /predict | 是 | 否 |
| POST /upload/image | 是 | 否 |
| GET /users | 是 | 是 |
| POST /users | 是 | 是 |
| PUT /users/{id} | 是 | 是 |
| DELETE /users/{id} | 是 | 是 |