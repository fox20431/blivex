''' This module implements the websocket protocol for bilibili live danmaku.'''

__all__ = ['fetch']

import asyncio
import aiohttp
import enum
import brotli
import utils.config as config
from utils.logger import get_logger
from utils.packet import build, parse_header

logger = get_logger(__name__)


class Version(enum.IntEnum):
    DEFAULT = 0
    ZLIB = 2
    BROTLI = 3

class OP(enum.IntEnum):
    HEARTBEAT = 2
    HEARTBEAT_REPLY = 3
    SEND_SMS_REPLY = 5
    AUTH = 7
    AUTH_REPLY = 8

async def _send_auth(ws: aiohttp.ClientWebSocketResponse):
    auth_params = {
        'uid': 0,
        'roomid': config.room_id,
        'protover': 0,
        'platform': 'web',
        'type': 2
    }
    await ws.send_bytes(build(auth_params, OP.AUTH))

async def _send_heartbeat(ws: aiohttp.ClientWebSocketResponse):
    while True:
        await asyncio.sleep(30)
        await ws.send_bytes(build({},OP.HEARTBEAT))

async def _handle_ws_msg(ws: aiohttp.ClientWebSocketResponse, queue: asyncio.Queue):
    async for msg in ws:
        header = parse_header(msg.data)
        logger.info(f'header: {header}')
        if header.op == OP.SEND_SMS_REPLY and header.ver == Version.BROTLI:
            body = msg.data[header.header_len: header.packet_len]
            # 该消息为完整包被压缩后再加上头，所以需要去头解压再去头才能得到真实信息
            decoded_packet = brotli.decompress(body)
            decoded_packet_header = parse_header(decoded_packet)
            data = decoded_packet[decoded_packet_header.header_len: decoded_packet_header.packet_len]
            text = data.decode('utf-8')
            await queue.put(text)

async def fetch(queue: asyncio.Queue):
    """
    Fetch the live danmaku from bilibili live server, and result will be put into the queue.
    
    Args:
        queue: asyncio.Queue, the queue to put the danmaku into.
    """
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('wss://broadcastlv.chat.bilibili.com/sub') as ws:
        # async with session.ws_connect('wss://tx-bj-live-comet-03.chat.bilibili.com/sub') as ws:
            await _send_auth(ws)
            heartbeat_task = asyncio.create_task(_send_heartbeat(ws))
            parse_ws_msg_task = asyncio.create_task(_handle_ws_msg(ws, queue=queue))
            await asyncio.gather(heartbeat_task, parse_ws_msg_task)

