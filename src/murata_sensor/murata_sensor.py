import logging
from typing import Any, Dict, List, Optional, Tuple

from murata_sensor.murata_exception import *

# 村田製作所　無線センサユニット　パケットフォーマット
# ドキュメントバージョン B に対応

# payloadの"センサデータ通知"項目に対応（0303[tt][SS] の 8 文字コード → センサータイプ名）
SENSOR_TYPE = {
    "030301FF": "temperature_and_humidity",  # 温湿度 1AN
    "030307FF": "thermocouple",  # 3温度/熱電対 1EM/1PF
    "030310FF": "current_pulse",  # 電流・パルス 1MU
    "030313FF": "voltage_pulse",  # 電圧・パルス 1RU
    "030312FF": "CT",  # CT 1MT/1NT
    "03030900": "vibration",  # 振動（加速度） 1LZ
    "03030901": "vibration",  # 振動（加速度）レンジオーバー 1LZ
    "03031800": "vibration_speed",  # 振動（速度） 1TF
    "03031801": "vibration_speed",  # 振動（速度）レンジオーバー 1TF
    "03031BFF": "3_current",  # 3電流 1ZU
    "03031CFF": "3_voltage",  # 3電圧 1ZV
    "03031DFF": "3_contacts",  # 3接点 1ZS
    "03031EFF": "water_leak",  # 漏水センサ 2AX
    "0303FEFF": "waterproof_repeater",  # 防水中継機 2CL
    "030319FF": "plg_duty",  # PLG Duty比監視ユニット 2AU
    "03032600": "brake_current_monitor",  # 無線ブレーキ電流監視ユニット 2DB
    "03032B00": "vibration_with_instruction",  # 計測指示機能付無線振動センサユニット 2DN
    "03032B01": "vibration_with_instruction",  # 計測指示機能付無線振動センサユニット 2DN (レンジオーバー)
    "030331FF": "compact_thermocouple",  # 小型熱電対ユニット 2FW
    "03033AFF": "solar_external_sensor",  # 外部センサ用ソーラーユニット 2SL
    "03033A00": "solar_external_sensor",  # 外部センサ用ソーラーユニット 2SL (接点パルスモード)
    "03033A02": "solar_external_sensor",  # 外部センサ用ソーラーユニット 2SL (内部エラー)
    "030330FF": "contact_output",  # 接点出力ユニット 2ST
    "030333FF": "analog_meter_reader",  # アナログメーター読取ユニット 2YT
    "03032F00": "vibration_2tf001_speed",  # 振動 2TF-001（速度モード/低速回転モード）
    "03032F01": "vibration_2tf001_speed",  # 振動 2TF-001（速度モード）レンジオーバー
    "03033200": "vibration_2tf001_accel",  # 振動 2TF-001（加速度モード）
    "03033201": "vibration_2tf001_accel",  # 振動 2TF-001（加速度モード）レンジオーバー
}

UNIT_TYPE = {
    "01": {"name": "Duty比", "unit": "%"},
    "02": {"name": "圧力", "unit": "Pa"},
    "07": {"name": "カウント", "unit": "Time"},
    "0B": {"name": "角度", "unit": "deg"},
    "0C": {"name": "加速度", "unit": "m/s2"},
    "18": {"name": "時間", "unit": "sec"},
    "1C": {"name": "周期", "unit": "sec"},
    "26": {"name": "周波数", "unit": "Hz"},
    "29": {"name": "インデックス", "unit": "-"},
    "2A": {"name": "セルシウス温度", "unit": "℃"},
    "2C": {"name": "相対湿度", "unit": "%RH"},
    "32": {"name": "電位差（電圧）", "unit": "V"},
    "39": {"name": "電流", "unit": "A"},
    "61": {"name": "磁力強度", "unit": "-"},
    "62": {"name": "電流", "unit": "mA"},
    "63": {"name": "加速度実効値", "unit": "m/s2"},
    "66": {"name": "尖度", "unit": "-"},
    "68": {"name": "単位なし", "unit": "-"},
    "69": {"name": "電力", "unit": "W"},
    "6A": {"name": "流量", "unit": "L/min"},
    "6B": {"name": "体積", "unit": "L"},
    "71": {"name": "角度", "unit": "rad"},
    "72": {"name": "速度", "unit": "mm/s"},
    "73": {"name": "変位", "unit": "mm"},
    "74": {"name": "速度実効値", "unit": "mm/s"},
    "80": {"name": "容量パーセント", "unit": "%"},
    "83": {"name": "日数", "unit": "day"},
    "96": {"name": "高さ", "unit": "m"},
    "FA": {"name": "シリアルNo", "unit": "-"},
    "FE": {"name": "レンジオーバー", "unit": "-"},
    "FF": {"name": "異常", "unit": "-"},
}

SCALE = {
    "00": 1,  # x1
    "01": 10,  # x10
    "02": 100,  # x100
    "03": 1000,  # x1000
    "04": 0.1,  # x0.1
    "05": 0.01,  # x0.01
    "06": 0.001,  # x0.001
    "80": -1,  # x(-1)
    "81": -10,  # x(-10)
    "82": -100,  # x(-100)
    "83": -1000,  # x(-1000)
    "84": -0.1,  # x(-0.1)
    "85": -0.01,  # x(-0.01)
    "86": -0.001,  # x(-0.001)
    "FF": 0,  # 無効データ
}


class MurataSensorBase(object):
    """
    村田製作所製センサーの基底クラス

    センサーデータの受信と解析を行う基本機能を提供。

    Attributes:
        data (bytes): 受信した電文データ
        info (dict): センサー情報を格納する辞書
        payload_length (int): ペイロードの長さ
        payload (bytes): ペイロードデータ
        values (dict): 解析したセンサー値
    """

    data: bytes
    info: Dict[str, Any]
    payload_length: int
    payload: bytes
    values: Dict[str, Any]
    logger: logging.Logger

    def __init__(
        self,
        data: bytes,
        addr: Tuple[Optional[str], Optional[int]] = (None, None),
    ) -> None:
        """
        Args:
            data: 受信した電文
            addr: IPアドレスとポート番号 ('xxx.xxx.xxx.xxx', 9999)

        Raises:
            FailedCheckSum: 電文全体のチェックサムが不正な場合
            FailedCheckSumPayload: ペイロードのチェックサムが不正な場合
        """
        self.logger = logging.getLogger(__name__)
        self.data = data
        self.info = {"addr": addr}
        self._parse_data()
        self._validate_checksums()
        self._get_sensor_info()
        self.retrieve_values()

        # RSSI値の計算（16進数の文字列から10進数に変換し、-107を加算）
        rssi_hex = data[23:25].decode()
        self.info["RSSI"] = int(rssi_hex, 16) - 107

        # 経路情報の解析
        route_info = data.decode().split()[-1]
        self.info["route"] = self._parse_route_info(route_info)

    def _parse_data(self) -> None:
        """電文データの基本的な解析を行う"""
        self.payload_length = int(self.data[31:33], 16)
        self.payload = self.data[33 + 1 : 33 + 1 + self.payload_length]
        self.values = {}

    def _validate_checksums(self) -> None:
        """チェックサムの検証を行う"""
        if not self._check_data():
            raise FailedCheckSum()
        if self.payload_length % 8 != 0 and not self._check_payload():
            raise FailedCheckSumPayload()

    def _check_data(self) -> bool:
        """電文全体のチェックサム

        Returns:

        """
        target = self.data[: 33 + 1 + self.payload_length]
        sum_value = self.data[
            33 + self.payload_length + 1 : 33 + self.payload_length + 1 + 2
        ]
        return self._check_sum(target, sum_value)

    def _check_payload(self) -> bool:
        """ペイロードのチェックサム

        Returns:

        """
        payload_target = self.payload[:-2]
        payload_sum_value = self.payload[-2:]
        return self._check_sum(payload_target, payload_sum_value)

    def _check_sum(self, target: bytes, sum_value: bytes) -> bool:
        """チェックサム共通処理

        Args:
            target: チェック対象
            sum_value: チェックサムの結果

        Returns:
            チェックサムが正しければTrue
        """
        try:
            # 空白文字(0x20)を含めて1文字ずつXOR計算
            result = 0
            for byte in target:
                result ^= byte

            # 計算結果を2文字の16進数文字列に変換
            calculated = format(result, "02X")
            expected = sum_value.decode()

            return bool(calculated == expected)

        except Exception as e:
            self.logger.error(f"Checksum calculation error: {str(e)}")
            return False

    def _get_sensor_info(self) -> None:
        """電文のペイロード外の情報を取得"""
        self.info["unit_id"] = self.data[8:12].decode("utf-8")
        self.info["message_id"] = self.data[18:22].decode("utf-8")

        # センサ種別コード [tt] をペイロード先頭から取得
        # 形式: 0303[tt][SS]...
        # payload[0:4] == b"0303" を前提とし、その直後の 2 文字をセンサ種別コードとして扱う
        try:
            type_code_bytes = self.payload[4:6]
            type_code = type_code_bytes.decode()
            self.info["sensor_type_code"] = type_code
        except Exception as e:
            # 予期しないフォーマットの場合はログのみ出力し、センサ種別コードは設定しない
            self.logger.error(f"Failed to parse sensor_type_code: {str(e)}")

        # センサー状態の解析を追加
        sensor_status = self.payload[6:8].decode()
        self.info["status"] = self._parse_sensor_status(sensor_status)

    def _parse_sensor_status(self, status: str) -> Dict[str, Any]:
        """センサー状態を解析する

        Args:
            status: センサー状態コード

        Returns:
            状態を示す辞書
        """
        if self.check_sensor_type(self.data) == "vibration":
            return {
                "code": status,
                "description": "正常" if status == "00" else "レンジオーバー",
            }
        else:
            return {
                "code": status,
                "description": "固定値(FF)" if status == "FF" else "不明な状態",
            }

    def _get_value(self, val_hex_text: bytes) -> Dict[str, Any]:
        """ペイロード内の個別のデータを返す

        例
        0303[tt][SS]01260532[ddddssuu]

        0303 ：固定（センサデータ通知）
        [tt] ：センサ種別
        [SS] ：状態 その他ユニッット（FF固定)
        振動ユニット（00：正常/01：レンジオーバ）
        01260532 ：電源電圧
        [ddddssuu] ：センサデータ（種別により数がことなる）
        電源電圧・センサデータフォーマット
        dddd ：データ（16進数）
        ss ：スケール
        uu ：単位

        Args:
            val_hex_text: bytes (12)

        Returns: dict
            例
            {
                'value': 2.94,
                'unit': 'V',
                'unit_name': '電位差（電圧）'
            }
            無効値の場合（FFFF## または ##FF##）:
            {
                'value': None,
                'unit': 'V',
                'unit_name': '電位差（電圧）'
            }
        """
        scale = val_hex_text[4:6]
        unit = val_hex_text[6:8]
        
        # 無効値判定: データ部分がFFFFまたはスケールがFF
        data_hex = val_hex_text[0:4].decode()
        scale_str = scale.decode()
        
        if data_hex == "FFFF" or scale_str == "FF":
            return {
                "value": None,
                "unit": UNIT_TYPE[unit.decode()]["unit"],
                "unit_name": UNIT_TYPE[unit.decode()]["name"],
            }
        
        return {
            "value": round(int(data_hex, 16) * SCALE[scale_str], 10),
            "unit": UNIT_TYPE[unit.decode()]["unit"],
            "unit_name": UNIT_TYPE[unit.decode()]["name"],
        }

    def __str__(self) -> str:
        return_string = ""
        return_string += "info: {},\n".format(self.info)
        return_string += "type: {},\n".format(self.check_sensor_type(self.data))
        return_string += "data: {},\n".format(
            self.data.decode("utf-8", errors="replace")
        )
        return_string += "payload: {},\n".format(
            self.payload.decode("utf-8", errors="replace")
        )
        return_string += "values: {},\n".format(self.values)
        return return_string

    def retrieve_values(self) -> None:
        """ペイロードのデータを個別に分解する関数
        詳細は継承先でオーバーライドする
        """
        pass

    @classmethod
    def is_murata_sensor_data(cls, data: bytes) -> bool:
        """村田製作所製センサーからの受信かを判定

        Args:
            data: 受信した電文全体

        Returns:

        """
        return data[0:7].decode() == "ERXDATA"

    @classmethod
    def check_sensor_type(cls, data: bytes) -> Optional[str]:
        """電文からセンサータイプを特定して返す

        Args:
            data: 受信した電文全体

        Returns: センサータイプ（不明な場合はNone）

        """
        d = data.decode("utf-8")
        c = d[34:42]
        return SENSOR_TYPE.get(c)

    def _parse_route_info(self, route_info: str) -> List[str]:
        """経路情報を解析する

        Args:
            route_info: 経路情報の文字列

        Returns:
            経路情報のリスト。最後の要素はGatewayのID
        """
        return route_info.split()


# ------------------------------------------------------------------------------------------------
# 以下、個別のセンサークラス群
# ------------------------------------------------------------------------------------------------


class VibrationSensor(MurataSensorBase):
    """振動ユニット（加速度版 1LZ）
    
    FFT有効時: ピーク周波数・加速度1-5を含む全14項目を出力
    FFT無効時: ピーク値は無効（value=None）として出力
    """

    def __init__(
        self,
        data: bytes,
        addr: Tuple[Optional[str], Optional[int]] = (None, None),
    ) -> None:
        super(VibrationSensor, self).__init__(data, addr)

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # センサデータ（ピーク周波数1）：[Hz]
        self.values["peak-frequency-1"] = self._get_value(self.payload[16:24])
        # センサデータ（ピーク加速度1）：[m/s2]
        self.values["peak-acceleration-1"] = self._get_value(self.payload[24:32])
        # センサデータ（ピーク周波数2）：[Hz]
        self.values["peak-frequency-2"] = self._get_value(self.payload[32:40])
        # センサデータ（ピーク加速度2）：[m/s2]
        self.values["peak-acceleration-2"] = self._get_value(self.payload[40:48])
        # センサデータ（ピーク周波数3）：[Hz]
        self.values["peak-frequency-3"] = self._get_value(self.payload[48:56])
        # センサデータ（ピーク加速度3）：[m/s2]
        self.values["peak-acceleration-3"] = self._get_value(self.payload[56:64])
        # センサデータ（ピーク周波数4）：[Hz]
        self.values["peak-frequency-4"] = self._get_value(self.payload[64:72])
        # センサデータ（ピーク加速度4）：[m/s2]
        self.values["peak-acceleration-4"] = self._get_value(self.payload[72:80])
        # センサデータ（ピーク周波数5）：[Hz]
        self.values["peak-frequency-5"] = self._get_value(self.payload[80:88])
        # センサデータ（ピーク加速度5）：[m/s2]
        self.values["peak-acceleration-5"] = self._get_value(self.payload[88:96])
        # センサデータ（加速度RMS） ：[m/s2]
        self.values["acceleration-RMS"] = self._get_value(self.payload[96:104])
        # センサデータ（尖度）
        self.values["kurtosis"] = self._get_value(self.payload[104:112])
        # センサデータ（温度）
        self.values["temperature"] = self._get_value(self.payload[112:120])


class VibrationSpeed(MurataSensorBase):
    """振動（速度）ユニット"""

    def __init__(
        self,
        data: bytes,
        addr: Tuple[Optional[str], Optional[int]] = (None, None),
    ) -> None:
        super(VibrationSpeed, self).__init__(data, addr)

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # センサデータ（ピーク周波数１） ：[Hz]
        self.values["peak-frequency-1"] = self._get_value(self.payload[16:24])
        # センサデータ（ピーク加速度１） ：[m/s2]
        self.values["peak-acceleration-1"] = self._get_value(self.payload[24:32])
        # センサデータ（ピーク周波数２） ：[Hz]
        self.values["peak-frequency-2"] = self._get_value(self.payload[32:40])
        # センサデータ（ピーク加速度２） ：[m/s2]
        self.values["peak-acceleration-2"] = self._get_value(self.payload[40:48])
        # センサデータ（加速度RMS） ：[m/s2]
        self.values["acceleration-RMS"] = self._get_value(self.payload[48:56])
        # センサデータ（速度ピーク周波数１） ：[Hz]
        self.values["speed-peak-frequency-1"] = self._get_value(self.payload[56:64])
        # センサデータ（ピーク速度１） ：[mm/s]
        self.values["peak-speed-1"] = self._get_value(self.payload[64:72])
        # センサデータ（速度ピーク周波数２） ：[Hz]
        self.values["speed-peak-frequency-2"] = self._get_value(self.payload[72:80])
        # センサデータ（ピーク速度２） ：[mm/s]
        self.values["peak-speed-2"] = self._get_value(self.payload[80:88])
        # センサデータ（速度ピーク周波数３） ：[Hz]
        self.values["speed-peak-frequency-3"] = self._get_value(self.payload[88:96])
        # センサデータ（ピーク速度３） ：[mm/s]
        self.values["peak-speed-3"] = self._get_value(self.payload[96:104])
        # センサデータ（速度RMS） ：[mm/s]
        self.values["speed-RMS"] = self._get_value(self.payload[104:112])
        # センサデータ（尖度） ：[-]
        self.values["kurtosis"] = self._get_value(self.payload[112:120])
        # センサデータ（温度） ：[℃]
        self.values["temperature"] = self._get_value(self.payload[120:128])


class TemperatureAndHumiditySensor(MurataSensorBase):
    """温湿度ユニット"""

    def __init__(
        self,
        data: bytes,
        addr: Tuple[Optional[str], Optional[int]] = (None, None),
    ) -> None:
        super(TemperatureAndHumiditySensor, self).__init__(data, addr)

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # センサデータ（温度） ：[℃]]
        self.values["temperature"] = self._get_value(self.payload[16:24])
        # センサデータ（湿度）：[%RH]
        self.values["humidity"] = self._get_value(self.payload[24:32])


class ThreeTemperatureSensor(MurataSensorBase):
    """3温度ユニット"""

    def __init__(
        self,
        data: bytes,
        addr: Tuple[Optional[str], Optional[int]] = (None, None),
    ) -> None:
        super(ThreeTemperatureSensor, self).__init__(data, addr)

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # センサデータ（温度1） ：[℃]
        self.values["temperature1"] = self._get_value(self.payload[16:24])
        # センサデータ（温度2） ：[℃]
        self.values["temperature2"] = self._get_value(self.payload[24:32])
        # センサデータ（温度3） ：[℃]
        self.values["temperature3"] = self._get_value(self.payload[32:40])


class CurrentPulseSensor(MurataSensorBase):
    """電流・パルスセンサー"""

    def __init__(
        self,
        data: bytes,
        addr: Tuple[Optional[str], Optional[int]] = (None, None),
    ) -> None:
        super(CurrentPulseSensor, self).__init__(data, addr)

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # センサデータ（電流値） ：[mA]
        self.values["current"] = self._get_value(self.payload[16:24])
        # センサデータ（パルスカウント） ：[Time]
        self.values["pulse-count"] = self._get_value(self.payload[24:32])


class VoltagePulseSensor(MurataSensorBase):
    """電圧・パルスセンサー"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # センサデータ（カウンタ）
        self.values["counter"] = self._get_value(self.payload[16:24])
        # センサデータ（電圧）：[V]
        self.values["voltage"] = self._get_value(self.payload[24:32])
        # センサデータ（パルスカウント）：[Time]
        self.values["pulse-count"] = self._get_value(self.payload[32:40])
        # センサデータ（前回電圧）：[V]
        self.values["previous-voltage"] = self._get_value(self.payload[40:48])
        # センサデータ（前回パルスカウント）：[Time]
        self.values["previous-pulse-count"] = self._get_value(self.payload[48:56])


class CTSensor(MurataSensorBase):
    """CTセンサー"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # センサデータ（カウンタ）
        self.values["counter"] = self._get_value(self.payload[16:24])
        # センサデータ（電流1）：[A]
        self.values["current1"] = self._get_value(self.payload[24:32])
        # センサデータ（電流2）：[A]
        self.values["current2"] = self._get_value(self.payload[32:40])
        # センサデータ（借電）
        self.values["power-borrowing"] = self._get_value(self.payload[40:48])
        # センサデータ（前回電流1）：[A]
        self.values["previous-current1"] = self._get_value(self.payload[48:56])
        # センサデータ（前回電流2）：[A]
        self.values["previous-current2"] = self._get_value(self.payload[56:64])
        # センサデータ（前回借電）
        self.values["previous-power-borrowing"] = self._get_value(self.payload[64:72])


class ThreeCurrentSensor(MurataSensorBase):
    """3電流ユニット"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # センサデータ（電流値1）：[mA]
        self.values["current1"] = self._get_value(self.payload[32:40])
        # センサデータ（電流値2）：[mA]
        self.values["current2"] = self._get_value(self.payload[40:48])
        # センサデータ（電流値3）：[mA]
        self.values["current3"] = self._get_value(self.payload[48:56])


class ThreeVoltageSensor(MurataSensorBase):
    """3電圧ユニット"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # センサデータ（電圧値1）：[V]
        self.values["voltage1"] = self._get_value(self.payload[32:40])
        # センサデータ（電圧値2）：[V]
        self.values["voltage2"] = self._get_value(self.payload[40:48])
        # センサデータ（電圧値3）：[V]
        self.values["voltage3"] = self._get_value(self.payload[48:56])


class ThreeContactSensor(MurataSensorBase):
    """3接点ユニット"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # センサデータ（検出エッジ1）
        self.values["edge1"] = self._get_value(self.payload[32:40])
        # センサデータ（エッジカウント1）
        self.values["edge-count1"] = self._get_value(self.payload[40:48])
        # センサデータ（検出エッジ2）
        self.values["edge2"] = self._get_value(self.payload[48:56])
        # センサデータ（エッジカウント2）
        self.values["edge-count2"] = self._get_value(self.payload[56:64])
        # センサデータ（検出エッジ3）
        self.values["edge3"] = self._get_value(self.payload[64:72])
        # センサデータ（エッジカウント3）
        self.values["edge-count3"] = self._get_value(self.payload[72:80])


class WaterproofRepeater(MurataSensorBase):
    """防水中継機 2CL"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # センサデータ（温度）：[℃]
        self.values["temperature"] = self._get_value(self.payload[32:40])
        # ソーラー電源運用モード時のみ
        if len(self.payload) > 48:
            # ソーラーバッテリー電圧：[V]
            self.values["solar-battery-voltage"] = self._get_value(self.payload[40:48])
            # ソーラーパネル電圧：[V]
            self.values["solar-panel-voltage"] = self._get_value(self.payload[48:56])


class WaterLeakSensor(MurataSensorBase):
    """漏水センサ 2AX"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # CH1漏水有無
        self.values["ch1-water-leak"] = self._get_value(self.payload[32:40])
        # CH2漏水有無
        self.values["ch2-water-leak"] = self._get_value(self.payload[40:48])
        # CH1漏水Index
        self.values["ch1-water-leak-index"] = self._get_value(self.payload[48:56])
        # CH2漏水Index
        self.values["ch2-water-leak-index"] = self._get_value(self.payload[56:64])


class PlgDutySensor(MurataSensorBase):
    """PLG Duty比監視ユニット 2AU"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # High Duty比(CH1)：[%]
        self.values["ch1-high-duty"] = self._get_value(self.payload[32:40])
        # 周期(CH1)：[sec]
        self.values["ch1-period"] = self._get_value(self.payload[40:48])
        # High Duty比(CH2)：[%]
        self.values["ch2-high-duty"] = self._get_value(self.payload[48:56])
        # 周期(CH2)：[sec]
        self.values["ch2-period"] = self._get_value(self.payload[56:64])


class BrakeCurrentMonitor(MurataSensorBase):
    """無線ブレーキ電流監視ユニット 2DB"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # 接点状態(電源)
        self.values["contact-power"] = self._get_value(self.payload[32:40])
        # 接点状態(開指令)
        self.values["contact-open-command"] = self._get_value(self.payload[40:48])
        # 接点状態(強励磁)
        self.values["contact-strong-excitation"] = self._get_value(self.payload[48:56])
        # 接点状態(弱励磁)
        self.values["contact-weak-excitation"] = self._get_value(self.payload[56:64])
        # 電流値(CTセンサ)：[V]
        self.values["ct-current"] = self._get_value(self.payload[64:72])
        # モード(状態表示)
        self.values["mode-status"] = self._get_value(self.payload[72:80])
        # 開指令カウント：[Time]
        self.values["open-command-count"] = self._get_value(self.payload[80:88])
        # パターン設定状態
        self.values["pattern-setting-status"] = self._get_value(self.payload[88:96])
        # 時刻補正経過日数：[day]
        self.values["time-correction-days"] = self._get_value(self.payload[96:104])
        # SDカード空き容量：[%]
        self.values["sd-card-free-space"] = self._get_value(self.payload[104:112])
        # 電源選択状態
        self.values["power-selection-status"] = self._get_value(self.payload[112:120])
        # 異常検出カウント：[Time]
        self.values["error-detection-count"] = self._get_value(self.payload[120:128])


class VibrationWithInstructionSensor(MurataSensorBase):
    """計測指示機能付無線振動センサユニット 2DN"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # センサデータ（ピーク周波数1）：[Hz]
        self.values["peak-frequency-1"] = self._get_value(self.payload[32:40])
        # センサデータ（ピーク加速度1）：[m/s2]
        self.values["peak-acceleration-1"] = self._get_value(self.payload[40:48])
        # センサデータ（ピーク周波数2）：[Hz]
        self.values["peak-frequency-2"] = self._get_value(self.payload[48:56])
        # センサデータ（ピーク加速度2）：[m/s2]
        self.values["peak-acceleration-2"] = self._get_value(self.payload[56:64])
        # センサデータ（加速度RMS）：[m/s2]
        self.values["acceleration-RMS"] = self._get_value(self.payload[64:72])
        # センサデータ（速度ピーク周波数1）：[Hz]
        self.values["speed-peak-frequency-1"] = self._get_value(self.payload[72:80])
        # センサデータ（ピーク速度1）：[mm/s]
        self.values["peak-speed-1"] = self._get_value(self.payload[80:88])
        # センサデータ（速度ピーク周波数2）：[Hz]
        self.values["speed-peak-frequency-2"] = self._get_value(self.payload[88:96])
        # センサデータ（ピーク速度2）：[mm/s]
        self.values["peak-speed-2"] = self._get_value(self.payload[96:104])
        # センサデータ（速度ピーク周波数3）：[Hz]
        self.values["speed-peak-frequency-3"] = self._get_value(self.payload[104:112])
        # センサデータ（ピーク速度3）：[mm/s]
        self.values["peak-speed-3"] = self._get_value(self.payload[112:120])
        # センサデータ（速度RMS）：[mm/s]
        self.values["speed-RMS"] = self._get_value(self.payload[120:128])
        # センサデータ（尖度）：[-]
        self.values["kurtosis"] = self._get_value(self.payload[128:136])
        # センサデータ（温度）：[℃]
        self.values["temperature"] = self._get_value(self.payload[136:144])


class CompactThermocoupleSensor(MurataSensorBase):
    """小型熱電対ユニット 2FW"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # 断線検知
        self.values["disconnection-detection"] = self._get_value(self.payload[32:40])
        # 異常判定(温度上限)
        self.values["temp-upper-limit-error"] = self._get_value(self.payload[40:48])
        # 異常判定(温度上昇幅)
        self.values["temp-rise-error"] = self._get_value(self.payload[48:56])
        # 熱電対温度：[℃]
        self.values["thermocouple-temperature"] = self._get_value(self.payload[56:64])
        # 環境温度：[℃]
        self.values["ambient-temperature"] = self._get_value(self.payload[64:72])
        # 基準温度：[℃]
        self.values["reference-temperature"] = self._get_value(self.payload[72:80])
        # 温度上昇開始からの経過時間
        self.values["elapsed-time-from-temp-rise"] = self._get_value(
            self.payload[80:88]
        )


class SolarExternalSensor(MurataSensorBase):
    """外部センサ用ソーラーユニット 2SL"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]（固定値3.6V）
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # 電池電圧：[V]
        self.values["battery-voltage"] = self._get_value(self.payload[32:40])
        # Ch1検出エッジ
        self.values["ch1-edge"] = self._get_value(self.payload[40:48])
        # Ch1エッジカウント下位：[回]
        self.values["ch1-edge-count-lower"] = self._get_value(self.payload[48:56])
        # Ch1エッジカウント上位：[回]
        self.values["ch1-edge-count-upper"] = self._get_value(self.payload[56:64])
        # Ch2検出エッジ
        self.values["ch2-edge"] = self._get_value(self.payload[64:72])
        # Ch2エッジカウント下位：[回]
        self.values["ch2-edge-count-lower"] = self._get_value(self.payload[72:80])
        # Ch2エッジカウント上位：[回]
        self.values["ch2-edge-count-upper"] = self._get_value(self.payload[80:88])
        # Ch1電流：[mA]
        self.values["ch1-current"] = self._get_value(self.payload[88:96])
        # Ch2電流：[mA]
        self.values["ch2-current"] = self._get_value(self.payload[96:104])
        # Ch1電圧：[V]
        self.values["ch1-voltage"] = self._get_value(self.payload[104:112])
        # Ch2電圧：[V]
        self.values["ch2-voltage"] = self._get_value(self.payload[112:120])
        # 温度：[℃]
        self.values["temperature"] = self._get_value(self.payload[120:128])
        # 高さ：[m]
        self.values["altitude"] = self._get_value(self.payload[128:136])
        # 緯度・経度はペイロード長により存在するかを確認
        if len(self.payload) > 160:
            # 緯度（x10000000[deg]）
            lat_raw = int(self.payload[144:152].decode(), 16)
            self.values["latitude"] = lat_raw / 10000000.0
            # 経度（x10000000[deg]）
            lon_raw = int(self.payload[152:160].decode(), 16)
            self.values["longitude"] = lon_raw / 10000000.0


class ContactOutputSensor(MurataSensorBase):
    """接点出力ユニット 2ST"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # 動作モード
        self.values["operation-mode"] = self._get_value(self.payload[32:40])
        # 接点1の状態
        self.values["contact1-status"] = self._get_value(self.payload[40:48])
        # 接点1残り出力継続時間：[sec]
        self.values["contact1-remaining-output-time"] = self._get_value(
            self.payload[48:56]
        )
        # 接点1残り無視時間：[sec]
        self.values["contact1-remaining-ignore-time"] = self._get_value(
            self.payload[56:64]
        )
        # 接点2の状態
        self.values["contact2-status"] = self._get_value(self.payload[64:72])
        # 接点2残り出力継続時間：[sec]
        self.values["contact2-remaining-output-time"] = self._get_value(
            self.payload[72:80]
        )
        # 接点2残り無視時間：[sec]
        self.values["contact2-remaining-ignore-time"] = self._get_value(
            self.payload[80:88]
        )


class AnalogMeterReaderSensor(MurataSensorBase):
    """アナログメーター読取ユニット 2YT"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # CH1角度：[deg]
        self.values["ch1-angle"] = self._get_value(self.payload[32:40])
        # CH1角度(Min)：[deg]
        self.values["ch1-angle-min"] = self._get_value(self.payload[40:48])
        # CH1角度(Max)：[deg]
        self.values["ch1-angle-max"] = self._get_value(self.payload[48:56])
        # CH1補正値：[deg]
        self.values["ch1-correction"] = self._get_value(self.payload[56:64])
        # CH1磁力強度：[-]
        self.values["ch1-magnetic-strength"] = self._get_value(self.payload[64:72])
        # CH2角度：[deg]
        self.values["ch2-angle"] = self._get_value(self.payload[72:80])
        # CH2角度(Min)：[deg]
        self.values["ch2-angle-min"] = self._get_value(self.payload[80:88])
        # CH2角度(Max)：[deg]
        self.values["ch2-angle-max"] = self._get_value(self.payload[88:96])
        # CH2補正値：[deg]
        self.values["ch2-correction"] = self._get_value(self.payload[96:104])
        # CH2磁力強度：[-]
        self.values["ch2-magnetic-strength"] = self._get_value(self.payload[104:112])


class Vibration2TF001SpeedSensor(MurataSensorBase):
    """振動 2TF-001（速度モード/低速回転モード）"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # センサデータ（ピーク周波数1）：[Hz]
        self.values["peak-frequency-1"] = self._get_value(self.payload[32:40])
        # センサデータ（ピーク加速度1）：[m/s2]
        self.values["peak-acceleration-1"] = self._get_value(self.payload[40:48])
        # センサデータ（ピーク周波数2）：[Hz]
        self.values["peak-frequency-2"] = self._get_value(self.payload[48:56])
        # センサデータ（ピーク加速度2）：[m/s2]
        self.values["peak-acceleration-2"] = self._get_value(self.payload[56:64])
        # センサデータ（加速度RMS）：[m/s2]
        self.values["acceleration-RMS"] = self._get_value(self.payload[64:72])
        # センサデータ（速度ピーク周波数1）：[Hz]
        self.values["speed-peak-frequency-1"] = self._get_value(self.payload[72:80])
        # センサデータ（ピーク速度1）：[mm/s]
        self.values["peak-speed-1"] = self._get_value(self.payload[80:88])
        # センサデータ（速度ピーク周波数2）：[Hz]
        self.values["speed-peak-frequency-2"] = self._get_value(self.payload[88:96])
        # センサデータ（ピーク速度2）：[mm/s]
        self.values["peak-speed-2"] = self._get_value(self.payload[96:104])
        # センサデータ（速度ピーク周波数3）：[Hz]
        self.values["speed-peak-frequency-3"] = self._get_value(self.payload[104:112])
        # センサデータ（ピーク速度3）：[mm/s]
        self.values["peak-speed-3"] = self._get_value(self.payload[112:120])
        # センサデータ（速度RMS）：[mm/s]
        self.values["speed-RMS"] = self._get_value(self.payload[120:128])
        # センサデータ（尖度）：[-]
        self.values["kurtosis"] = self._get_value(self.payload[128:136])
        # センサデータ（温度）：[℃]
        self.values["temperature"] = self._get_value(self.payload[136:144])


class Vibration2TF001AccelSensor(MurataSensorBase):
    """振動 2TF-001（加速度モード）"""

    def retrieve_values(self) -> None:
        # 電源電圧：[V]
        self.values["power-supply-voltage"] = self._get_value(self.payload[8:16])
        # シリアルナンバー
        serial_upper = self.payload[16:24].decode()
        serial_lower = self.payload[24:32].decode()
        self.info["serial_number"] = serial_upper + serial_lower
        # センサデータ（ピーク周波数1）：[Hz]
        self.values["peak-frequency-1"] = self._get_value(self.payload[32:40])
        # センサデータ（ピーク加速度1）：[m/s2]
        self.values["peak-acceleration-1"] = self._get_value(self.payload[40:48])
        # センサデータ（ピーク周波数2）：[Hz]
        self.values["peak-frequency-2"] = self._get_value(self.payload[48:56])
        # センサデータ（ピーク加速度2）：[m/s2]
        self.values["peak-acceleration-2"] = self._get_value(self.payload[56:64])
        # センサデータ（ピーク周波数3）：[Hz]
        self.values["peak-frequency-3"] = self._get_value(self.payload[64:72])
        # センサデータ（ピーク加速度3）：[m/s2]
        self.values["peak-acceleration-3"] = self._get_value(self.payload[72:80])
        # センサデータ（ピーク周波数4）：[Hz]
        self.values["peak-frequency-4"] = self._get_value(self.payload[80:88])
        # センサデータ（ピーク加速度4）：[m/s2]
        self.values["peak-acceleration-4"] = self._get_value(self.payload[88:96])
        # センサデータ（ピーク周波数5）：[Hz]
        self.values["peak-frequency-5"] = self._get_value(self.payload[96:104])
        # センサデータ（ピーク加速度5）：[m/s2]
        self.values["peak-acceleration-5"] = self._get_value(self.payload[104:112])
        # センサデータ（加速度RMS）：[m/s2]
        self.values["acceleration-RMS"] = self._get_value(self.payload[112:120])
        # センサデータ（尖度）：[-]
        self.values["kurtosis"] = self._get_value(self.payload[120:128])
        # センサデータ（温度）：[℃]
        self.values["temperature"] = self._get_value(self.payload[128:136])
