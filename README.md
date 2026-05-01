# Murata Sensor Receiver

村田製作所製無線センサユニットからのUDPデータを受信・解析するPythonライブラリ

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 概要

村田製作所の無線センサユニット（電文仕様I対応）は、UDPパケットでセンサーデータを送信します。
このライブラリではUDPパケットを受信・解析します。

## 特徴

- **リアルタイム処理**: UDPパケットの連続受信と即座の解析
- **コールバックアーキテクチャ**: ユーザー定義コールバックによるデータ処理
- **テキスト解析対応**: ログファイルやCSVからのセンサーデータ解析
- **データ検証**: チェックサム検証
- **依存関係なし**: Python標準ライブラリのみを使用

## インストール

```bash
pip install murata-sensor-receiver
```

## クイックスタート

### 基本的な使用方法

```python
from murata_sensor import MurataReceiver
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)

def data_handler(sensor_data, addr):
    """受信したセンサーデータのコールバック関数"""
    print(f"Received from {addr[0]}:{addr[1]}")
    print(f"Sensor Type: {sensor_data['sensor_type']}")
    print(f"Sensor Type Code: {sensor_data['sensor_type_code']}")  # 例: '01', '09'
    print(f"Values: {sensor_data['values']}")
    print(f"RSSI: {sensor_data['info']['RSSI']} dBm")
    print("-" * 40)

def error_handler(error, raw_data, addr):
    """エラー処理のコールバック関数"""
    print(f"Error from {addr}: {error}")

# レシーバー作成
receiver = MurataReceiver(
    port=55039,
    data_callback=data_handler,
    error_callback=error_handler
)

# 受信開始
try:
    receiver.recv()
except KeyboardInterrupt:
    print("Stopping receiver...")
```

### 高度な使用方法

```python
from murata_sensor import MurataReceiver
import logging
import json

# カスタムロガー
logger = logging.getLogger('my_app.sensor')
logger.setLevel(logging.DEBUG)

class SensorDataProcessor:
    def __init__(self):
        self.data_buffer = []
    
    def handle_sensor_data(self, sensor_data, addr):
        """センサーデータの処理と保存"""
        # タイムスタンプと送信元情報を追加
        sensor_data.update({
            'source_ip': addr[0],
            'source_port': addr[1],
            'processed_at': datetime.now().isoformat()
        })
        
        # バッファに保存
        self.data_buffer.append(sensor_data)
        
        # センサータイプに応じた処理
        sensor_type = sensor_data['sensor_type']
        
        if sensor_type == 'vibration':
            self.process_vibration_data(sensor_data)
        elif sensor_type == 'temperature_and_humidity':
            self.process_temp_humidity_data(sensor_data)
        
        # データベース保存、API送信など
        self.save_to_database(sensor_data)
    
    def handle_error(self, error, raw_data, addr):
        """エラー処理"""
        logger.error(f"Sensor error from {addr}: {error}")
        # アラート送信、ファイルログなど
    
    def process_vibration_data(self, data):
        """振動データの固有処理"""
        values = data['values']
        # 異常検知、FFT計算など
        pass
    
    def process_temp_humidity_data(self, data):
        """温湿度データの固有処理"""
        values = data['values']
        # 範囲チェック、トレンド計算など
        pass
    
    def save_to_database(self, data):
        """データベースへの保存"""
        # 使用するデータベースに応じた実装
        pass

# プロセッサの初期化
processor = SensorDataProcessor()

# カスタムプロセッサを使用したレシーバーの作成
receiver = MurataReceiver(
    port=55039,
    data_callback=processor.handle_sensor_data,
    error_callback=processor.handle_error,
    logger=logger
)

# 受信開始
receiver.recv()
```

### 非同期（asyncio）での使用

FastAPI や aiohttp など非同期フレームワークと組み合わせる場合は `AsyncMurataReceiver` を使用する。

```python
import asyncio
from murata_sensor import AsyncMurataReceiver

async def main():
    receiver = AsyncMurataReceiver(port=55039)
    await receiver.start()

    try:
        async for sensor_data, addr in receiver:
            print(f"{sensor_data['sensor_type']} ({sensor_data['sensor_type_code']}): {sensor_data['values']}")
    finally:
        await receiver.stop()

asyncio.run(main())
```

既存の `MurataReceiver` をスレッドで動かす場合は `run_in_thread()` を使う。

```python
from murata_sensor import MurataReceiver

def on_data(sensor_data, addr):
    print(f"受信: {sensor_data['sensor_type']}")

receiver = MurataReceiver(port=55039, data_callback=on_data)
thread = receiver.run_in_thread()

# メインスレッドで別の処理を継続できる
```

## 対応センサータイプ

| センサータイプ | センサーコード | 説明 | 製品例 |
|-------------|-------------|------|--------|
| temperature_and_humidity | 030301FF | 温湿度センサー | 1AN |
| thermocouple | 030307FF | 3温度/熱電対センサー | 1EM/1PF |
| current_pulse | 030310FF | 電流・パルスセンサー | 1MU |
| voltage_pulse | 030313FF | 電圧・パルスセンサー | 1RU |
| CT | 030312FF | CTセンサー | 1MT/1NT |
| vibration | 03030900, 03030901 | 振動センサー（加速度） | 1LZ |
| vibration_speed | 03031800, 03031801 | 振動センサー（速度） | 1TF |
| 3_current | 03031BFF | 防水3電流センサー | 1ZU |
| 3_voltage | 03031CFF | 防水3電圧センサー | 1ZV |
| 3_contacts | 03031DFF | 防水3接点センサー | 1ZS |
| water_leak | 03031EFF | 漏水センサー | 2AX |
| waterproof_repeater | 0303FEFF | 防水中継機 | 2CL |
| plg_duty | 030319FF | PLG Duty比監視ユニット | 2AU |
| brake_current_monitor | 03032600 | 無線ブレーキ電流監視ユニット | 2DB |
| vibration_with_instruction | 03032B00, 03032B01 | 計測指示機能付振動センサー | 2DN |
| compact_thermocouple | 030331FF | 小型熱電対ユニット | 2FW |
| solar_external_sensor | 03033AFF, 03033A00, 03033A02 | 外部センサ用ソーラーユニット | 2SL |
| contact_output | 030330FF | 接点出力ユニット | 2ST |
| analog_meter_reader | 030333FF | アナログメーター読取ユニット | 2YT |
| vibration_2tf001_speed | 03032F00, 03032F01 | 振動 2TF-001 速度モード/低速回転モード | 2TF-001 |
| vibration_2tf001_accel | 03033200, 03033201 | 振動 2TF-001 加速度モード | 2TF-001 |
| waterproof_contact_pulse | 030338FF | 防水防塵接点パルスユニット | 2ZS |
| waterproof_analog_output | 030339FF | 防水防塵アナログ出力無線化ユニット | 2ZU |

対応済みセンサー一覧はAPIからも取得できます。設定画面や診断表示など、利用アプリ側で対応範囲を表示したい場合に使用します。

```python
from murata_sensor import get_supported_sensors

for sensor in get_supported_sensors():
    print(sensor["sensor_type"], sensor["type_codes"], sensor["products"])
```

## 解析結果のデータ構造

このライブラリは、UDP受信時およびテキスト解析時に、**Pythonの辞書形式**で解析結果を返します。  
開発者はこの辞書をそのままDB保存・JSON変換・メッセージキュー送信などに利用できます。

### UDP受信（MurataReceiver / AsyncMurataReceiver）の例

`MurataReceiver` の `data_callback` に渡される `sensor_data` の典型的な例（温湿度センサー）:

```python
{
    "sensor_type": "temperature_and_humidity",  # センサータイプ名
    "sensor_type_code": "01",                   # センサ種別コード [tt]（16進2桁）
    "timestamp": "2024-03-17T10:30:00.123456",  # 受信時刻（ISO8601文字列）
    "values": {                                 # センサー固有の測定値
        "power-supply-voltage": {
            "value": 3.0,
            "unit": "V",
            "unit_name": "電位差（電圧）",
        },
        "temperature": {
            "value": 25.3,
            "unit": "℃",
            "unit_name": "セルシウス温度",
        },
        "humidity": {
            "value": 60.2,
            "unit": "%RH",
            "unit_name": "相対湿度",
        },
    },
    "info": {                                   # センサー情報メタデータ
        "addr": ("192.168.1.100", 55039),       # 送信元アドレス
        "unit_id": "0002",                      # ユニットID
        "message_id": "62BE",                   # メッセージID
        "RSSI": -45,                            # 受信信号強度[dBm]
        "sensor_type_code": "01",               # センサ種別コード（冗長だが info 側にも格納）
        "status": {
            "code": "FF",
            "description": "固定値(FF)",
        },
        "route": ["7FFF"],                      # 経路情報（最後の要素がゲートウェイID）
    },
    "addr": ("192.168.1.100", 55039),           # MurataReceiver が受信したアドレス
}
```

振動センサー（1LZ）の例（FFT有効時）:

```python
{
    "sensor_type": "vibration",
    "sensor_type_code": "09",
    "timestamp": "2024-03-17T10:31:00.456789",
    "values": {
        "power-supply-voltage": {"value": 3.34, "unit": "V", "unit_name": "電位差（電圧）"},
        "peak-frequency-1": {"value": 12, "unit": "Hz", "unit_name": "周波数"},
        "peak-acceleration-1": {"value": 0.22, "unit": "m/s2", "unit_name": "加速度"},
        "peak-frequency-2": {"value": 25, "unit": "Hz", "unit_name": "周波数"},
        "peak-acceleration-2": {"value": 0.22, "unit": "m/s2", "unit_name": "加速度"},
        # ... (ピーク3-5も同様)
        "acceleration-RMS": {"value": 0.12, "unit": "m/s2", "unit_name": "加速度実効値"},
        "kurtosis": {"value": 1.53, "unit": "-", "unit_name": "尖度"},
        "temperature": {"value": 26.52, "unit": "℃", "unit_name": "セルシウス温度"},
    },
    "info": {
        "addr": ("192.168.1.101", 55039),
        "unit_id": "1115",
        "message_id": "0464",
        "RSSI": -58,
        "sensor_type_code": "09",
        "status": {"code": "00", "description": "正常"},
        "route": ["7FFF"],
    },
    "addr": ("192.168.1.101", 55039),
}
```

**無効値の処理:**

センサーデータに無効値（ペイロード内で`FFFFFF##`）が含まれる場合、`value`フィールドに`None`が設定されます。

```python
# FFT無効時の振動センサー例（ピーク値が無効）
{
    "sensor_type": "vibration",
    "values": {
        "power-supply-voltage": {"value": 3.03, "unit": "V", "unit_name": "電位差（電圧）"},
        "peak-frequency-1": {"value": None, "unit": "Hz", "unit_name": "周波数"},  # 無効
        "peak-acceleration-1": {"value": None, "unit": "m/s2", "unit_name": "加速度"},  # 無効
        # ... (ピーク2-5も無効)
        "acceleration-RMS": {"value": 0.0, "unit": "m/s2", "unit_name": "加速度実効値"},
        "kurtosis": {"value": 0.0, "unit": "-", "unit_name": "尖度"},
        "temperature": {"value": 25, "unit": "℃", "unit_name": "セルシウス温度"}
    }
}
```

### テキスト解析（parse_text_line）の例

`parse_text_line()` はテキスト1行から同様の情報を辞書で返します:

```python
from murata_sensor import parse_text_line

line = "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 1115 0000 0464 F000 4D 7A 03030900..."
result = parse_text_line(line)

print(result["sensor_type"])       # 例: 'vibration'
print(result["sensor_type_code"])  # 例: '09'
print(result["timestamp"])         # datetime(2024, 9, 20, 16, 26, 11)
print(result["source_ip"])         # '192.168.1.100'
print(result["values"])            # センサー固有の値辞書
print(result["info"])              # MurataSensorBase.info と同等の情報
```

戻り値の構造（概要）:

```python
{
    "timestamp": datetime | None,       # 受信タイムスタンプ（なければ None）
    "source_ip": str | None,            # 送信元IPアドレス
    "source_port": int | None,          # 送信元ポート番号
    "sensor": MurataSensorBase,         # 解析済みセンサーオブジェクト
    "sensor_type": str,                 # センサータイプ名
    "sensor_type_code": str | None,     # センサ種別コード [tt]（16進2桁）
    "values": dict,                     # センサー値
    "info": dict,                       # センサー情報
    "raw_data": bytes,                  # 元のERXDATA文字列のバイト列
}
```

## APIリファレンス

### MurataReceiver

村田製作所製センサーデータの受信と処理を行うメインクラス

#### コンストラクタ

```python
MurataReceiver(port, buffer_size=1024, data_callback=None, error_callback=None, logger=None)
```

**パラメータ:**
- `port` (int): リッスンするUDPポート番号
- `buffer_size` (int, optional): 受信バッファサイズ（デフォルト: 1024）
- `data_callback` (callable, optional): センサーデータのコールバック関数
- `error_callback` (callable, optional): エラー処理のコールバック関数
- `logger` (logging.Logger, optional): カスタムロガーインスタンス

#### メソッド

##### recv()
センサーデータの連続受信を開始します（ブロッキング）。

##### run_in_thread(daemon=True)
別スレッドで受信を開始し、スレッドオブジェクトを返します。メインスレッドで他の処理を継続したい場合に使用します。

##### get_latest_data(addr)
指定したアドレスからの最新のセンサーデータを取得します。

##### get_sensor_history(addr)
指定したアドレスからのセンサーデータ履歴を取得します。

### コールバック関数

#### データコールバック
```python
def data_callback(sensor_data: dict, addr: tuple) -> None:
    """
    Args:
        sensor_data (dict): 処理済みセンサーデータ（以下の構造）:
            {
                'sensor_type': str,      # センサータイプ名
                'timestamp': str,        # ISO形式のタイムスタンプ
                'values': dict,          # センサー固有の値
                'info': dict,           # センサー情報（RSSI、ユニットIDなど）
                'addr': tuple           # 送信元アドレス（ip, port）
            }
        addr (tuple): 送信元アドレス（ip_address, port）
    """
```

#### エラーコールバック
```python
def error_callback(error: Exception, raw_data: bytes, addr: tuple) -> None:
    """
    Args:
        error (Exception): 発生した例外
        raw_data (bytes): 生のUDPパケットデータ
        addr (tuple): 送信元アドレス（ip_address, port）
    """
```

### AsyncMurataReceiver

asyncio 対応の非同期 UDP 受信クラス。`async for` でセンサーデータを取得できる。

#### コンストラクタ

```python
AsyncMurataReceiver(port, buffer_size=1024, logger=None)
```

#### メソッド

##### async start()
受信を開始する。UDP ソケットをバインドし、バックグラウンドで受信を開始する。

##### async stop()
受信を停止する。

##### async for での利用
`async for sensor_data, addr in receiver:` で受信データをイテレートできる。`start()` 呼び出し後に使用する。

## 使用例

詳細な使用例は [`examples/`](./examples/) ディレクトリを参照してください:

| ファイル | 説明 |
|---------|------|
| [simple_stdout.py](./examples/simple_stdout.py) | UDP受信→標準出力（最もシンプルな例） |
| [sqlite_storage.py](./examples/sqlite_storage.py) | UDP受信→SQLiteデータベース保存 |
| [file_output.py](./examples/file_output.py) | UDP受信→CSV/JSONファイル出力 |
| [mqtt_publish.py](./examples/mqtt_publish.py) | UDP受信→MQTTブローカーへ送信 |
| [parse_text.py](./examples/parse_text.py) | テキスト行からセンサーデータを解析 |
| [callback_closure.py](./examples/callback_closure.py) | コールバック: クロージャパターン |
| [callback_class.py](./examples/callback_class.py) | コールバック: クラスメソッドパターン |
| [callback_partial.py](./examples/callback_partial.py) | コールバック: functools.partialパターン |
| [callback_lambda.py](./examples/callback_lambda.py) | コールバック: ラムダ式パターン |
| [async_receiver.py](./examples/async_receiver.py) | 非同期受信（AsyncMurataReceiver と async for） |
| [threaded_receiver.py](./examples/threaded_receiver.py) | スレッドで受信（run_in_thread） |
| [async_durable_processing.py](./examples/async_durable_processing.py) | 長時間稼働・大量受信・DB保存・欠損なし（キュー＋ワーカー） |
| [async_fastapi_receiver.py](./examples/async_fastapi_receiver.py) | FastAPI と同時に裏で UDP 受信（要: pip install fastapi uvicorn） |
| [debug_sender.py](./examples/debug_sender.py) | テスト用UDPパケット送信ツール |

## エラーハンドリング

このライブラリは、カスタム例外にエラー処理を提供します:

- `FailedCheckSum`: メッセージのチェックサム検証失敗
- `FailedCheckSumPayload`: ペイロードのチェックサム検証失敗
- `MurataExceptionBase`: すべての村田センサー関連エラーの基底例外

```python
from murata_sensor import MurataReceiver, FailedCheckSum, FailedCheckSumPayload

def error_handler(error, raw_data, addr):
    if isinstance(error, FailedCheckSum):
        print(f"Checksum error from {addr}")
    elif isinstance(error, FailedCheckSumPayload):
        print(f"Payload checksum error from {addr}")
    else:
        print(f"Unknown error from {addr}: {error}")

receiver = MurataReceiver(port=55039, error_callback=error_handler)
```

## ドキュメント

設計書・API仕様

- [docs/overview.md](docs/overview.md) - プロジェクト概要・ディレクトリ構造・関連ドキュメント一覧
- [docs/architecture.md](docs/architecture.md) - システムアーキテクチャ設計
- [docs/api_specification.md](docs/api_specification.md) - API仕様書

## 開発

### 開発環境セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/wazyc/murata-sensor-receiver.git
cd murata-sensor-receiver

# 開発用依存関係のインストール
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# テスト実行
pytest

# コードフォーマット
black src/murata_sensor/
flake8 src/ tests/

# 型チェック
mypy src/murata_sensor/
```

### テスト

```bash
# カバレッジ付きですべてのテストを実行
pytest --cov=murata_sensor

# 特定のテストファイルを実行
pytest tests/test_murata_receiver.py

# HTMLカバレッジレポートの生成
pytest --cov=murata_sensor --cov-report=html
```

## ライセンス

MIT [LICENSE](LICENSE) 
