"""日志模块"""
import logging
import sys
from datetime import datetime

# 创建日志记录器
logger = logging.getLogger("feishu_adapter")
logger.setLevel(logging.DEBUG)

# 控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# 日志格式
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)

# 添加处理器
logger.addHandler(console_handler)

# 为 maim_message 库创建专用 logger
custom_logger = logging.getLogger("maim_message")
custom_logger.setLevel(logging.INFO)
custom_logger.addHandler(console_handler)
