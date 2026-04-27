# API仕様書

## 概要

村田製作所製無線センサユニットデータ受信ライブラリのAPI仕様書

## クラス一覧

### 1. MurataReceiver

村田製作所製センサーからのUDPデータ受信を行うメインクラス

#### コンストラクタ

```python
MurataReceiver(port: int, buffer_size: int = 1024,
               data_callback: Optional[Callable] = None,
               error_callback: Optional[Callable] = None,
               logger: Optional[logging.Logger] = None)
```

**パラメータ:**
- `port` (int): 受信ポート番号
- `buffer_size` (int, optional): 受信バッファサイズ（デフォルト: 1024）
- `data_callback` (callable, optional): センサーデータ受信時に呼ばれるコールバック。`(sensor_data: dict, addr: tuple) -> None`
- `error_callback` (callable, optional): エラー発生時に呼ばれるコールバック。`(error: Exception, raw_data: bytes, addr: tuple) -> None`
- `logger` (logging.Logger, optional): ロガー。未指定時は `logging.getLogger(__name__)` を使用

**例:**
```python
receiver = MurataReceiver(55039, data_callback=on_data, error_callback=on_error)
```

#### メソッド

##### run_in_thread(daemon=True)
```python
def run_in_thread(self, daemon: bool = True) -> threading.Thread
```
**説明:**  
別スレッドで受信を開始し、スレッドオブジェクトを返します。メインスレッドで他の処理を続けたい場合に使用します。

**パラメータ:** `daemon` (bool): True の場合デーモンスレッドにする（デフォルト: True）

**戻り値:** 受信ループを実行しているスレッド

##### recv()
```python
def recv() -> None
```
**説明:**  
UDPパケットの受信を開始します。ブロッキングの無限ループで動作し、KeyboardInterruptで停止します。

**戻り値:**  
None

**例外:**
- `KeyboardInterrupt`: ユーザーによる中断

**例:**
```python
try:
    receiver.recv()
except KeyboardInterrupt:
    print("受信を停止しました")
```

##### get_latest_data(addr: tuple)
```python
def get_latest_data(addr: tuple) -> Optional[MurataSensorBase]
```
**説明:**  
指定した送信元アドレスの最新のセンサーオブジェクトを取得します。

**パラメータ:**
- `addr` (tuple): IPアドレスとポート番号のタプル

**戻り値:**
- `MurataSensorBase`: 最新のセンサーオブジェクト（`.values`, `.info`, `.data` で参照）
- `None`: データが存在しない場合

**例:**
```python
sensor = receiver.get_latest_data(('192.168.1.100', 55039))
if sensor:
    print(sensor.values, sensor.info)
```

##### get_sensor_history(addr: tuple)
```python
def get_sensor_history(addr: tuple) -> List[Tuple[datetime, MurataSensorBase]]
```
**説明:**  
指定した送信元アドレスのセンサーデータ履歴を取得します。最大1000件まで保持。

**パラメータ:**
- `addr` (tuple): IPアドレスとポート番号のタプル

**戻り値:**
- `List[Tuple[datetime, MurataSensorBase]]`: `(更新日時, センサーオブジェクト)` のリスト

**例:**
```python
history = receiver.get_sensor_history(('192.168.1.100', 55039))
for ts, sensor in history[-5:]:
    print(ts, sensor.values)
```

##### make_sensor(data: bytes, addr: tuple)
```python
def make_sensor(data: bytes, addr: tuple) -> Optional[MurataSensorBase]
```
**説明:**  
受信データからセンサーインスタンスを生成します。

**パラメータ:**
- `data` (bytes): 受信した電文データ
- `addr` (tuple): 送信元アドレス

**戻り値:**
- `MurataSensorBase`: センサーインスタンス
- `None`: 解析に失敗した場合

---

### 2. AsyncMurataReceiver

asyncio 対応の非同期 UDP 受信クラス。`async for` でセンサーデータを取得できる。

#### コンストラクタ

```python
AsyncMurataReceiver(port: int, buffer_size: int = 1024, logger: Optional[logging.Logger] = None)
```

**パラメータ:** `port`, `buffer_size`, `logger`（いずれも MurataReceiver と同様）

#### メソッド

- **async start()**: 受信を開始する。UDP ソケットをバインドし、バックグラウンドで受信を開始する。
- **async stop()**: 受信を停止する。

#### イテレーション

`start()` 呼び出し後に `async for sensor_data, addr in receiver:` で受信データをイテレートできる。`sensor_data` は辞書（`sensor_type`, `sensor_type_code`, `timestamp`, `values`, `info`, `addr`）。

---

## ユーティリティ関数

### parse_text_line()

```python
def parse_text_line(line: str) -> Dict[str, Any]
```

**説明:**  
テキスト行からセンサーデータを解析します。ログファイルやCSVから取得したテキスト行を解析し、センサーデータを抽出できます。

**対応フォーマット:**
1. タイムスタンプ + IP/ポート + ERXDATA形式:  
   `2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 5438 0000 ...`
2. ERXDATAのみ:  
   `ERXDATA 5438 0000 ...`

**パラメータ:**
- `line` (str): テキスト行

**戻り値:**
```python
{
    'timestamp': datetime,          # 受信タイムスタンプ（なければNone）
    'source_ip': str,               # 送信元IPアドレス（なければNone）
    'source_port': int,             # 送信元ポート番号（なければNone）
    'sensor': MurataSensorBase,     # 解析済みセンサーオブジェクト
    'sensor_type': str,             # センサータイプ名
    'sensor_type_code': str | None, # センサ種別コード [tt]（16進2桁）
    'values': dict,                 # センサー値
    'info': dict,                   # センサー情報
    'raw_data': bytes,              # ERXDATAバイト列
}
```

**例外:**
- `ValueError`: 文字列フォーマットが不正な場合（ERXDATAが見つからない等）
- `FailedCheckSum`: チェックサムエラー
- `FailedCheckSumPayload`: ペイロードチェックサムエラー

**例:**
```python
from murata_sensor import parse_text_line

# タイムスタンプ + IP付きフォーマット
line = "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 5438 0000 1E75 F000 2F 7A 0303090001590532000C00260088050C002500260003040C005700260016050C00AF0026000F050C00BB0026000F050C00630563008705660D68052A0577 5438 7FFF"
result = parse_text_line(line)

print(result['timestamp'])      # datetime(2024, 9, 20, 16, 26, 11)
print(result['source_ip'])      # '192.168.1.100'
print(result['source_port'])    # 55061
print(result['sensor_type'])    # 'vibration'
print(result['values'])         # {'power-supply-voltage': {...}, ...}

# ERXDATAのみの文字列も解析可能
raw_line = "ERXDATA 5438 0000 1E75 F000 2F 7A 0303090001590532..."
result = parse_text_line(raw_line)
print(result['timestamp'])      # None
print(result['source_ip'])      # None
```

---

### create_sensor()

```python
def create_sensor(data: bytes, addr: Tuple[str, int] = (None, None)) -> Optional[MurataSensorBase]
```

**説明:**  
受信データからセンサーオブジェクトを生成するモジュールレベル関数。`MurataReceiver`インスタンスを使わずにセンサーオブジェクトを生成できます。

**パラメータ:**
- `data` (bytes): 受信データ（ERXDATAで始まるバイト列）
- `addr` (tuple, optional): 送信元アドレス（IPアドレス, ポート番号）のタプル

**戻り値:**
- `MurataSensorBase`: 生成したセンサーオブジェクト
- `None`: 不正なデータの場合

**例外:**
- `FailedCheckSum`: 電文全体のチェックサムが不正な場合
- `FailedCheckSumPayload`: ペイロードのチェックサムが不正な場合

**例:**
```python
from murata_sensor import create_sensor

data = b"ERXDATA 5438 0000 1E75 F000 2F 7A 0303090001590532..."
sensor = create_sensor(data, ('192.168.1.100', 55061))

if sensor:
    print(sensor.values)  # センサー値を取得
    print(sensor.info)    # センサー情報を取得
```

---

### 3. MurataSensorBase

センサーデータ解析の基底クラス

#### コンストラクタ

```python
MurataSensorBase(data: bytes, addr: tuple = (None, None))
```

**パラメータ:**
- `data` (bytes): 受信した電文データ
- `addr` (tuple, optional): IPアドレスとポート番号

**例外:**
- `FailedCheckSum`: 電文全体のチェックサムが不正
- `FailedCheckSumPayload`: ペイロードのチェックサムが不正

#### 属性

```python
data: bytes              # 受信した電文データ
info: Dict               # センサー情報辞書
payload_length: int      # ペイロードの長さ
payload: bytes          # ペイロードデータ
values: Dict            # 解析したセンサー値
```

#### メソッド

##### retrieve_values()
```python
def retrieve_values(self) -> None
```
**説明:**  
センサー固有のデータ解析を行います。各サブクラスで実装が必要です。

---

### 4. 各センサークラス

#### VibrationSensor（振動センサー・加速度版 1LZ）

```python
class VibrationSensor(MurataSensorBase)
```

**解析対象データ:**
- 電源電圧 [V]
- ピーク周波数1-5 [Hz]（FFT有効時のみ、無効時はNone）
- ピーク加速度1-5 [m/s2]（FFT有効時のみ、無効時はNone）
- 加速度RMS [m/s2]
- 尖度 [-]
- 温度 [℃]
- RSSI値 [dBm]

**出力形式（FFT有効時）:**
```python
{
    'power-supply-voltage': {'value': 2.97, 'unit': 'V', 'unit_name': '電位差（電圧）'},
    'peak-frequency-1': {'value': 12, 'unit': 'Hz', 'unit_name': '周波数'},
    'peak-acceleration-1': {'value': 0.02, 'unit': 'm/s2', 'unit_name': '加速度'},
    'peak-frequency-2': {'value': 37, 'unit': 'Hz', 'unit_name': '周波数'},
    'peak-acceleration-2': {'value': 0.01, 'unit': 'm/s2', 'unit_name': '加速度'},
    # ... (ピーク3-5も同様)
    'acceleration-RMS': {'value': 0.01, 'unit': 'm/s2', 'unit_name': '加速度実効値'},
    'kurtosis': {'value': 3.23, 'unit': '-', 'unit_name': '尖度'},
    'temperature': {'value': 25, 'unit': '℃', 'unit_name': 'セルシウス温度'}
}
```

**出力形式（FFT無効時）:**
```python
{
    'power-supply-voltage': {'value': 3.03, 'unit': 'V', 'unit_name': '電位差（電圧）'},
    'peak-frequency-1': {'value': None, 'unit': 'Hz', 'unit_name': '周波数'},  # 無効
    'peak-acceleration-1': {'value': None, 'unit': 'm/s2', 'unit_name': '加速度'},  # 無効
    # ... (ピーク2-5も無効、value=None)
    'acceleration-RMS': {'value': 0.0, 'unit': 'm/s2', 'unit_name': '加速度実効値'},
    'kurtosis': {'value': 0.0, 'unit': '-', 'unit_name': '尖度'},
    'temperature': {'value': 25, 'unit': '℃', 'unit_name': 'セルシウス温度'}
}
```

**注意:**
- FFT無効時や起動検知（閾値未満）の場合、ピーク周波数・加速度はペイロード内で`FFFFFF##`（無効値）として送信されます
- 無効値は`value: None`として返されます（unit、unit_nameは設定されます）

#### TemperatureAndHumiditySensor（温湿度センサー）

```python
class TemperatureAndHumiditySensor(MurataSensorBase)
```

**解析対象データ:**
- 温度
- 湿度
- 電源電圧
- RSSI値

#### CurrentPulseSensor（電流・パルスセンサー）

```python
class CurrentPulseSensor(MurataSensorBase)
```

**解析対象データ:**
- 電流値
- パルス数
- 電源電圧
- RSSI値

#### VibrationSpeed（振動・速度センサー 1TF）

```python
class VibrationSpeed(MurataSensorBase)
```

**解析対象データ:**
- ピーク周波数/加速度（2組）
- 加速度RMS
- 速度ピーク周波数/ピーク速度（3組）
- 速度RMS
- 尖度
- 温度
- 電源電圧
- RSSI値

#### その他のセンサークラス

**既存センサー:**
- `VoltagePulseSensor`: 電圧・パルスセンサー (1RU)
- `CTSensor`: CTセンサー (1MT/1NT)
- `ThreeTemperatureSensor`: 3温度/熱電対センサー (1EM/1PF)
- `ThreeCurrentSensor`: 3電流センサー (1ZU)
- `ThreeVoltageSensor`: 3電圧センサー (1ZV)
- `ThreeContactSensor`: 3接点センサー (1ZS)
- `WaterproofRepeater`: 防水中継機 (2CL)

**新規追加センサー:**
- `WaterLeakSensor`: 漏水センサー (2AX)
- `PlgDutySensor`: PLG Duty比監視ユニット (2AU)
- `BrakeCurrentMonitor`: 無線ブレーキ電流監視ユニット (2DB)
- `VibrationWithInstructionSensor`: 計測指示機能付無線振動センサユニット (2DN)
- `CompactThermocoupleSensor`: 小型熱電対ユニット (2FW)
- `SolarExternalSensor`: 外部センサ用ソーラーユニット (2SL)
- `ContactOutputSensor`: 接点出力ユニット (2ST)
- `AnalogMeterReaderSensor`: アナログメーター読取ユニット (2YT)
- `Vibration2TF001SpeedSensor`: 振動 2TF-001 速度モード/低速回転モード
- `Vibration2TF001AccelSensor`: 振動 2TF-001 加速度モード
- `WaterproofContactPulseSensor`: 防水防塵接点パルスユニット (2ZS)
- `WaterproofAnalogOutputSensor`: 防水防塵アナログ出力無線化ユニット (2ZU)

---

## 例外クラス

### MurataExceptionBase

```python
class MurataExceptionBase(Exception)
```

**説明:**  
村田センサー関連例外の基底クラス

**コンストラクタ:**
```python
MurataExceptionBase(message: str = "", details: str = "")
```

### FailedCheckSum

```python
class FailedCheckSum(MurataExceptionBase)
```

**説明:**  
電文全体のチェックサムエラー

### FailedCheckSumPayload

```python
class FailedCheckSumPayload(MurataExceptionBase)
```

**説明:**  
ペイロードのチェックサムエラー

---

## データ形式

### センサーデータ辞書

```python
{
    "addr": ("192.168.1.100", 55039),   # 送信元アドレス
    "RSSI": -45,                        # 受信信号強度
    "route": "...",                     # 経路情報
    "timestamp": "2024-06-13T10:30:00", # タイムスタンプ
    "sensor_type": "vibration",         # センサータイプ
    "sensor_type_code": "09",           # センサ種別コード [tt]（16進2桁, 仕様書「センサ種別」の値）
    "values": {                         # センサー値（センサータイプ毎に異なる）
        "temperature": 25.3,
        "humidity": 60.2,
        "voltage": 3.2
    }
}
```

### センサー値の形式

各センサー値は以下の形式の辞書として返されます：

```python
{
    'value': 25.3,              # 測定値（数値）または None（無効値の場合）
    'unit': '℃',                # 単位
    'unit_name': 'セルシウス温度'  # 単位名（日本語）
}
```

#### 無効値の処理

ペイロード内で無効値（`FFFFFF##`形式）が含まれる場合、`value`フィールドに`None`が設定されます。

**無効値が発生する主なケース:**
- 振動センサーのFFT無効時: ピーク周波数・加速度が無効
- 起動検知で閾値未満の場合: 各種測定値が無効
- 熱電対の基準温度未設定: 基準温度が無効
- センサー異常時: 該当項目が無効

**無効値の例:**
```python
# FFT無効時の振動センサーのピーク周波数
{
    'value': None,
    'unit': 'Hz',
    'unit_name': '周波数'
}

# 有効な温度値
{
    'value': 25.0,
    'unit': '℃',
    'unit_name': 'セルシウス温度'
}
```

### センサータイプ識別子

```python
SENSOR_TYPE = {
    # 基本センサー
    "030301FF": "temperature_and_humidity",  # 温湿度 1AN
    "030307FF": "thermocouple",             # 3温度/熱電対 1EM/1PF
    "030310FF": "current_pulse",            # 電流・パルス 1MU
    "030313FF": "voltage_pulse",            # 電圧・パルス 1RU
    "030312FF": "CT",                       # CT 1MT/1NT
    
    # 振動センサー（加速度）
    "03030900": "vibration",                # 振動（加速度） 1LZ
    "03030901": "vibration",                # 振動（加速度）レンジオーバー 1LZ
    
    # 振動センサー（速度）
    "03031800": "vibration_speed",          # 振動（速度） 1TF
    "03031801": "vibration_speed",          # 振動（速度）レンジオーバー 1TF
    
    # 防水防塵対応ユニット
    "03031BFF": "3_current",                # 3電流 1ZU
    "03031CFF": "3_voltage",                # 3電圧 1ZV
    "03031DFF": "3_contacts",               # 3接点 1ZS
    "03031EFF": "water_leak",               # 漏水センサ 2AX
    
    # 中継機・監視ユニット
    "0303FEFF": "waterproof_repeater",      # 防水中継機 2CL
    "030319FF": "plg_duty",                 # PLG Duty比監視ユニット 2AU
    "03032600": "brake_current_monitor",    # 無線ブレーキ電流監視ユニット 2DB
    
    # 計測指示機能付振動センサー
    "03032B00": "vibration_with_instruction",  # 計測指示機能付無線振動センサユニット 2DN
    "03032B01": "vibration_with_instruction",  # 計測指示機能付無線振動センサユニット 2DN (レンジオーバー)
    
    # 熱電対ユニット
    "030331FF": "compact_thermocouple",     # 小型熱電対ユニット 2FW
    
    # ソーラーユニット
    "03033AFF": "solar_external_sensor",    # 外部センサ用ソーラーユニット 2SL
    "03033A00": "solar_external_sensor",    # 外部センサ用ソーラーユニット 2SL (接点パルスモード)
    "03033A02": "solar_external_sensor",    # 外部センサ用ソーラーユニット 2SL (内部エラー)
    
    # 接点出力・メーター読取
    "030330FF": "contact_output",           # 接点出力ユニット 2ST
    "030333FF": "analog_meter_reader",      # アナログメーター読取ユニット 2YT
    
    # 振動 2TF-001シリーズ
    "03032F00": "vibration_2tf001_speed",   # 振動 2TF-001（速度モード/低速回転モード）
    "03032F01": "vibration_2tf001_speed",   # 振動 2TF-001（速度モード）レンジオーバー
    "03033200": "vibration_2tf001_accel",   # 振動 2TF-001（加速度モード）
    "03033201": "vibration_2tf001_accel",   # 振動 2TF-001（加速度モード）レンジオーバー
    
    # 防水防塵ユニット
    "030338FF": "waterproof_contact_pulse", # 防水防塵接点パルスユニット 2ZS
    "030339FF": "waterproof_analog_output", # 防水防塵アナログ出力無線化ユニット 2ZU
}
```

---

## 使用例

### 基本的な使用方法

```python
from murata_sensor import MurataReceiver
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# レシーバー初期化（コールバック未指定の場合はログ出力のみ）
receiver = MurataReceiver(55039)

try:
    # データ受信開始
    logger.info("Starting sensor data receiver...")
    receiver.recv()
except KeyboardInterrupt:
    # 終了時の処理
    logger.info("Shutting down...")
    
    # 全送信元の最新データを表示
    for addr in receiver.sensors.keys():
        sensor = receiver.get_latest_data(addr)
        if sensor:
            logger.info(f"Latest from {addr}: {sensor.values}")
        history = receiver.get_sensor_history(addr)
        logger.info(f"History count for {addr}: {len(history)}")
```

### 特定センサーのデータ取得

```python
# 特定のIPアドレスからのデータを監視
target_addr = ('192.168.1.100', 55039)

# 最新データ取得
sensor = receiver.get_latest_data(target_addr)
if sensor and sensor.values:
    print(f"Temperature: {sensor.values.get('temperature', {}).get('value')}°C")
    print(f"RSSI: {sensor.info.get('RSSI')} dBm")

# 履歴データ取得
history = receiver.get_sensor_history(target_addr)
for ts, s in history[-5:]:  # 最新5件
    print(f"Time: {ts}, Values: {s.values}")
```

### テキスト行からのデータ解析

```python
from murata_sensor import parse_text_line

# ログファイルからの読み込み例
with open('sensor_log.txt', 'r') as f:
    for line in f:
        try:
            result = parse_text_line(line)
            print(f"Time: {result['timestamp']}")
            print(f"Sensor Type: {result['sensor_type']}")
            print(f"Values: {result['values']}")
        except ValueError as e:
            print(f"解析エラー: {e}")
        except Exception as e:
            print(f"チェックサムエラー: {e}")

# 単一行の解析
line = "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 5438 0000 ..."
result = parse_text_line(line)

# センサー値の取得
for key, value_info in result['values'].items():
    print(f"{key}: {value_info['value']} {value_info['unit']}")
```

### create_sensorによる直接解析

```python
from murata_sensor import create_sensor

# バイトデータから直接センサーオブジェクトを生成
data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
sensor = create_sensor(data)

if sensor:
    print(f"温度: {sensor.values['temperature']['value']}℃")
    print(f"湿度: {sensor.values['humidity']['value']}%RH")
```

---

## 制限事項

1. **メモリ管理**: 履歴データはメモリ内にのみ保存（送信元あたり最大1000件）
2. **エラーハンドリング**: チェックサム検証とコールバックによる通知
3. **スレッドセーフティ**: マルチスレッド環境での `MurataReceiver` 共有は未検証。非同期利用は `AsyncMurataReceiver`、並行実行は `run_in_thread()` を推奨

