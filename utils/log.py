import sys

from loguru import logger
import os

from app.core.config import log_dir


# 配置日志：按天归档到指定目录
def setup_loguru_logger():

    # 创建目录
    os.makedirs(log_dir, exist_ok=True)
    # 移除默认的控制台输出
    logger.remove()

    # 添加文件处理器：按天归档
    logger.add(
        f"{log_dir}/app.log",
        rotation="00:00",  # 每天午夜切割
        retention=7,  # 保留7天
        compression="zip",  # 压缩备份
        encoding="utf-8",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # 添加控制台输出
    logger.add(
        sink=sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    return logger


logger = setup_loguru_logger()
