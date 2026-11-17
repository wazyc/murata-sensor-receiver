#!/usr/bin/env python3
"""
UDP受信と FastAPI によるデータ提供を同時に行う簡易サンプル

別スレッドで UDP を受信し、最新のセンサーデータを HTTP で返す。
より本格的な非同期版は examples/async_fastapi_receiver.py を参照する

必要なパッケージ（本サンプルのみ）:
    pip install fastapi uvicorn

実行方法:
    python examples/fastapi_receiver.py

確認方法:
    curl http://127.0.0.1:8000/latest

停止方法:
    Ctrl+C
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI

from murata_sensor import MurataReceiver

# 受信ポート（環境に合わせて変更）
UDP_PORT = 55039
# HTTP ポート
HTTP_PORT = 8000

# 最新の受信データ（未受信なら None）
latest: Optional[Dict[str, Any]] = None

app = FastAPI()


def on_data(sensor_data: dict, addr: tuple) -> None:
    """受信したセンサーデータを最新値として保持する"""
    global latest
    latest = {"addr": list(addr), "sensor_data": sensor_data}


@app.get("/latest")
def get_latest() -> Optional[Dict[str, Any]]:
    """最新のセンサーデータを返す。未受信なら null"""
    return latest


def main() -> None:
    import uvicorn

    receiver = MurataReceiver(port=UDP_PORT, data_callback=on_data)
    receiver.run_in_thread(daemon=True)

    print(
        f"UDP受信中 (port={UDP_PORT})。"
        f"最新データ: http://127.0.0.1:{HTTP_PORT}/latest"
    )
    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT)


if __name__ == "__main__":
    main()
