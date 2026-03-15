#!/usr/bin/env python3
"""
テキスト解析例: 文字列→センサーデータ

ログファイルやCSVに記録されたセンサーデータ文字列を解析し、
構造化されたデータとして取得します。

実行方法:
    python examples/parse_text.py

対応フォーマット:
    1. タイムスタンプ + IP/ポート + ERXDATA形式:
       "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 5438 0000 ..."
    2. ERXDATAのみ:
       "ERXDATA 5438 0000 ..."
"""

from murata_sensor import parse_text_line


def main():
    # サンプルデータ（実際のセンサーから取得したデータ形式）
    sample_lines = [
        # 振動センサーのデータ
        "ERXDATA 1115 0000 0464 F000 4D 7A 03030900014E0532000C00260016050C001900260016050C002500260016050C004B00260007050C005700260007050C000C0563009905660A5C052A070D 1115 7FFF",
        # タイムスタンプ付きデータ（実際のログ形式）
        "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 1115 0000 0464 F000 4D 7A 03030900014E0532000C00260016050C001900260016050C002500260016050C004B00260007050C005700260007050C000C0563009905660A5C052A070D 1115 7FFF",
    ]

    for i, line in enumerate(sample_lines, 1):
        print(f"=== サンプル {i} ===")
        print(f"入力: {line[:60]}...")
        print()

        try:
            result = parse_text_line(line)

            # メタデータ表示
            if result["timestamp"]:
                print(f"タイムスタンプ: {result['timestamp']}")
            if result["source_ip"]:
                print(f"送信元: {result['source_ip']}:{result['source_port']}")

            # センサー情報
            print(f"センサータイプ: {result['sensor_type']}")
            print(f"ユニットID: {result['info'].get('unit_id')}")
            print(f"RSSI: {result['info'].get('RSSI')} dBm")

            # センサー値
            print("測定値:")
            for key, value in result["values"].items():
                print(f"  {key}: {value['value']} {value['unit']}")

        except ValueError as e:
            print(f"エラー: {e}")

        print()


def parse_from_file_example():
    """ファイルから読み込んで解析する例"""
    print("=== ファイルからの解析例 ===")
    print("（以下はサンプルコードです）")
    print()
    print("""
# ログファイルを1行ずつ解析
with open("sensor_log.txt", "r") as f:
    for line in f:
        if "ERXDATA" in line:
            try:
                result = parse_text_line(line)
                print(f"{result['sensor_type']}: {result['values']}")
            except ValueError as e:
                print(f"解析エラー: {e}")
    """)


if __name__ == "__main__":
    main()
    print()
    parse_from_file_example()
