#!/usr/bin/env python3
"""
コールバックパターン: ラムダ式

ラムダ式を使って簡潔に追加の値を渡します。

利点:
    - 1行で書ける
    - 簡単な場合に最適

注意:
    - 複雑な処理には向かない
    - デバッグが難しくなる場合がある

実行方法:
    python examples/callback_lambda.py

停止方法:
    Ctrl+C
"""

from murata_sensor import MurataReceiver


def save_with_tag(sensor_data: dict, addr: tuple, tag: str) -> None:
    """タグ付きでセンサーデータを処理する関数"""
    print(f"[{tag}] {sensor_data['sensor_type']}")
    print(f"  送信元: {addr[0]}:{addr[1]}")
    print(f"  RSSI: {sensor_data['info'].get('RSSI')} dBm")


def main():
    # 追加の値を定義
    tag = "PRODUCTION"
    threshold = -60
    
    # ラムダ式で追加の値を渡す
    receiver = MurataReceiver(
        port=55039,
        data_callback=lambda data, addr: save_with_tag(data, addr, tag)
    )
    
    print("センサーデータを受信中... (Ctrl+Cで停止)")
    print(f"タグ: {tag}")
    print()
    
    try:
        receiver.recv()
    except KeyboardInterrupt:
        print("\n終了しました")


# より複雑な例: 複数の値を渡す
def main_complex():
    """複数の値を渡す例"""
    config = {
        "tag": "FACTORY-B",
        "threshold": -50,
        "debug": True
    }
    
    def process(data, addr):
        rssi = data["info"].get("RSSI", 0)
        status = "OK" if rssi >= config["threshold"] else "WARNING"
        print(f"[{config['tag']}] {status}: {data['sensor_type']}")
    
    receiver = MurataReceiver(
        port=55039,
        data_callback=lambda data, addr: process(data, addr)
    )
    
    print("センサーデータを受信中... (Ctrl+Cで停止)")
    try:
        receiver.recv()
    except KeyboardInterrupt:
        print("\n終了しました")


if __name__ == "__main__":
    main()
