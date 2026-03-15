#!/usr/bin/env python3
"""
スレッド実行例: MurataReceiver.run_in_thread()

村田センサーからのUDPパケットを受信しつつ、メインスレッドでは別の処理を継続する。
受信は run_in_thread() で別スレッドで実行する。標準ライブラリのみ使用。

実行方法:
    python examples/threaded_receiver.py

停止方法:
    Ctrl+C
"""

import time

from murata_sensor import MurataReceiver

# 受信ポート（環境に合わせて変更）
PORT = 55039


def on_data(sensor_data: dict, addr: tuple) -> None:
    """受信したセンサーデータを表示するコールバック"""
    print(f"[受信] {addr[0]}:{addr[1]} - {sensor_data['sensor_type']}: {sensor_data['values']}")


def main() -> None:
    receiver = MurataReceiver(port=PORT, data_callback=on_data)
    thread = receiver.run_in_thread(daemon=True)

    print(f"受信を開始しました (port={PORT})。メインスレッドでは5秒ごとにメッセージを表示します。Ctrl+C で終了。")

    try:
        count = 0
        while True:
            count += 1
            print(f"メイン処理実行中... ({count}回目)")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n終了しました。")


if __name__ == "__main__":
    main()
