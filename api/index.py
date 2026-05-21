import sys
import os

# 将 backend 目录添加到 Python 路径，以便导入工作
# 这里假设 root 是部署的基础目录
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
