#!/usr/bin/env python3
"""
FastAPI 后端项目启动脚本
确保正确的 Python 路径和模块导入
"""
import os
import sys
from pathlib import Path

# 获取当前脚本所在目录
current_dir = Path(__file__).parent
back_dir = current_dir / "system" / "back"

# 确保 back 目录在 Python 路径中
if str(back_dir) not in sys.path:
    sys.path.insert(0, str(back_dir))

# 切换到 back 目录
os.chdir(back_dir)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)