import asyncio
from core.fetch_live import fetch

from utils.logger import get_logger
from handlers.log_damaku import log_danmaku

logger = get_logger(__name__)

async def main():
    queue = asyncio.Queue()

    # 创建 asyncio 任务
    fetch_task = asyncio.create_task(fetch(queue=queue))
    # read_danmaku_task = asyncio.create_task(read_danmaku(queue=queue))
    log_danmaku_task = asyncio.create_task(log_danmaku(queue=queue))

    # 等待两个任务完成
    # await asyncio.gather(fetch_task, read_danmaku_task)
    await asyncio.gather(fetch_task, log_danmaku_task)

if __name__ == '__main__':
    asyncio.run(main())