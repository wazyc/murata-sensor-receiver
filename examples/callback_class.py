#!/usr/bin/env python3
"""
コールバックパターン: クラスのメソッド

クラスを使って状態と追加データを管理し、メソッドをコールバックとして使用します。

利点:
    - 状態管理が容易
    - 複数のコールバック（data/error）を整理できる
    - リソースのクリーンアップが明確

実行方法:
    python examples/callback_class.py

停止方法:
    Ctrl+C
"""

import sqlite3
from datetime import datetime

from murata_sensor import MurataReceiver


class SensorHandler:
    """センサーデータを処理するハンドラークラス"""
    
    def __init__(self, db_path: str, prefix: str = "[SENSOR]"):
        """
        Args:
            db_path: データベースファイルパス
            prefix: ログ出力の接頭辞
        """
        self.db_path = db_path
        self.prefix = prefix
        self.count = 0
        self.conn = sqlite3.connect(db_path)
        self.start_time = datetime.now()
    
    def on_data(self, sensor_data: dict, addr: tuple) -> None:
        """
        データコールバック
        
        self を通じて追加データ（conn, prefix, count）にアクセス
        """
        self.count += 1
        print(f"{self.prefix} #{self.count}: {sensor_data['sensor_type']}")
        print(f"  送信元: {addr[0]}:{addr[1]}")
        print(f"  RSSI: {sensor_data['info'].get('RSSI')} dBm")
    
    def on_error(self, error: Exception, raw_data: bytes, addr: tuple) -> None:
        """エラーコールバック"""
        print(f"{self.prefix} エラー: {error}")
        print(f"  送信元: {addr[0]}:{addr[1]}")
    
    def get_stats(self) -> dict:
        """統計情報を取得"""
        elapsed = datetime.now() - self.start_time
        return {
            "count": self.count,
            "elapsed_seconds": elapsed.total_seconds(),
        }
    
    def close(self) -> None:
        """リソースのクリーンアップ"""
        self.conn.close()
        stats = self.get_stats()
        print(f"{self.prefix} 終了")
        print(f"  処理件数: {stats['count']}")
        print(f"  稼働時間: {stats['elapsed_seconds']:.1f}秒")


def main():
    # ハンドラーを作成
    handler = SensorHandler(
        db_path=":memory:",
        prefix="[FACTORY-A]"
    )
    
    # メソッドをコールバックとして渡す
    receiver = MurataReceiver(
        port=55039,
        data_callback=handler.on_data,
        error_callback=handler.on_error
    )
    
    print("センサーデータを受信中... (Ctrl+Cで停止)")
    print()
    
    try:
        receiver.recv()
    except KeyboardInterrupt:
        print()
        handler.close()


if __name__ == "__main__":
    main()
