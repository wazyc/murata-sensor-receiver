# プロジェクト概要

## 基本情報

- プロジェクト名: murata-sensor-receiver
- 目的: 村田製作所製無線センサユニット（電文仕様G対応）からのUDPデータ受信・解析
- ライセンス: MIT

## このライブラリについて

村田製作所の無線センサユニットはUDPパケットでセンサーデータを送信する。このライブラリはそのバイナリプロトコルを解析し、Pythonの辞書形式でデータを提供する。他のシステムに組み込んで使うPythonパッケージとして設計されている。

## 対象ユーザー

- 村田製作所の無線センサユニットを使用するシステム開発者

## 主要機能

1. UDP受信によるリアルタイムデータ取得
2. 同シリーズのセンサーに対応（温湿度、振動、電流・電圧、熱電対、漏水、防水中継機など）
3. コールバック方式によるデータ処理（data_callback / unparsed_callback / error_callback）
4. 非同期（asyncio）対応: `AsyncMurataReceiver`、スレッド実行: `MurataReceiver.run_in_thread()`
5. テキスト化された受信データからの解析: `parse_text_line()`（サンプル: `examples/parse_text.py`）
6. 自動チェックサム検証
7. 無効値の自動検出とNone変換（FFT無効時のピーク値、熱電対の基準温度など）
8. 未対応センサーや解析不能データのraw data通知

## 使用方法

### UDP受信（基本）

```python
from murata_sensor import MurataReceiver

def on_data(sensor_data, addr):
    print(sensor_data['sensor_type'], sensor_data['values'])

def on_unparsed(unparsed_data, addr):
    # UDPは再受信できないため、未解析データを保存して後日再解析できるようにします。
    print(unparsed_data['reason'], unparsed_data['sensor_type_code'])

receiver = MurataReceiver(
    port=55039,
    data_callback=on_data,
    unparsed_callback=on_unparsed,
)
receiver.recv()
```

### テキスト解析

```python
from murata_sensor import parse_text_line

line = "ERXDATA 1115 0000 0464 F000 4D 7A 03030900..."
result = parse_text_line(line)
print(result['sensor_type'], result['values'])
```

未対応センサーを含むログを処理し続けたい場合は、`strict=False` を指定します。

```python
result = parse_text_line(line, strict=False)
if result['parsed']:
    print(result['sensor_type'], result['values'])
else:
    print(result['reason'], result['sensor_type_code'])
    # raw_dataを保存して、ライブラリ更新後に再解析できます。
    save_raw_packet(result['raw_data'])
```

### 非同期（asyncio）での使用

```python
import asyncio
from murata_sensor import AsyncMurataReceiver

async def main():
    receiver = AsyncMurataReceiver(port=55039, include_unparsed=True)
    await receiver.start()
    try:
        async for sensor_data, addr in receiver:
            if sensor_data.get('parsed') is False:
                print(sensor_data['reason'], sensor_data['sensor_type_code'])
            else:
                print(sensor_data['sensor_type'], sensor_data['values'])
    finally:
        await receiver.stop()

asyncio.run(main())
```

スレッドで受信しながらメイン処理を続ける場合は `MurataReceiver.run_in_thread()` を使用する（サンプル: `examples/threaded_receiver.py`）。

## 関連ドキュメント

| ドキュメント | 説明 |
|------------|------|
| [architecture.md](architecture.md) | システムアーキテクチャ設計 |
| [api_specification.md](api_specification.md) | API仕様書 |

## 変更履歴

### v1.0.0 (現行)
- **メタデータAPI**: 対応センサー一覧・タイプ判定（`get_supported_sensors` 等）を追加
- **解析検証フラグ**: `parse_verified` で実電文による値解析の自動テスト済み範囲を明示
- **不具合修正**: Async の `sensor_type_code`、Solar 緯度経度の values 規約、振動系 SS 状態解析など

### v0.3.0
- **防水防塵接点パルスユニット2ZS**: 状態、エッジカウント、桁上がりカウントの解析に対応
- **防水防塵アナログ出力無線化ユニット2ZU**: 電流値、電圧値、測定モードの解析に対応

### v0.2.0
- **振動センサー1LZ**: FFT解析結果（ピーク周波数・加速度1-5）の出力に対応
- **無効値処理**: ペイロード内の無効値（`FFFFFF##`）を`None`として明示的に返すように改善
- **全センサー対応**: 小型熱電対2FWなど、すべてのセンサーで無効値が統一的に処理される

### v0.1.0 
- 初回リリース
- UDP受信、テキスト解析、非同期受信の機能を実装

## ディレクトリ構造

```
murata-sensor-receiver/
├── src/
│   └── murata_sensor/          # コアライブラリ
│       ├── __init__.py         # パブリックAPI
│       ├── murata_receiver.py  # UDP受信・データ管理（MurataReceiver, create_sensor, parse_text_line）
│       ├── async_receiver.py   # 非同期UDP受信（AsyncMurataReceiver）
│       ├── murata_sensor.py    # センサーデータ解析（MurataSensorBase, 各センサークラス）
│       └── murata_exception.py # カスタム例外
├── examples/                   # 使用例
│   ├── simple_stdout.py        # 標準出力
│   ├── sqlite_storage.py       # SQLite保存
│   ├── file_output.py         # ファイル出力
│   ├── mqtt_publish.py        # MQTT送信
│   ├── parse_text.py          # テキスト解析
│   ├── async_receiver.py      # 非同期受信（AsyncMurataReceiver）
│   ├── async_durable_processing.py  # 長時間・大量受信・DB保存・欠損なし
│   ├── async_fastapi_receiver.py   # FastAPI と同時に裏で受信
│   ├── threaded_receiver.py   # スレッド実行（run_in_thread）
│   ├── callback_closure.py    # コールバック: クロージャ
│   ├── callback_class.py      # コールバック: クラス
│   ├── callback_partial.py    # コールバック: partial
│   ├── callback_lambda.py     # コールバック: ラムダ
│   ├── debug_sender.py        # テスト用送信
│   ├── test_fft_modes.py      # FFT有効/無効時のテスト
│   └── test_invalid_values.py # 無効値処理のテスト
├── tests/                      # テストコード
├── docs/                       # ドキュメント（本ファイルは docs/overview.md）
├── pyproject.toml              # パッケージ設定
└── README.md                   # プロジェクト説明
```

## 対応センサー一覧

「対応」はセンサーコード登録と解析クラスの存在を意味する。実電文による主要値の自動テスト済みかどうかは `parse_verified` で区別する（`get_supported_sensors()` でも取得可能）。

| センサー名（sensor_type） | センサーコード | 説明 | 製品例 | parse_verified |
|---------------------------|----------------|------|--------|----------------|
| temperature_and_humidity | 030301FF | 温湿度センサー | 1AN | 済み |
| thermocouple | 030307FF | 3温度/熱電対センサー | 1EM/1PF | 済み |
| current_pulse | 030310FF | 電流・パルスセンサー | 1MU | 未 |
| voltage_pulse | 030313FF | 電圧・パルスセンサー | 1RU | 未 |
| CT | 030312FF | CTセンサー | 1MT/1NT | 未 |
| vibration | 03030900, 03030901 | 振動センサー（加速度） | 1LZ | 済み |
| vibration_speed | 03031800, 03031801 | 振動センサー（速度） | 1TF | 未 |
| 3_current | 03031BFF | 防水3電流センサー | 1ZU | 済み |
| 3_voltage | 03031CFF | 防水3電圧センサー | 1ZV | 済み |
| 3_contacts | 03031DFF | 防水3接点センサー | 1ZS | 済み |
| water_leak | 03031EFF | 漏水センサー | 2AX | 未 |
| waterproof_repeater | 0303FEFF | 防水中継機 | 2CL | 済み |
| plg_duty | 030319FF | PLG Duty比監視ユニット | 2AU | 未 |
| brake_current_monitor | 03032600 | 無線ブレーキ電流監視ユニット | 2DB | 未 |
| vibration_with_instruction | 03032B00, 03032B01 | 計測指示機能付振動センサー | 2DN | 未 |
| compact_thermocouple | 030331FF | 小型熱電対ユニット | 2FW | 未 |
| solar_external_sensor | 03033AFF, 03033A00, 03033A02 | 外部センサ用ソーラーユニット | 2SL | 未 |
| contact_output | 030330FF | 接点出力ユニット | 2ST | 未 |
| analog_meter_reader | 030333FF | アナログメーター読取ユニット | 2YT | 未 |
| vibration_2tf001_speed | 03032F00, 03032F01 | 振動 2TF-001 速度モード/低速回転モード | 2TF-001 | 未 |
| vibration_2tf001_accel | 03033200, 03033201 | 振動 2TF-001 加速度モード | 2TF-001 | 未 |
| waterproof_contact_pulse | 030338FF | 防水防塵接点パルスユニット | 2ZS | 済み |
| waterproof_analog_output | 030339FF | 防水防塵アナログ出力無線化ユニット | 2ZU | 済み |

対応済みセンサー一覧は `get_supported_sensors()` からも取得できる。詳細なAPIは [api_specification.md](api_specification.md) を参照。
