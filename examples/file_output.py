#!/usr/bin/env python3
"""
ファイル出力例: UDP受信→CSV/JSONファイル

村田センサーからのUDPパケットを受信し、ファイルに出力します。
CSV形式とJSON Lines形式の両方に対応しています。

実行方法:
    python examples/file_output.py           # CSV形式（デフォルト）
    python examples/file_output.py --json    # JSON Lines形式

停止方法:
    Ctrl+C

出力ファイル:
    sensor_YYYYMMDD_HHMMSS.csv または sensor_YYYYMMDD_HHMMSS.jsonl
"""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import TextIO

from murata_sensor import MurataReceiver


class FileWriter:
    """ファイル出力を管理するクラス"""

    def __init__(self, use_json: bool = False):
        self.use_json = use_json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = "jsonl" if use_json else "csv"
        self.filepath = Path(f"sensor_{timestamp}.{ext}")
        self.file: TextIO = open(self.filepath, "w", encoding="utf-8", newline="")
        self.csv_writer = None
        self.count = 0

        if not use_json:
            self.csv_writer = csv.writer(self.file)
            self.csv_writer.writerow(
                ["timestamp", "source_ip", "sensor_type", "unit_id", "rssi", "values"]
            )

    def write(self, sensor_data: dict, addr: tuple) -> None:
        """センサーデータをファイルに書き込む"""
        timestamp = datetime.now().isoformat()
        values_str = json.dumps(sensor_data["values"], ensure_ascii=False)

        if self.use_json:
            record = {
                "timestamp": timestamp,
                "source_ip": addr[0],
                "source_port": addr[1],
                "sensor_type": sensor_data["sensor_type"],
                "unit_id": sensor_data["info"].get("unit_id"),
                "rssi": sensor_data["info"].get("RSSI"),
                "values": sensor_data["values"],
            }
            self.file.write(json.dumps(record, ensure_ascii=False) + "\n")
        else:
            self.csv_writer.writerow(
                [
                    timestamp,
                    addr[0],
                    sensor_data["sensor_type"],
                    sensor_data["info"].get("unit_id"),
                    sensor_data["info"].get("RSSI"),
                    values_str,
                ]
            )

        self.file.flush()
        self.count += 1
        print(f"書込: {sensor_data['sensor_type']} ({self.count}件)")

    def close(self) -> None:
        """ファイルを閉じる"""
        self.file.close()


def main():
    parser = argparse.ArgumentParser(description="センサーデータをファイルに出力")
    parser.add_argument("--json", action="store_true", help="JSON Lines形式で出力")
    args = parser.parse_args()

    writer = FileWriter(use_json=args.json)
    print(f"出力ファイル: {writer.filepath}")

    def on_data(sensor_data: dict, addr: tuple) -> None:
        writer.write(sensor_data, addr)

    receiver = MurataReceiver(port=55039, data_callback=on_data)

    print("センサーデータを受信中... (Ctrl+Cで停止)")
    try:
        receiver.recv()
    except KeyboardInterrupt:
        writer.close()
        print(f"\n終了しました (出力件数: {writer.count})")


if __name__ == "__main__":
    main()
