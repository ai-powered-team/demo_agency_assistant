"""
日志配置模块

提供统一的日志配置和记录功能。
"""

import logging
import os
from pathlib import Path
from util.config import config


def setup_logger() -> logging.Logger:
    """设置并返回日志记录器"""
    
    # 创建日志目录
    log_file_path = Path(config.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger("ai_insurance")
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# 全局日志记录器实例
logger = setup_logger()
