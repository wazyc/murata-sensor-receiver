import socket
import logging
import re
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
from datetime import datetime
from murata_sensor.murata_sensor import *

# センサータイプとクラスのマッピング
SENSOR_CLASSES = {
    "vibration": VibrationSensor,
    "vibration_speed": VibrationSpeed,
    "temperature_and_humidity": TemperatureAndHumiditySensor,
    "thermocouple": ThreeTemperatureSensor,
    "current_pulse": CurrentPulseSensor,
    "voltage_pulse": VoltagePulseSensor,
    "CT": CTSensor,
    "3_current": ThreeCurrentSensor,
    "3_voltage": ThreeVoltageSensor,
    "3_contacts": ThreeContactSensor,
    "waterproof_repeater": WaterproofRepeater,
    "water_leak": WaterLeakSensor,
    "plg_duty": PlgDutySensor,
    "brake_current_monitor": BrakeCurrentMonitor,
    "vibration_with_instruction": VibrationWithInstructionSensor,
    "compact_thermocouple": CompactThermocoupleSensor,
    "solar_external_sensor": SolarExternalSensor,
    "contact_output": ContactOutputSensor,
    "analog_meter_reader": AnalogMeterReaderSensor,
    "vibration_2tf001_speed": Vibration2TF001SpeedSensor,
    "vibration_2tf001_accel": Vibration2TF001AccelSensor,
    "waterproof_contact_pulse": WaterproofContactPulseSensor,
    "waterproof_analog_output": WaterproofAnalogOutputSensor,
}


def _is_murata_sensor_data(data: bytes) -> bool:
    """村田センサー形式かを安全に判定する"""
    try:
        return MurataSensorBase.is_murata_sensor_data(data)
    except Exception:
        return False


def _extract_sensor_message_code(data: bytes) -> Optional[str]:
    """ペイロード先頭のセンサー通知コード（0303[tt][SS]）を取得する"""
    try:
        message_code = data.decode("utf-8")[34:42]
    except Exception:
        return None
    return message_code if len(message_code) == 8 else None


def _extract_sensor_type_code(data: bytes) -> Optional[str]:
    """センサ種別コード [tt] を取得する"""
    message_code = _extract_sensor_message_code(data)
    if message_code is None:
        return None
    return message_code[4:6]


def _classify_unparsed_reason(data: bytes, error: Optional[Exception] = None) -> str:
    """未解析データの理由を分類する"""
    if error is not None:
        if isinstance(error, FailedCheckSum):
            return "checksum_error"
        if isinstance(error, FailedCheckSumPayload):
            return "payload_checksum_error"
        return "parse_error"

    if not _is_murata_sensor_data(data):
        return "non_murata_format"

    try:
        sensor_type = MurataSensorBase.check_sensor_type(data)
    except Exception:
        return "parse_error"
    if sensor_type is None or sensor_type not in SENSOR_TYPE.values():
        return "unsupported_sensor_type"

    return "parse_error"


def build_unparsed_data(
    raw_data: bytes,
    addr: Tuple[Optional[str], Optional[int]] = (None, None),
    reason: Optional[str] = None,
    error: Optional[Exception] = None,
    timestamp: Optional[Union[str, datetime]] = None,
) -> Dict[str, Any]:
    """解析できなかった受信データをアプリへ渡すための辞書を作成する"""
    if timestamp is None:
        timestamp_value: Union[str, datetime, None] = datetime.now().isoformat()
    else:
        timestamp_value = timestamp

    return {
        "parsed": False,
        "raw_data": raw_data,
        "addr": addr,
        "timestamp": timestamp_value,
        "reason": reason or _classify_unparsed_reason(raw_data, error),
        "sensor_type_code": _extract_sensor_type_code(raw_data),
        "sensor_message_code": _extract_sensor_message_code(raw_data),
        "is_murata_format": _is_murata_sensor_data(raw_data),
        "error": error,
    }


def create_sensor(
    data: bytes,
    addr: Tuple[Optional[str], Optional[int]] = (None, None),
) -> Optional[MurataSensorBase]:
    """受信データからセンサーオブジェクトを生成する

    MurataReceiverインスタンスを使わずにセンサーオブジェクトを生成できる
    モジュールレベル関数。

    Args:
        data: 受信データ（ERXDATAで始まるバイト列）
        addr: 送信元アドレス（IPアドレス, ポート番号）のタプル

    Returns:
        生成したセンサーオブジェクト。不正なデータの場合はNone

    Raises:
        FailedCheckSum: 電文全体のチェックサムが不正な場合
        FailedCheckSumPayload: ペイロードのチェックサムが不正な場合

    Example:
        >>> data = b"ERXDATA 5438 0000 1E75 F000 2F 7A 03030900..."
        >>> sensor = create_sensor(data, ('192.168.1.100', 55061))
        >>> print(sensor.values)
    """
    if not MurataSensorBase.is_murata_sensor_data(data):
        return None

    sensor_type = MurataSensorBase.check_sensor_type(data)
    if sensor_type is None or sensor_type not in SENSOR_TYPE.values():
        return None

    sensor_class = SENSOR_CLASSES.get(sensor_type)
    if sensor_class:
        return cast(Optional[MurataSensorBase], sensor_class(data, addr))
    return None


def parse_text_line(line: str, strict: bool = True) -> Dict[str, Any]:
    """テキスト行からセンサーデータを解析する

    ログファイルやCSVから取得したテキスト行を解析し、
    センサーデータを抽出する。

    対応フォーマット:
        1. タイムスタンプ + IP/ポート + ERXDATA形式:
           "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 5438 0000 ..."
        2. ERXDATAのみ:
           "ERXDATA 5438 0000 ..."

    Args:
        line: テキスト行
        strict: Trueの場合は従来通り解析不能時に例外を送出する。
            Falseの場合は未解析結果を辞書で返す。

    Returns:
        解析結果の辞書:
        {
            'timestamp': datetime または None,      # 受信タイムスタンプ
            'source_ip': str または None,          # 送信元IPアドレス
            'source_port': int または None,        # 送信元ポート番号
            'sensor': MurataSensorBase,            # 解析済みセンサーオブジェクト
            'sensor_type': str,                    # センサータイプ名
            'sensor_type_code': str または None,   # センサ種別コード [tt]（16進2桁）
            'values': dict,                        # センサー値
            'info': dict,                          # センサー情報
            'raw_data': bytes,                     # ERXDATAバイト列
        }

    Raises:
        ValueError: 文字列フォーマットが不正な場合（ERXDATAが見つからない等）
        FailedCheckSum: チェックサムエラー
        FailedCheckSumPayload: ペイロードチェックサムエラー

    Example:
        >>> line = "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 5438 0000 ..."
        >>> result = parse_text_line(line)
        >>> print(result['timestamp'])      # datetime(2024, 9, 20, 16, 26, 11)
        >>> print(result['source_ip'])      # '192.168.1.100'
        >>> print(result['sensor_type'])    # 'vibration'
        >>> print(result['values'])         # {'power-supply-voltage': {...}, ...}
    """
    line = line.strip()
    if not line:
        if not strict:
            return build_unparsed_data(
                b"",
                reason="empty_line",
                timestamp=None,
            )
        raise ValueError("空の文字列は解析できません")

    timestamp = None
    source_ip = None
    source_port = None
    erxdata_str = None

    # ERXDATAの位置を検索
    erxdata_index = line.find("ERXDATA")
    if erxdata_index == -1:
        if not strict:
            return build_unparsed_data(
                line.encode("utf-8"),
                reason="erxdata_not_found",
                timestamp=None,
            )
        raise ValueError("ERXDATAが見つかりません")

    # ERXDATAより前の部分を解析（タイムスタンプ、IP/ポート）
    if erxdata_index > 0:
        prefix = line[:erxdata_index]

        # タイムスタンプのパース（YYYY/MM/DD HH:MM:SS形式）
        timestamp_pattern = r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})"
        timestamp_match = re.search(timestamp_pattern, prefix)
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                pass

        # IP/ポートのパース（xxx.xxx.xxx.xxx/port:形式）
        ip_port_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/(\d+):"
        ip_port_match = re.search(ip_port_pattern, prefix)
        if ip_port_match:
            source_ip = ip_port_match.group(1)
            source_port = int(ip_port_match.group(2))

    # ERXDATA以降を抽出
    erxdata_str = line[erxdata_index:]

    # バイト列に変換
    raw_data = erxdata_str.encode("utf-8")

    # アドレスタプルを構築
    addr = (source_ip, source_port)

    # センサーオブジェクトを生成
    try:
        sensor = create_sensor(raw_data, addr)
    except Exception as e:
        if not strict:
            result = build_unparsed_data(
                raw_data,
                addr,
                error=e,
                timestamp=timestamp,
            )
            result.update(
                {
                    "source_ip": source_ip,
                    "source_port": source_port,
                }
            )
            return result
        raise

    if sensor is None:
        # create_sensorがNoneを返した場合、村田センサーデータとして認識できない
        # または未知のセンサータイプ
        if not _is_murata_sensor_data(raw_data):
            if not strict:
                result = build_unparsed_data(
                    raw_data,
                    addr,
                    reason="non_murata_format",
                    timestamp=timestamp,
                )
                result.update(
                    {
                        "source_ip": source_ip,
                        "source_port": source_port,
                    }
                )
                return result
            raise ValueError("村田センサーのデータ形式ではありません")

        sensor_type_code = _extract_sensor_message_code(raw_data) or "不明"
        if not strict:
            result = build_unparsed_data(
                raw_data,
                addr,
                reason="unsupported_sensor_type",
                timestamp=timestamp,
            )
            result.update(
                {
                    "source_ip": source_ip,
                    "source_port": source_port,
                }
            )
            return result
        raise ValueError(f"未知のセンサータイプです: {sensor_type_code}")

    sensor_type = MurataSensorBase.check_sensor_type(raw_data)

    return {
        "parsed": True,
        "timestamp": timestamp,
        "source_ip": source_ip,
        "source_port": source_port,
        "sensor": sensor,
        "sensor_type": sensor_type,
        "sensor_type_code": sensor.info.get("sensor_type_code"),
        "values": sensor.values,
        "info": sensor.info,
        "raw_data": raw_data,
    }


class SensorData:
    """センサーデータを管理するクラス"""

    def __init__(self, sensor: MurataSensorBase):
        self.last_update = datetime.now()
        self.sensor = sensor
        self.history = [(self.last_update, sensor)]

    def update(self, sensor: MurataSensorBase) -> None:
        """センサーデータを更新する

        Args:
            sensor: 新しいセンサーデータ
        """
        self.last_update = datetime.now()
        self.sensor = sensor
        self.history.append((self.last_update, sensor))

        # 履歴は最新1000件まで保持
        if len(self.history) > 1000:
            self.history = self.history[-1000:]


class MurataReceiver:
    """
    村田製作所製センサーからのUDPデータ受信を行うクラス

    Attributes:
        port (int): 受信ポート番号
        buffer_size (int): 受信バッファサイズ
        sensors (Dict): 送信元アドレスごとのセンサーデータを管理する辞書
    """

    def __init__(
        self,
        port: int,
        buffer_size: int = 1024,
        data_callback: Optional[
            Callable[[Dict[str, Any], Tuple[str, int]], None]
        ] = None,
        error_callback: Optional[
            Callable[[Exception, bytes, Tuple[str, int]], None]
        ] = None,
        logger: Optional[logging.Logger] = None,
        unparsed_callback: Optional[
            Callable[[Dict[str, Any], Tuple[str, int]], None]
        ] = None,
    ):
        """
        Args:
            port: 受信ポート番号
            buffer_size: 受信バッファサイズ（デフォルト1024）
            data_callback: センサーデータ受信時のコールバック関数
            error_callback: エラー発生時のコールバック関数
            logger: ロガーインスタンス（指定しない場合はデフォルトロガーを使用）
            unparsed_callback: 未解析データ受信時のコールバック関数
        """
        self.port = port
        self.buffer_size = buffer_size
        self.sensors: Dict[Tuple[str, int], SensorData] = {}
        self.data_callback = data_callback
        self.unparsed_callback = unparsed_callback
        self.error_callback = error_callback
        self._last_unparsed_error: Optional[Exception] = None
        self._last_unparsed_reason: Optional[str] = None
        self._setup_socket()

        # ロガーの設定
        self.logger = logger if logger else logging.getLogger(__name__)

    def _setup_socket(self) -> None:
        """UDPソケットの初期化を行う

        全てのネットワークインターフェースでデータを受信できるように設定
        """
        self.udp_serv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_serv_sock.bind(("0.0.0.0", self.port))

    def run_in_thread(self, daemon: bool = True) -> threading.Thread:
        """
        別スレッドで受信を開始し、スレッドオブジェクトを返す。

        メインスレッドで他の処理を行いながらUDP受信を継続できる。
        スレッドは recv() を実行するため、戻り値のスレッドが生存している間は受信が続く。

        Args:
            daemon: True の場合、スレッドをデーモンにする（メインプロセス終了時に自動終了）

        Returns:
            受信ループを実行しているスレッドオブジェクト

        Example:
            >>> receiver = MurataReceiver(port=55039, data_callback=on_data)
            >>> thread = receiver.run_in_thread()
            >>> # メインスレッドで別の処理が可能
        """
        thread = threading.Thread(target=self.recv, daemon=daemon)
        thread.start()
        return thread

    def recv(self) -> None:
        """センサーデータを継続的に受信する"""
        while True:  # 常に受信待ち
            data = b""
            addr: Tuple[str, int] = ("", 0)
            try:
                data, addr = self.udp_serv_sock.recvfrom(self.buffer_size)  # 受信
                self.logger.info(f"Received data from {addr}")
                self.logger.debug(f"Data: {data!r}")

                sensor = self.make_sensor(data, addr)
                if sensor:
                    self._update_sensor_data(addr, sensor)
                    self._process_sensor_data(addr, sensor)
                else:
                    self._process_unparsed_data(
                        data,
                        addr,
                        reason=self._last_unparsed_reason,
                        error=self._last_unparsed_error,
                    )
            except Exception as e:
                self.logger.error(f"Error processing data from {addr}: {e}")
                if self.error_callback:
                    try:
                        self.error_callback(e, data, addr)
                    except Exception as callback_error:
                        self.logger.error(f"Error in error callback: {callback_error}")

    def _process_unparsed_data(
        self,
        data: bytes,
        addr: Tuple[str, int],
        reason: Optional[str] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """解析できなかった受信データを未解析データ用コールバックへ渡す"""
        unparsed_data = build_unparsed_data(data, addr, reason=reason, error=error)

        self.logger.warning(
            "Unparsed sensor data from %s:%s reason=%s sensor_message_code=%s",
            addr[0],
            addr[1],
            unparsed_data["reason"],
            unparsed_data["sensor_message_code"],
        )

        if self.unparsed_callback:
            try:
                self.unparsed_callback(unparsed_data, addr)
            except Exception as e:
                self.logger.error(f"Error in unparsed callback: {e}")
                if self.error_callback:
                    try:
                        self.error_callback(e, data, addr)
                    except Exception as callback_error:
                        self.logger.error(f"Error in error callback: {callback_error}")

    def _update_sensor_data(
        self, addr: Tuple[str, int], sensor: MurataSensorBase
    ) -> None:
        """センサーデータを更新する

        Args:
            addr: 送信元アドレス
            sensor: センサーデータ
        """
        if addr in self.sensors:
            self.sensors[addr].update(sensor)
        else:
            self.sensors[addr] = SensorData(sensor)
            self.logger.info(f"New sensor detected from {addr}")

    def _process_sensor_data(
        self, addr: Tuple[str, int], sensor: MurataSensorBase
    ) -> None:
        """センサーデータの処理を行う

        Args:
            addr: 送信元アドレス
            sensor: センサーデータ
        """
        # センサーデータをディクショナリ形式に変換
        sensor_data = {
            "sensor_type": sensor.check_sensor_type(sensor.data),
            "sensor_type_code": sensor.info.get("sensor_type_code"),
            "timestamp": datetime.now().isoformat(),
            "values": sensor.values,
            "info": sensor.info,
            "addr": addr,
        }

        # デフォルトのログ出力
        self.logger.info("=" * 80)
        self.logger.info(f"Sensor Data from {addr[0]}:{addr[1]}")
        self.logger.info("-" * 40)
        self.logger.info(f"Sensor Type: {sensor_data['sensor_type']}")
        self.logger.info(f"Unit ID: {sensor.info['unit_id']}")
        self.logger.info(f"RSSI: {sensor.info['RSSI']} dBm")
        self.logger.info("-" * 40)
        self.logger.info("Sensor Values:")
        for key, value in sensor.values.items():
            self.logger.info(f"  {key}:")
            self.logger.info(f"    Value: {value['value']} {value['unit']}")
            self.logger.info(f"    Type: {value['unit_name']}")
        self.logger.info("=" * 80)

        # コールバック関数の実行
        if self.data_callback:
            try:
                self.data_callback(sensor_data, addr)
            except Exception as e:
                self.logger.error(f"Error in data callback: {e}")
                if self.error_callback:
                    try:
                        self.error_callback(e, sensor.data, addr)
                    except Exception as callback_error:
                        self.logger.error(f"Error in error callback: {callback_error}")

    def get_latest_data(self, addr: Tuple[str, int]) -> Optional[MurataSensorBase]:
        """指定された送信元の最新のセンサーデータを取得する

        Args:
            addr: 送信元アドレス

        Returns:
            最新のセンサーデータ。送信元が存在しない場合はNone
        """
        if addr in self.sensors:
            return self.sensors[addr].sensor
        return None

    def get_sensor_history(self, addr: Tuple[str, int]) -> List[Any]:
        """指定された送信元のセンサーデータ履歴を取得する

        Args:
            addr: 送信元アドレス

        Returns:
            センサーデータの履歴リスト。送信元が存在しない場合は空リスト
        """
        if addr in self.sensors:
            return self.sensors[addr].history
        return []

    def make_sensor(
        self,
        data: bytes,
        addr: Tuple[Optional[str], Optional[int]],
    ) -> Optional[MurataSensorBase]:
        """
        受信データからセンサーオブジェクトを生成する

        Args:
            data: 受信データ
            addr: 送信元アドレス

        Returns:
            生成したセンサーオブジェクト。不正なデータの場合はNone
        """
        self._last_unparsed_error = None
        self._last_unparsed_reason = None
        try:
            if not _is_murata_sensor_data(data):
                self.logger.warning("Unknown sensor data received")
                self._last_unparsed_reason = "non_murata_format"
                return None

            sensor_type = MurataSensorBase.check_sensor_type(data)
            if sensor_type is None or sensor_type not in SENSOR_TYPE.values():
                c = _extract_sensor_message_code(data) or "不明"
                self.logger.warning(f"Unknown sensor type: {c}")
                self._last_unparsed_reason = "unsupported_sensor_type"
                return None

            return cast(
                Optional[MurataSensorBase],
                self._create_sensor_instance(sensor_type, data, addr),
            )

        except Exception as e:
            self.logger.error(f"Error creating sensor object: {str(e)}")
            self._last_unparsed_error = e
            self._last_unparsed_reason = _classify_unparsed_reason(data, e)
            return None

    def _create_sensor_instance(
        self,
        sensor_type: str,
        data: bytes,
        addr: Tuple[Optional[str], Optional[int]],
    ) -> Optional[MurataSensorBase]:
        """センサータイプに応じたインスタンスを生成する

        内部的にモジュールレベルのSENSOR_CLASSESマッピングを使用する。
        """
        sensor_class = SENSOR_CLASSES.get(sensor_type)
        if sensor_class:
            return cast(Optional[MurataSensorBase], sensor_class(data, addr))
        return None
