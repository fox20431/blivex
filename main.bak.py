import asyncio
import aiohttp
import json
import struct
import enum
import collections
import logging
import brotli
import pyttsx3
from pydub import AudioSegment
import pyaudio
import sys
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow

# logging init
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# bussness data structure
HeaderTuple = collections.namedtuple('HeaderTuple', ('packet_len', 'header_len', 'ver', 'op', 'seq_id'))
header_struct = struct.Struct('>I2H2I')

# pyttsx3 init
engine = pyttsx3.init() # object creation
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_ZH-CN_HUIHUI_11.0') 

# prepare the audio

niganma_audio_file = AudioSegment.from_file(r"C:\Users\ming\projects\blivex\assets\niganma.mp3", format="mp3")
niganma_audio_data = niganma_audio_file.raw_data
# 初始化音频流对象
niganma_audio_stream = pyaudio.PyAudio().open(
    format=pyaudio.paInt16,
    channels=niganma_audio_file.channels,
    rate=niganma_audio_file.frame_rate,
    output=True
)

class ProtoVer(enum.IntEnum):
    NORMAL = 0
    HEARTBEAT = 1
    DEFLATE = 2
    BROTLI = 3

# ref: https://open-live.bilibili.com/document/doc&tool/api/websocket.html#_2-%E5%8F%91%E9%80%81%E5%BF%83%E8%B7%B3
class OP(enum.IntEnum):
    HEARTBEAT = 2
    HEARTBEAT_REPLY = 3
    SEND_SMS_REPLY = 5
    AUTH = 7
    AUTH_REPLY = 8

class CMD(str, enum.Enum):
    # 直播间改变
    ROOM_CHANGE = "ROOM_CHANGE"
    # 推流提示
    LIVE = "LIVE"
    # 弹幕信息
    DANMU_MSG = "DANMU_MSG"
    # 用户进入直播间
    INTERACT_WORD = "INTERACT_WORD"

def make_packet(data: dict, operation: int):
    body = json.dumps(data).encode('UTF-8')
    header = header_struct.pack(*HeaderTuple(
        packet_len=header_struct.size + len(body),
        header_len=header_struct.size,
        ver=1,
        op=operation,
        seq_id=1
    ))
    return header + body

async def send_auth(ws: aiohttp.ClientWebSocketResponse):
    auth_params = {
        'uid': 0,
        'roomid': 10341336,
        'protover': 3,
        'platform': 'web',
        'type': 2
    }
    await ws.send_bytes(make_packet(auth_params, OP.AUTH))

async def send_heartbeat(ws: aiohttp.ClientWebSocketResponse):
    while True:
        await asyncio.sleep(30)
        await ws.send_bytes(make_packet({},OP.HEARTBEAT))

async def parse_msg_reply(header: HeaderTuple, body: bytes):
    print()

async def handle_ws_msg(ws: aiohttp.ClientWebSocketResponse):
    async for msg in ws:
        header = HeaderTuple(*header_struct.unpack_from(msg.data, 0))
        # print(header)
        if header.op == OP.SEND_SMS_REPLY:
            body = msg.data[header.header_len: header.packet_len]
            if header.ver == ProtoVer.BROTLI:
                # 该消息为完整包被压缩后再加上头，所以需要去头解压再去头才能得到真实信息
                decoded_packet = brotli.decompress(body)
                decoded_packet_header = HeaderTuple(*header_struct.unpack_from(decoded_packet, 0))
                data = decoded_packet[decoded_packet_header.header_len: decoded_packet_header.packet_len]
                text = data.decode('utf-8')
                danmu_msg_obj = json.loads(text)
                logger.info(danmu_msg_obj)
                # danmu_msg_json = json.dumps(danmu_msg_obj)
                # print(danmu_msg_json)

                # 弹幕信息
                if danmu_msg_obj['cmd'] == CMD.DANMU_MSG:
                    danmu_msg_text = danmu_msg_obj['info'][1]
                    danmu_msg_user = danmu_msg_obj['info'][2][1]
                    # print(danmu_msg)
                    engine.say(f"{danmu_msg_user}说：{danmu_msg_text}")
                    if '干嘛' in danmu_msg_text:
                        niganma_audio_stream.write(niganma_audio_data)
                    engine.runAndWait()
                    engine.stop()

                # 进入直播间
                if danmu_msg_obj['cmd'] == CMD.INTERACT_WORD:
                    interact_word_uname = danmu_msg_obj['data']['uname']
                    # print(danmu_msg)
                    engine.say(f"欢迎{interact_word_uname}进入直播间")
                    engine.runAndWait()
                    engine.stop()

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('wss://broadcastlv.chat.bilibili.com/sub') as ws:
            await send_auth(ws)
            heartbeat_task = asyncio.create_task(send_heartbeat(ws))
            parse_ws_msg_task = asyncio.create_task(handle_ws_msg(ws))
            await asyncio.gather(heartbeat_task, parse_ws_msg_task)

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # `asyncio.run(main())` will block the event loop, so we need to run it in another thread
        self.thread = threading.Thread(target=asyncio.run, args=(main(),))
        self.thread.start()

        # Set window title and size
        self.setWindowTitle("My Window")
        self.setGeometry(100, 100, 640, 480)
        
        # Show the window
        self.show()
    
    def closeEvent(self, event):
        self.thread._stop()
        event.accept()

    async def wait_for_tasks(self):
        tasks = asyncio.all_tasks()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        asyncio.get_running_loop().stop()

if __name__ == '__main__':
    # Create a new QApplication instance
    app = QApplication(sys.argv)

    # Create a new instance of the main window
    window = MyWindow()


    niganma_audio_stream.close()
    sys.exit(app.exec())
