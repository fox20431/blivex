__all__ = ['log_danmaku']

import asyncio
import enum
import json
from utils.logger import get_logger

logger = get_logger(__name__)

class CMD(str, enum.Enum):
    # 直播间改变
    ROOM_CHANGE = "ROOM_CHANGE"
    # 推流提示
    LIVE = "LIVE"
    # 弹幕信息
    DANMU_MSG = "DANMU_MSG"
    # 用户进入直播间
    INTERACT_WORD = "INTERACT_WORD"

# 全局变量：存放从网络请求到的弹幕数据
async def log_danmaku(queue: asyncio.Queue):
    while True:
        text = await queue.get()
        obj = json.loads(text)
        logger.info(obj)