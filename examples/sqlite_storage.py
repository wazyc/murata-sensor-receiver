#!/usr/bin/env python3
"""
SQLite保存例: UDP受信→SQLiteデータベース

村田センサーからのUDPパケットを受信し、SQLiteデータベースに保存します。

実行方法:
    python examples/sqlite_storage.py

停止方法:
    Ctrl+C

出力ファイル:
    sensor_data.db (カレントディレクトリに作成)
"""

import json
import sqlite3
from datetime import datetime

from murata_sensor import MurataReceiver

# データベースファイルパス
DB_PATH = "sensor_data.db"


def init_database() -> None:
    """データベースとテーブルを初期化"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                source_port INTEGER NOT NULL,
                sensor_type TEXT NOT NULL,
                unit_id TEXT,
                rssi INTEGER,
                values_json TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON sensor_readings(timestamp)
        """)


def on_data(sensor_data: dict, addr: tuple) -> None:
    """センサーデータをSQLiteに保存"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO sensor_readings 
            (timestamp, source_ip, source_port, sensor_type, unit_id, rssi, values_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                addr[0],
                addr[1],
                sensor_data["sensor_type"],
                sensor_data["info"].get("unit_id"),
                sensor_data["info"].get("RSSI"),
                json.dumps(sensor_data["values"], ensure_ascii=False),
            ),
        )

    print(f"保存: {sensor_data['sensor_type']} from {addr[0]}")


def main():
    # データベース初期化
    init_database()
    print(f"データベース: {DB_PATH}")

    # レシーバー開始
    receiver = MurataReceiver(port=55039, data_callback=on_data)

    print("センサーデータを受信中... (Ctrl+Cで停止)")
    try:
        receiver.recv()
    except KeyboardInterrupt:
        # 保存件数を表示
        with sqlite3.connect(DB_PATH) as conn:
            count = conn.execute("SELECT COUNT(*) FROM sensor_readings").fetchone()[0]
        print(f"\n終了しました (保存件数: {count})")


if __name__ == "__main__":
    main()
