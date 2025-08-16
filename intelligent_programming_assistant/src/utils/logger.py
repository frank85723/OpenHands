"""日志工具"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from .config_loader import config


def setup_logger(
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    max_file_size: str = "10MB",
    backup_count: int = 5
) -> None:
    """设置日志系统"""
    
    # 移除默认的日志处理器
    logger.remove()
    
    # 从配置文件获取日志设置
    logging_config = config.get('logging', {})
    
    log_level = log_level or logging_config.get('level', 'INFO')
    log_file = log_file or logging_config.get('file', 'logs/assistant.log')
    max_file_size = max_file_size or logging_config.get('max_file_size', '10MB')
    backup_count = backup_count or logging_config.get('backup_count', 5)
    log_format = logging_config.get(
        'format', 
        "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=log_level,
        format=log_format,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 添加文件输出
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level=log_level,
            format=log_format,
            rotation=max_file_size,
            retention=backup_count,
            compression="zip",
            backtrace=True,
            diagnose=True
        )
    
    logger.info(f"日志系统初始化完成 - 级别: {log_level}, 文件: {log_file}")


def get_logger(name: str):
    """获取指定名称的日志器"""
    return logger.bind(name=name)


# 初始化默认日志系统
setup_logger()