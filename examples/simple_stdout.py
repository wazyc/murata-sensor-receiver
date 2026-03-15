#!/usr/bin/env python3
"""
最もシンプルな使用例: UDP受信→標準出力

村田センサーからのUDPパケットを受信し、センサーデータを標準出力に表示します。

実行方法:
    python examples/simple_stdout.py

停止方法:
    Ctrl+C
"""

from murata_sensor import MurataReceiver


def on_data(sensor_data: dict, addr: tuple) -> None:
    """センサーデータ受信時のコールバック"""
    print(f"[{addr[0]}:{addr[1]}] {sensor_data['sensor_type']}")
    for key, value in sensor_data["values"].items():
        print(f"  {key}: {value['value']} {value['unit']}")
    print()


def main():
    # ポート55039でUDP受信を開始
    receiver = MurataReceiver(port=55039, data_callback=on_data)

    print("センサーデータを受信中... (Ctrl+Cで停止)")
    try:
        receiver.recv()
    except KeyboardInterrupt:
        print("\n終了しました")


if __name__ == "__main__":
    main()
