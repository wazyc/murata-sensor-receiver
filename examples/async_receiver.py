#!/usr/bin/env python3
"""
非同期受信の基本例: AsyncMurataReceiver と async for

村田センサーからのUDPパケットを非同期で受信し、async for でイテレートする。
標準ライブラリのみ使用（asyncio）。

実行方法:
    python examples/async_receiver.py

停止方法:
    Ctrl+C
"""

import asyncio

from murata_sensor import AsyncMurataReceiver

# 受信ポート（環境に合わせて変更）
PORT = 55039


async def main() -> None:
    receiver = AsyncMurataReceiver(port=PORT)
    await receiver.start()

    print(f"非同期受信を開始しました (port={PORT})。Ctrl+C で終了します。")

    try:
        async for sensor_data, addr in receiver:
            print(
                f"[{addr[0]}:{addr[1]}] "
                f"{sensor_data['sensor_type']}: {sensor_data['values']}"
            )
    except asyncio.CancelledError:
        pass
    finally:
        await receiver.stop()
        print("終了しました。")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n終了しました。")
