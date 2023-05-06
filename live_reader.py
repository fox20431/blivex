import asyncio
import logging
import time
from typing import Optional
import pyttsx3


# logging init
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# pyttsx3 init
engine = pyttsx3.init() # object creation
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_ZH-CN_HUIHUI_11.0') 

# 全局变量：存放从网络请求到的弹幕数据
async def read_danmaku(queue: asyncio.Queue):
    while True:
        logger.info("read_danmaku() is running")
        danmaku_text = await queue.get()
        logger.info(f"danmaku_text: {danmaku_text}")
        engine.say(f"{danmaku_text}")
        engine.runAndWait()
        engine.stop()
