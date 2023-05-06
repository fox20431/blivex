import asyncio
import aiohttp
import json
import struct
import enum
import collections
import brotli
import config
from logger import get_logger

logger = get_logger(__name__)

# bussness data structure
HeaderTuple = collections.namedtuple('HeaderTuple', ('packet_len', 'header_len', 'ver', 'op', 'seq_id'))
header_struct = struct.Struct('>I2H2I')

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
        # 'roomid': 10341336,
        'roomid': config.room_id,
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

async def handle_ws_msg(ws: aiohttp.ClientWebSocketResponse, queue: asyncio.Queue):
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
                await queue.put(text)


async def fetch(queue: asyncio.Queue):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('wss://broadcastlv.chat.bilibili.com/sub') as ws:
            await send_auth(ws)
            heartbeat_task = asyncio.create_task(send_heartbeat(ws))
            parse_ws_msg_task = asyncio.create_task(handle_ws_msg(ws, queue=queue))
            await asyncio.gather(heartbeat_task, parse_ws_msg_task)
