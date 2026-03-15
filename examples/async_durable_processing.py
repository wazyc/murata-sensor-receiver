#!/usr/bin/env python3
"""
長時間稼働・大量受信・重い後処理・欠損なし対応のサンプル

以下の要件に対応する構成例です。
- 長時間稼働: 受信と処理をキューで分離し、Ctrl+C まで継続
- 短時間に大量受信: 無制限キューでバッファし、受信側は捨てない
- 時間のかかる処理: ワーカーがキューから取り出して DB 書き込み等を実行（ブロックしない）
- データの欠損なし: キューに載せたデータはワーカーがすべて処理するまで待つ

標準ライブラリのみ使用（asyncio, sqlite3）。実行方法:
  python examples/async_durable_processing.py

停止: Ctrl+C（キューが空になるまで処理を待ってから終了）
"""

import asyncio
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Optional

from murata_sensor import AsyncMurataReceiver

PORT = 55039
DB_PATH = Path("sensor_data_durable.db")
# 重い処理を実行するスレッドプール（DB などブロッキング I/O 用）
executor = ThreadPoolExecutor(max_workers=2)

# 終了要求フラグ（Ctrl+C で立てる）
shutdown_requested = False


def init_db(db_path: Path) -> None:
    """SQLite テーブルを初期化する。"""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                source_port INTEGER NOT NULL,
                sensor_type TEXT NOT NULL,
                unit_id TEXT,
                rssi INTEGER,
                values_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_received_at ON sensor_readings(received_at)"
        )


def insert_sensor_reading(
    db_path: Path,
    received_at: str,
    source_ip: str,
    source_port: int,
    sensor_type: str,
    unit_id: Optional[str],
    rssi: Optional[int],
    values_json: str,
) -> None:
    """
    1 件のセンサーデータを DB に挿入する（ブロッキング）。
    ワーカーから run_in_executor で呼び出す想定。
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO sensor_readings
            (received_at, source_ip, source_port, sensor_type, unit_id, rssi, values_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (received_at, source_ip, source_port, sensor_type, unit_id, rssi, values_json),
        )


async def process_one(
    queue: asyncio.Queue,
    db_path: Path,
    loop: asyncio.AbstractEventLoop,
) -> None:
    """
    キューから 1 件取り出して DB に保存する。
    時間のかかる処理は run_in_executor で別スレッドで実行し、イベントループをブロックしない。
    """
    while True:
        try:
            item = await asyncio.wait_for(queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            if shutdown_requested:
                break
            continue
        if item is None:
            # 終了用 sentinel
            queue.task_done()
            break
        sensor_data, addr = item
        try:
            received_at = sensor_data.get("timestamp") or datetime.now().isoformat()
            info = sensor_data.get("info") or {}
            unit_id = info.get("unit_id")
            rssi = info.get("RSSI")
            values_json = json.dumps(sensor_data.get("values") or {}, ensure_ascii=False)
            await loop.run_in_executor(
                executor,
                insert_sensor_reading,
                db_path,
                received_at,
                addr[0],
                addr[1],
                sensor_data.get("sensor_type", ""),
                unit_id,
                rssi,
                values_json,
            )
        except Exception as e:
            print(f"保存エラー {addr}: {e}")
        finally:
            queue.task_done()


async def receive_into_queue(
    receiver: AsyncMurataReceiver,
    queue: asyncio.Queue,
) -> None:
    """受信データをキューに投入する。欠損を防ぐためキューは無制限。"""
    try:
        async for sensor_data, addr in receiver:
            if shutdown_requested:
                break
            await queue.put((sensor_data, addr))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"受信エラー: {e}")


async def main() -> None:
    global shutdown_requested
    init_db(DB_PATH)
    print(f"DB: {DB_PATH}")
    print("長時間稼働・大量受信・欠損なしのサンプル。Ctrl+C で終了（キュー消化後に終了）。")

    # 無制限キューで受信バースト時も欠損しない
    queue: asyncio.Queue = asyncio.Queue()
    receiver = AsyncMurataReceiver(port=PORT)
    await receiver.start()

    loop = asyncio.get_running_loop()
    consumer = asyncio.create_task(process_one(queue, DB_PATH, loop))
    producer = asyncio.create_task(receive_into_queue(receiver, queue))

    try:
        await asyncio.gather(producer, consumer)
    except asyncio.CancelledError:
        pass
    finally:
        shutdown_requested = True
        producer.cancel()
        try:
            await producer
        except asyncio.CancelledError:
            pass
        await receiver.stop()
        # ワーカーに終了を伝え、キュー残りを処理
        await queue.put(None)
        await asyncio.wait_for(consumer, timeout=30.0)
        consumer.cancel()
        try:
            await consumer
        except asyncio.CancelledError:
            pass

    executor.shutdown(wait=True)
    with sqlite3.connect(DB_PATH) as conn:
        n = conn.execute("SELECT COUNT(*) FROM sensor_readings").fetchone()[0]
    print(f"終了しました。保存件数: {n}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        shutdown_requested = True
        print("\n終了要求を送信しました。キューを処理してから終了します。")
