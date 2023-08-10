import asyncio
import enum
import json
import pyttsx3
from utils.logger import get_logger

logger = get_logger(__name__)

# pyttsx3 init
engine = pyttsx3.init() # object creation
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_ZH-CN_HUIHUI_11.0') 

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
async def read_danmaku(queue: asyncio.Queue):
    while True:
        text = await queue.get()
        obj = json.loads(text)
        logger.info(obj)
        # danmaku_msg_json = json.dumps(danmaku_msg_obj)
        # print(danmaku_msg_json)

        # 弹幕信息
        if obj['cmd'] == CMD.DANMU_MSG:
            danmaku_text = obj['info'][1]
            danmaku_user = obj['info'][2][1]
            engine.say(f"{danmaku_text}")
            engine.runAndWait()
            engine.stop()

        # 进入直播间
        if obj['cmd'] == CMD.INTERACT_WORD:
            interact_word_uname = obj['data']['uname']
            # print(danmaku_msg)
