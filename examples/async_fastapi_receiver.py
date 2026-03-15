#!/usr/bin/env python3
"""
FastAPI と同時に裏でセンサーデータを受信し続けるサンプル

- FastAPI は HTTP API として動作（ヘルスチェック・最新センサー一覧など）
- バックグラウンドで AsyncMurataReceiver が UDP 受信を継続
- 受信データはメモリに保持し、API から参照可能

必要なパッケージ（本サンプルのみ）:
  pip install fastapi uvicorn

実行方法:
  uvicorn examples.async_fastapi_receiver:app --host 0.0.0.0 --port 8000

  ※ プロジェクトルートで実行するか、PYTHONPATH にプロジェクトを追加すること。
  または:
  cd /path/to/murata-sensor-receiver && uvicorn examples.async_fastapi_receiver:app --host 0.0.0.0 --port 8000

API 例:
  GET /health          - 稼働確認
  GET /sensors/latest  - 直近の受信データ一覧（送信元ごとに最新1件）
  GET /sensors/recent  - 直近 N 件の受信データ（デフォルト50件）
"""

import asyncio
from collections import deque
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI

from murata_sensor import AsyncMurataReceiver

# 受信ポート（環境に合わせて変更）
UDP_PORT = 55039
# 直近の受信件数を保持する上限
RECENT_MAXLEN = 500

# 送信元アドレスごとの最新1件（API 用）
latest_by_addr: Dict[tuple, Dict[str, Any]] = {}
# 直近の受信データ（新しい順、RECENT_MAXLEN 件まで）
recent_queue: deque = deque(maxlen=RECENT_MAXLEN)
# 受信タスク（lifespan で開始・停止）
_receiver_task: Any = None


async def _receive_loop(receiver: AsyncMurataReceiver) -> None:
    """バックグラウンドで受信し、latest_by_addr と recent_queue を更新する。"""
    try:
        async for sensor_data, addr in receiver:
            item = {"addr": list(addr), "sensor_data": sensor_data}
            latest_by_addr[addr] = item
            recent_queue.append(item)
    except asyncio.CancelledError:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時に受信を開始、終了時に受信を停止する。"""
    global _receiver_task
    receiver = AsyncMurataReceiver(port=UDP_PORT)
    await receiver.start()
    _receiver_task = asyncio.create_task(_receive_loop(receiver))
    yield
    _receiver_task.cancel()
    try:
        await _receiver_task
    except asyncio.CancelledError:
        pass
    await receiver.stop()


app = FastAPI(
    title="Murata Sensor Receiver API",
    description="裏で UDP 受信を続けつつ、HTTP API で最新データを取得するサンプル",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> Dict[str, str]:
    """稼働確認用。"""
    return {"status": "ok"}


@app.get("/sensors/latest")
async def sensors_latest() -> List[Dict[str, Any]]:
    """送信元アドレスごとの最新1件を返す。"""
    return list(latest_by_addr.values())


@app.get("/sensors/recent")
async def sensors_recent(limit: int = 50) -> List[Dict[str, Any]]:
    """直近の受信データを返す（新しい順）。limit は最大件数（デフォルト50、最大500）。"""
    if limit <= 0 or limit > RECENT_MAXLEN:
        limit = min(50, RECENT_MAXLEN)
    return list(recent_queue)[-limit:][::-1]


if __name__ == "__main__":
    import uvicorn
    # 直接実行時は app を渡す（uvicorn examples.async_fastapi_receiver:app でも可）
    uvicorn.run(app, host="0.0.0.0", port=8000)
