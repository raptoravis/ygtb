import argparse
import os
from typing import List


def list_subdirectories(parent_dir: str) -> List[str]:
    """
    列出指定目录下的所有子目录
    
    Args:
        parent_dir: 需要扫描的父目录路径
        
    Returns:
        子目录名称列表
    """
    if not os.path.exists(parent_dir):
        print(f"错误: 路径 '{parent_dir}' 不存在。")
        return []
    
    if not os.path.isdir(parent_dir):
        print(f"错误: '{parent_dir}' 不是一个文件夹。")
        return []

    # 获取所有子目录
    subdirs = [
        name for name in os.listdir(parent_dir)
        if os.path.isdir(os.path.join(parent_dir, name))
    ]
    
    return subdirs


def main():
    parser = argparse.ArgumentParser(description="输出指定文件夹里的子目录名字")
    parser.add_argument("directory", type=str, help="目标文件夹路径")
    
    args = parser.parse_args()
    
    target_dir = args.directory
    subdirs = list_subdirectories(target_dir)
    print(subdirs)


if __name__ == "__main__":
    main()
