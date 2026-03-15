#!/usr/bin/env python3
"""
コールバックパターン: クロージャ（関数内関数）

クロージャを使って追加の値（DB接続、設定など）をコールバックに渡します。

利点:
    - シンプルで直感的
    - 外部変数を自然にキャプチャできる

実行方法:
    python examples/callback_closure.py

停止方法:
    Ctrl+C
"""

import sqlite3

from murata_sensor import MurataReceiver


def create_callback(db_path: str, threshold: int):
    """
    クロージャを使って追加の値をキャプチャしたコールバックを生成
    
    Args:
        db_path: データベースファイルパス
        threshold: RSSI警告閾値
    
    Returns:
        コールバック関数
    """
    conn = sqlite3.connect(db_path)
    count = [0]
    
    def on_data(sensor_data: dict, addr: tuple) -> None:
        count[0] += 1
        rssi = sensor_data["info"].get("RSSI", 0)
        
        # キャプチャした threshold を使用
        if rssi < threshold:
            print(f"[{count[0]}] 警告: RSSI={rssi} (閾値: {threshold})")
        else:
            print(f"[{count[0]}] OK: RSSI={rssi}")
        
        print(f"  センサー: {sensor_data['sensor_type']} from {addr[0]}")
    
    return on_data


def main():
    # クロージャでDB接続と閾値をキャプチャ
    callback = create_callback(
        db_path=":memory:",  # メモリ上のDB（テスト用）
        threshold=-50        # RSSI閾値
    )
    
    receiver = MurataReceiver(port=55039, data_callback=callback)
    
    print("センサーデータを受信中... (Ctrl+Cで停止)")
    print(f"RSSI閾値: -50 dBm")
    print()
    
    try:
        receiver.recv()
    except KeyboardInterrupt:
        print("\n終了しました")


if __name__ == "__main__":
    main()
