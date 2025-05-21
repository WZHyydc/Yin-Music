"""
运行模型可视化的入口脚本
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sasrec.model.visualization import main

if __name__ == "__main__":
    main() 