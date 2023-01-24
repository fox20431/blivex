import asyncio
import aiohttp
import json
import struct
import enum
import collections
import logging
import brotli
import pyttsx3

HeaderTuple = collections.namedtuple('HeaderTuple', ('packet_len', 'header_len', 'ver', 'op', 'seq_id'))
header_struct = struct.Struct('>I2H2I')

engine = pyttsx3.init() # object creation
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_ZH-CN_HUIHUI_11.0') 


class ProtoVer(enum.IntEnum):
    NORMAL = 0
    HEARTBEAT = 1
    DEFLATE = 2
    BROTLI = 3

class CMD(enum.IntEnum):
    HANDSHAKE = 0
    HANDSHAKE_REPLY = 1
    HEARTBEAT = 2
    HEARTBEAT_REPLY = 3
    SEND_MSG = 4
    DANMU_MSG = 5 # 弹幕
    DISCONNECT_REPLY = 6
    AUTH = 7
    AUTH_REPLY = 8
    RAW = 9
    PROTO_READY = 10
    PROTO_FINISH = 11
    CHANGE_ROOM = 12
    CHANGE_ROOM_REPLY = 13
    REGISTER = 14
    REGISTER_REPLY = 15
    UNREGISTER = 16
    UNREGISTER_REPLY = 17
    # B站业务自定义OP
    # MinBusinessOp = 1000
    # MaxBusinessOp = 10000

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
    await ws.send_bytes(make_packet(auth_params, CMD.AUTH))

async def send_heartbeat(ws: aiohttp.ClientWebSocketResponse):
    while True:
        await asyncio.sleep(30)
        await ws.send_bytes(make_packet({},CMD.HEARTBEAT))

async def parse_msg_reply(header: HeaderTuple, body: bytes):
    print()

async def handle_ws_msg(ws: aiohttp.ClientWebSocketResponse):
    async for msg in ws:
        # offset = 0
        header = HeaderTuple(*header_struct.unpack_from(msg.data, 0))
        print(header)
        if header.op == CMD.DANMU_MSG:
            body = msg.data[header.header_len: header.packet_len]
            if header.ver == ProtoVer.BROTLI:
                # 该消息为完整包被压缩后再加上头，所以需要去头解压再去头才能得到真实信息
                decoded_packet = brotli.decompress(body)
                decoded_packet_header = HeaderTuple(*header_struct.unpack_from(decoded_packet, 0))
                data = decoded_packet[decoded_packet_header.header_len: decoded_packet_header.packet_len]
                text = data.decode('utf-8')
                danmu_msg_obj = json.loads(text)
                # danmu_msg_json = json.dumps(danmu_msg_obj)
                # print(danmu_msg_json)
                danmu_msg_text = danmu_msg_obj['info'][1]
                danmu_msg_user = danmu_msg_obj['info'][2][1]
                # print(danmu_msg)
                engine.say(f"{danmu_msg_user}说：{danmu_msg_text}")
                engine.runAndWait()
                engine.stop()

            # body = json.loads(body.decode('utf-8'))
            # print(body)
            # parse_msg_reply(header, body)
            # print(header)
            # # 弹幕消息，存在数据量大被分包的情况
            # while True:
            #     # 切片，获取主干内容
            #     body = msg.data[offset + header.raw_header_size: offset + header.pack_len]
            #     await parse_msg_reply(header, body)
            #     offset += header.pack_len
            #     if offset >= len(msg.data):
            #         break
            #     header = HeaderTuple(*header_struct.unpack_from(msg.data, offset))

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('wss://broadcastlv.chat.bilibili.com/sub') as ws:
            await send_auth(ws)
            heartbeat_task = asyncio.create_task(send_heartbeat(ws))
            parse_ws_msg_task = asyncio.create_task(handle_ws_msg(ws))
            await asyncio.gather(heartbeat_task, parse_ws_msg_task)

if __name__ == '__main__':
    asyncio.run(main())