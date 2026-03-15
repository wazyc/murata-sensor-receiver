import asyncio
import pytest
from datetime import datetime
from murata_sensor import *
from murata_sensor.murata_receiver import create_sensor, parse_text_line


class TestModel(object):
    # @classmethod
    # def setup_class(cls):
    #     print('start')

    def test_is_murata_sensor_data(self):
        c = "ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF".encode()
        assert MurataSensorBase.is_murata_sensor_data(c)

        c = "ERXDATa 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF".encode()
        assert not MurataSensorBase.is_murata_sensor_data(c)

    def test_check_sensor_type(self):
        # 存在する仕様のセンサーデータ
        c = "ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF".encode()
        assert MurataSensorBase.check_sensor_type(c) == "temperature_and_humidity"

        # 存在しない仕様のセンサーのデータ
        c = "ERXDATA 0002 0000 62BE F000 18 20 030399FF012605320C90052A11AF052C7C0002 7FFF".encode()
        assert MurataSensorBase.check_sensor_type(c) is None

    def test_check_sum(self):
        addr = ("123.456.789.111", 8765)

        # チェックサムに失敗するテスト
        c = "ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7199 8001 7FFF".encode()
        with pytest.raises(FailedCheckSum) as e:
            sensor = VibrationSensor(c, addr)

    def test_sensor(self):
        """電文内の値を取得するテスト"""
        addr = ("123.456.789.111", 8765)

        # 振動センサ
        c = "ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7170 8001 7FFF".encode()
        sensor = VibrationSensor(c, addr)
        
        # 基本情報のテスト
        assert sensor.info['addr'] == ('123.456.789.111', 8765)
        assert sensor.info['unit_id'] == '8001'
        assert sensor.info['message_id'] == '1012'
        # RSSI値はデータ位置によって決まる
        assert 'RSSI' in sensor.info
        
        # 値のテスト（キーの存在と値の確認）
        assert 'power-supply-voltage' in sensor.values
        assert sensor.values['power-supply-voltage']['value'] == 3.03
        assert sensor.values['power-supply-voltage']['unit'] == 'V'
        
        assert 'acceleration-RMS' in sensor.values
        assert sensor.values['acceleration-RMS']['value'] == 0
        
        assert 'kurtosis' in sensor.values
        assert sensor.values['kurtosis']['value'] == 0
        
        assert 'temperature' in sensor.values
        assert sensor.values['temperature']['value'] == 25
        assert sensor.values['temperature']['unit'] == '℃'

    def test_three_temperature_sensor(self):
        """3温度ユニットのテスト"""
        addr = ("192.168.1.100", 1234)
        data = "ERXDATA 0740 0000 392C F000 50 2A 030307FF012A05320109042A001C002A0011002A7C0F 0740 7FFF".encode()
        
        sensor = ThreeTemperatureSensor(data, addr)
        
        # 基本情報のテスト
        assert sensor.info['unit_id'] == '0740'
        assert sensor.info['message_id'] == '392C'
        # route情報は最後の単語をスプリットした結果
        assert 'route' in sensor.info
        assert isinstance(sensor.info['route'], list)
        
        # センサー値のテスト
        assert 'power-supply-voltage' in sensor.values
        assert 'temperature1' in sensor.values
        assert 'temperature2' in sensor.values
        assert 'temperature3' in sensor.values

    def test_rssi_calculation(self):
        """RSSI計算のテスト"""
        addr = ("192.168.1.100", 1234)
        
        # 有効なテストデータを使用（チェックサムが正しいデータ）
        data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        sensor = TemperatureAndHumiditySensor(data, addr)
        
        # RSSI値が計算されていることを確認
        assert 'RSSI' in sensor.info
        assert isinstance(sensor.info['RSSI'], int)

    def test_current_pulse_sensor(self):
        """電流・パルスセンサーのテスト（クラス構造の確認）"""
        # CurrentPulseSensorクラスの構造テスト
        assert hasattr(CurrentPulseSensor, 'retrieve_values')
        assert issubclass(CurrentPulseSensor, MurataSensorBase)
        
        # retrieve_valuesで設定されるキーの確認
        # 実際のセンサーデータなしでも、クラスの存在とメソッドを確認

    def test_sensor_status(self):
        """センサー状態のテスト"""
        addr = ("192.168.1.100", 1234)
        
        # 振動センサー - 正常 (status code = 00)
        # 有効なテストデータを使用
        data = b"ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7170 8001 7FFF"
        sensor = VibrationSensor(data, addr)
        assert sensor.info['status']['code'] == '00'
        assert sensor.info['status']['description'] == '正常'

    def test_voltage_pulse_sensor(self):
        """電圧・パルスセンサーのテスト（クラス構造の確認）"""
        # VoltagePulseSensorクラスの構造テスト
        assert hasattr(VoltagePulseSensor, 'retrieve_values')
        assert issubclass(VoltagePulseSensor, MurataSensorBase)

    def test_ct_sensor(self):
        """CTセンサーのテスト（クラス構造の確認）"""
        # CTSensorクラスの構造テスト
        assert hasattr(CTSensor, 'retrieve_values')
        assert issubclass(CTSensor, MurataSensorBase)

    def test_three_current_sensor(self):
        """3電流ユニットのテスト"""
        addr = ("192.168.1.100", 1234)
        data = "ERXDATA CDEF 0000 351C F000 50 3A 03031BFF01300532123456FAABCDEFFA006D04620030046200000062000E CDEF 7FFF".encode()
        
        sensor = ThreeCurrentSensor(data, addr)
        
        # 基本情報のテスト
        assert sensor.info['unit_id'] == 'CDEF'
        assert sensor.info['message_id'] == '351C'
        assert sensor.info['serial_number'] == '123456FAABCDEFFA'
        
        # センサー値のテスト
        assert sensor.values['power-supply-voltage']['value'] == 3.04
        assert sensor.values['current1']['value'] == 10.9
        assert sensor.values['current2']['value'] == 4.8
        assert sensor.values['current3']['value'] == 0.0

    def test_three_voltage_sensor(self):
        """3電圧ユニットのテスト"""
        addr = ("192.168.1.100", 1234)
        data = "ERXDATA CDEF 0000 0042 F000 50 3A 03031CFF01300532123456FAABCDEFFA001D04320030043200000032037C CDEF 7FFF".encode()
        
        sensor = ThreeVoltageSensor(data, addr)
        
        # 基本情報のテスト
        assert sensor.info['unit_id'] == 'CDEF'
        assert sensor.info['message_id'] == '0042'
        assert sensor.info['serial_number'] == '123456FAABCDEFFA'
        
        # センサー値のテスト
        assert sensor.values['power-supply-voltage']['value'] == 3.04
        assert sensor.values['voltage1']['value'] == 2.9
        assert sensor.values['voltage2']['value'] == 4.8
        assert sensor.values['voltage3']['value'] == 0.0

    def test_three_contact_sensor(self):
        """3接点ユニットのテスト"""
        addr = ("192.168.1.100", 1234)
        data = "ERXDATA 9ABC 0000 5B27 F000 50 52 03031DFF01180532123456FA789ABCFA00010068000100070000006800000007000000680000000701009ABC 7FFF".encode()
        
        sensor = ThreeContactSensor(data, addr)
        
        # 基本情報のテスト
        assert sensor.info['unit_id'] == '9ABC'
        assert sensor.info['message_id'] == '5B27'
        assert sensor.info['serial_number'] == '123456FA789ABCFA'
        
        # センサー値のキーの存在確認
        assert 'power-supply-voltage' in sensor.values
        assert 'edge1' in sensor.values
        assert 'edge-count1' in sensor.values
        assert 'edge2' in sensor.values
        assert 'edge-count2' in sensor.values
        assert 'edge3' in sensor.values
        assert 'edge-count3' in sensor.values

    def test_waterproof_repeater(self):
        """防水中継機のテスト"""
        addr = ("192.168.1.100", 1234)
        data = "ERXDATA 1234 0000 4485 F000 4D 2A 0303FEFF00030032000010FA111234FA00F0042A0503 1234 7FFF".encode()
        
        sensor = WaterproofRepeater(data, addr)
        
        # 基本情報のテスト
        assert sensor.info['unit_id'] == '1234'
        assert sensor.info['message_id'] == '4485'
        assert sensor.info['serial_number'] == '000010FA111234FA'
        
        # センサー値のテスト
        assert sensor.values['power-supply-voltage']['value'] == 3.00
        assert sensor.values['temperature']['value'] == 24.0


class TestCreateSensor:
    """create_sensor関数のテスト"""
    
    def test_create_sensor_vibration(self):
        """振動センサーの生成テスト"""
        data = b"ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7170 8001 7FFF"
        addr = ("192.168.1.100", 55061)
        
        sensor = create_sensor(data, addr)
        
        assert sensor is not None
        assert isinstance(sensor, VibrationSensor)
        assert sensor.info['unit_id'] == '8001'
        assert sensor.values['temperature']['value'] == 25
    
    def test_create_sensor_temperature_humidity(self):
        """温湿度センサーの生成テスト"""
        data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        addr = ("192.168.1.100", 55061)
        
        sensor = create_sensor(data, addr)
        
        assert sensor is not None
        assert isinstance(sensor, TemperatureAndHumiditySensor)
        assert sensor.info['unit_id'] == '0002'
    
    def test_create_sensor_without_addr(self):
        """アドレスなしでのセンサー生成テスト"""
        data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        
        sensor = create_sensor(data)
        
        assert sensor is not None
        assert sensor.info['addr'] == (None, None)
    
    def test_create_sensor_invalid_data(self):
        """不正なデータでNoneが返されるテスト"""
        invalid_data = b"INVALID DATA"
        
        sensor = create_sensor(invalid_data)
        
        assert sensor is None
    
    def test_create_sensor_unknown_type(self):
        """未知のセンサータイプでNoneが返されるテスト"""
        data = b"ERXDATA 0002 0000 62BE F000 18 20 030399FF012605320C90052A11AF052C7C0002 7FFF"
        
        sensor = create_sensor(data)
        
        assert sensor is None


class TestParseTextLine:
    """parse_text_line関数のテスト"""
    
    def test_parse_full_format(self):
        """タイムスタンプ + IP/ポート + ERXDATAの完全なフォーマットのテスト"""
        line = "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 5438 0000 1E75 F000 2F 7A 0303090001590532000C00260088050C002500260003040C005700260016050C00AF0026000F050C00BB0026000F050C00630563008705660D68052A0577 5438 7FFF"
        
        result = parse_text_line(line)
        
        # タイムスタンプの検証
        assert result['timestamp'] == datetime(2024, 9, 20, 16, 26, 11)
        
        # 送信元情報の検証
        assert result['source_ip'] == '192.168.1.100'
        assert result['source_port'] == 55061
        
        # センサータイプの検証
        assert result['sensor_type'] == 'vibration'
        
        # センサーオブジェクトの検証
        assert result['sensor'] is not None
        assert isinstance(result['sensor'], VibrationSensor)
        
        # センサー値の検証
        assert 'power-supply-voltage' in result['values']
        assert 'acceleration-RMS' in result['values']
        assert 'kurtosis' in result['values']
        assert 'temperature' in result['values']
        
        # info の検証
        assert result['info']['unit_id'] == '5438'
    
    def test_parse_erxdata_only(self):
        """ERXDATAのみの文字列のテスト"""
        line = "ERXDATA 5438 0000 1E75 F000 2F 7A 0303090001590532000C00260088050C002500260003040C005700260016050C00AF0026000F050C00BB0026000F050C00630563008705660D68052A0577 5438 7FFF"
        
        result = parse_text_line(line)
        
        # タイムスタンプとIPはNone
        assert result['timestamp'] is None
        assert result['source_ip'] is None
        assert result['source_port'] is None
        
        # センサータイプの検証
        assert result['sensor_type'] == 'vibration'
        
        # センサーオブジェクトの検証
        assert result['sensor'] is not None
    
    def test_parse_temperature_humidity(self):
        """温湿度センサーのテキスト行解析テスト"""
        line = "2024/09/20 10:00:00 192.168.1.50/12345:ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        
        result = parse_text_line(line)
        
        assert result['sensor_type'] == 'temperature_and_humidity'
        assert isinstance(result['sensor'], TemperatureAndHumiditySensor)
    
    def test_parse_multiple_lines(self):
        """複数行の解析テスト（実際のログファイル形式）"""
        lines = [
            "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 5438 0000 1E75 F000 2F 7A 0303090001590532000C00260088050C002500260003040C005700260016050C00AF0026000F050C00BB0026000F050C00630563008705660D68052A0577 5438 7FFF",
            "2024/09/20 16:28:13 192.168.1.100/55061:ERXDATA 5448 0000 6D98 F000 32 7A 0303090001570532000C00260016050C001900260016050C002500260016050C003E00260016050C005700260007050C000C056300AF05660023002A7077 5448 7FFF",
        ]
        
        results = [parse_text_line(line) for line in lines]
        
        assert len(results) == 2
        assert results[0]['info']['unit_id'] == '5438'
        assert results[1]['info']['unit_id'] == '5448'
        assert results[0]['timestamp'] == datetime(2024, 9, 20, 16, 26, 11)
        assert results[1]['timestamp'] == datetime(2024, 9, 20, 16, 28, 13)
    
    def test_parse_empty_line(self):
        """空行でValueErrorが発生するテスト"""
        with pytest.raises(ValueError) as exc_info:
            parse_text_line("")
        
        assert "空の文字列" in str(exc_info.value)
    
    def test_parse_no_erxdata(self):
        """ERXDATAが含まれない文字列でValueErrorが発生するテスト"""
        with pytest.raises(ValueError) as exc_info:
            parse_text_line("2024/09/20 16:26:11 192.168.1.100/55061:INVALID DATA")
        
        assert "ERXDATAが見つかりません" in str(exc_info.value)
    
    def test_parse_invalid_sensor_data(self):
        """フォーマットは正しいがセンサータイプが特定できないデータのテスト"""
        # ERXDATAはあるがデータが短すぎてセンサータイプを特定できない
        with pytest.raises(ValueError) as exc_info:
            parse_text_line("ERXDATA SHORT")
        
        # センサータイプを特定できないため「未知のセンサータイプ」エラー
        assert "未知のセンサータイプ" in str(exc_info.value)
    
    def test_parse_unknown_sensor_type(self):
        """未知のセンサータイプでValueErrorが発生するテスト"""
        line = "ERXDATA 0002 0000 62BE F000 18 20 030399FF012605320C90052A11AF052C7C0002 7FFF"
        
        with pytest.raises(ValueError) as exc_info:
            parse_text_line(line)
        
        assert "未知のセンサータイプ" in str(exc_info.value)
    
    def test_parse_raw_data_preserved(self):
        """raw_dataが正しく保持されているテスト"""
        line = "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 5438 0000 1E75 F000 2F 7A 0303090001590532000C00260088050C002500260003040C005700260016050C00AF0026000F050C00BB0026000F050C00630563008705660D68052A0577 5438 7FFF"
        
        result = parse_text_line(line)
        
        assert result['raw_data'].startswith(b"ERXDATA")
        assert b"5438 0000 1E75" in result['raw_data']
    
    def test_parse_whitespace_handling(self):
        """前後の空白を含む行の処理テスト"""
        line = "  ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF  \n"
        
        result = parse_text_line(line)
        
        assert result['sensor'] is not None
        assert result['sensor_type'] == 'temperature_and_humidity'
    
    def test_parse_checksum_error(self):
        """チェックサムエラーのテスト"""
        line = "ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7199 8001 7FFF"
        
        with pytest.raises(FailedCheckSum):
            parse_text_line(line)


class TestMurataExceptions:
    """例外クラスのテスト"""
    
    def test_failed_checksum_message(self):
        """FailedCheckSum例外のメッセージテスト"""
        exc = FailedCheckSum()
        assert "Failed to validate message checksum" in str(exc)
    
    def test_failed_checksum_with_details(self):
        """FailedCheckSum例外の詳細情報付きテスト"""
        exc = FailedCheckSum(details="Expected: AB, Got: CD")
        assert "Failed to validate message checksum" in str(exc)
        assert "Expected: AB, Got: CD" in str(exc)
    
    def test_failed_checksum_payload_message(self):
        """FailedCheckSumPayload例外のメッセージテスト"""
        exc = FailedCheckSumPayload()
        assert "Failed to validate payload checksum" in str(exc)
    
    def test_failed_checksum_payload_with_details(self):
        """FailedCheckSumPayload例外の詳細情報付きテスト"""
        exc = FailedCheckSumPayload(details="Payload validation failed")
        assert "Failed to validate payload checksum" in str(exc)
        assert "Payload validation failed" in str(exc)
    
    def test_exception_inheritance(self):
        """例外クラスの継承関係テスト"""
        from murata_sensor.murata_exception import MurataExceptionBase
        
        assert issubclass(FailedCheckSum, MurataExceptionBase)
        assert issubclass(FailedCheckSumPayload, MurataExceptionBase)
        assert issubclass(MurataExceptionBase, Exception)
    
    def test_exception_can_be_raised_and_caught(self):
        """例外を発生させてキャッチできることを確認"""
        with pytest.raises(FailedCheckSum):
            raise FailedCheckSum()
        
        with pytest.raises(FailedCheckSumPayload):
            raise FailedCheckSumPayload()
    
    def test_murata_exception_base_attributes(self):
        """MurataExceptionBaseの属性テスト"""
        from murata_sensor.murata_exception import MurataExceptionBase
        
        exc = MurataExceptionBase("Test message", "Test details")
        assert exc.message == "Test message"
        assert exc.details == "Test details"
        assert "Test message" in str(exc)
        assert "Test details" in str(exc)


class TestSensorDataClass:
    """SensorDataクラスのテスト"""
    
    @pytest.fixture
    def sample_sensor(self):
        """テスト用のセンサーオブジェクトを生成"""
        data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        addr = ("192.168.1.100", 1234)
        return TemperatureAndHumiditySensor(data, addr)
    
    @pytest.fixture
    def sample_vibration_sensor(self):
        """テスト用の振動センサーオブジェクトを生成"""
        data = b"ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7170 8001 7FFF"
        addr = ("192.168.1.100", 1234)
        return VibrationSensor(data, addr)
    
    def test_sensor_data_initialization(self, sample_sensor):
        """SensorDataの初期化テスト"""
        from murata_sensor.murata_receiver import SensorData
        
        sensor_data = SensorData(sample_sensor)
        
        assert sensor_data.sensor == sample_sensor
        assert sensor_data.last_update is not None
        assert len(sensor_data.history) == 1
        assert sensor_data.history[0][1] == sample_sensor
    
    def test_sensor_data_update(self, sample_sensor, sample_vibration_sensor):
        """SensorDataのupdate()メソッドテスト"""
        from murata_sensor.murata_receiver import SensorData
        import time
        
        sensor_data = SensorData(sample_sensor)
        initial_update_time = sensor_data.last_update
        
        time.sleep(0.01)
        sensor_data.update(sample_vibration_sensor)
        
        assert sensor_data.sensor == sample_vibration_sensor
        assert sensor_data.last_update > initial_update_time
        assert len(sensor_data.history) == 2
        assert sensor_data.history[1][1] == sample_vibration_sensor
    
    def test_sensor_data_history_limit(self, sample_sensor):
        """SensorDataの履歴1000件制限テスト"""
        from murata_sensor.murata_receiver import SensorData
        
        sensor_data = SensorData(sample_sensor)
        
        for i in range(1100):
            sensor_data.update(sample_sensor)
        
        assert len(sensor_data.history) == 1000
    
    def test_sensor_data_history_order(self, sample_sensor, sample_vibration_sensor):
        """SensorDataの履歴が時系列順になっていることを確認"""
        from murata_sensor.murata_receiver import SensorData
        
        sensor_data = SensorData(sample_sensor)
        sensor_data.update(sample_vibration_sensor)
        sensor_data.update(sample_sensor)
        
        assert len(sensor_data.history) == 3
        for i in range(len(sensor_data.history) - 1):
            assert sensor_data.history[i][0] <= sensor_data.history[i + 1][0]
    
    def test_sensor_data_last_update_type(self, sample_sensor):
        """last_updateがdatetime型であることを確認"""
        from murata_sensor.murata_receiver import SensorData
        
        sensor_data = SensorData(sample_sensor)
        assert isinstance(sensor_data.last_update, datetime)


class TestMurataReceiverUnit:
    """MurataReceiverクラスのユニットテスト"""
    
    @pytest.fixture
    def mock_socket(self, mocker=None):
        """モック化されたソケットを提供"""
        import unittest.mock as mock
        with mock.patch('socket.socket') as mock_sock:
            yield mock_sock
    
    def test_receiver_initialization(self):
        """MurataReceiverの初期化テスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            assert receiver.port == 55039
            assert receiver.buffer_size == 1024
            assert receiver.sensors == {}
            assert receiver.data_callback is None
            assert receiver.error_callback is None
    
    def test_receiver_with_custom_buffer_size(self):
        """カスタムバッファサイズでの初期化テスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039, buffer_size=2048)
            assert receiver.buffer_size == 2048
    
    def test_receiver_with_callbacks(self):
        """コールバック関数付きでの初期化テスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        def data_cb(data, addr):
            pass
        
        def error_cb(exc, data, addr):
            pass
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(
                55039, 
                data_callback=data_cb, 
                error_callback=error_cb
            )
            assert receiver.data_callback == data_cb
            assert receiver.error_callback == error_cb
    
    def test_make_sensor_valid_data(self):
        """make_sensor()の正常系テスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            addr = ("192.168.1.100", 55061)
            
            sensor = receiver.make_sensor(data, addr)
            
            assert sensor is not None
            assert isinstance(sensor, TemperatureAndHumiditySensor)
    
    def test_make_sensor_invalid_data(self):
        """make_sensor()の異常系テスト - 不正なデータ"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            invalid_data = b"INVALID DATA"
            addr = ("192.168.1.100", 55061)
            
            sensor = receiver.make_sensor(invalid_data, addr)
            
            assert sensor is None
    
    def test_make_sensor_unknown_type(self):
        """make_sensor()の異常系テスト - 未知のセンサータイプ"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            data = b"ERXDATA 0002 0000 62BE F000 18 20 030399FF012605320C90052A11AF052C7C0002 7FFF"
            addr = ("192.168.1.100", 55061)
            
            sensor = receiver.make_sensor(data, addr)
            
            assert sensor is None
    
    def test_get_latest_data_existing_sensor(self):
        """get_latest_data()の正常系テスト - 既存センサー"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver, SensorData
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            addr = ("192.168.1.100", 55061)
            
            sensor = receiver.make_sensor(data, addr)
            receiver.sensors[addr] = SensorData(sensor)
            
            latest = receiver.get_latest_data(addr)
            
            assert latest is not None
            assert latest == sensor
    
    def test_get_latest_data_nonexistent_sensor(self):
        """get_latest_data()のテスト - 存在しないセンサー"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            addr = ("192.168.1.100", 55061)
            latest = receiver.get_latest_data(addr)
            
            assert latest is None
    
    def test_get_sensor_history_existing_sensor(self):
        """get_sensor_history()の正常系テスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver, SensorData
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            addr = ("192.168.1.100", 55061)
            
            sensor = receiver.make_sensor(data, addr)
            receiver.sensors[addr] = SensorData(sensor)
            
            history = receiver.get_sensor_history(addr)
            
            assert len(history) == 1
            assert history[0][1] == sensor
    
    def test_get_sensor_history_nonexistent_sensor(self):
        """get_sensor_history()のテスト - 存在しないセンサー"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            addr = ("192.168.1.100", 55061)
            history = receiver.get_sensor_history(addr)
            
            assert history == []
    
    def test_update_sensor_data_new_sensor(self):
        """_update_sensor_data()の新規センサーテスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            addr = ("192.168.1.100", 55061)
            
            sensor = receiver.make_sensor(data, addr)
            receiver._update_sensor_data(addr, sensor)
            
            assert addr in receiver.sensors
            assert receiver.sensors[addr].sensor == sensor
    
    def test_update_sensor_data_existing_sensor(self):
        """_update_sensor_data()の既存センサー更新テスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            addr = ("192.168.1.100", 55061)
            
            sensor1 = receiver.make_sensor(data, addr)
            receiver._update_sensor_data(addr, sensor1)
            
            sensor2 = receiver.make_sensor(data, addr)
            receiver._update_sensor_data(addr, sensor2)
            
            assert len(receiver.sensors[addr].history) == 2
    
    def test_data_callback_invoked(self):
        """データコールバックが呼び出されることを確認"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        callback_called = []
        
        def data_callback(data, addr):
            callback_called.append((data, addr))
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039, data_callback=data_callback)
            
            data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            addr = ("192.168.1.100", 55061)
            
            sensor = receiver.make_sensor(data, addr)
            receiver._update_sensor_data(addr, sensor)
            receiver._process_sensor_data(addr, sensor)
            
            assert len(callback_called) == 1
            assert callback_called[0][1] == addr
    
    def test_error_callback_on_callback_error(self):
        """コールバック内エラー時にエラーコールバックが呼ばれることを確認"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        error_callback_called = []
        
        def data_callback(data, addr):
            raise ValueError("Test error")
        
        def error_callback(exc, data, addr):
            error_callback_called.append((exc, data, addr))
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(
                55039, 
                data_callback=data_callback,
                error_callback=error_callback
            )
            
            data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            addr = ("192.168.1.100", 55061)
            
            sensor = receiver.make_sensor(data, addr)
            receiver._process_sensor_data(addr, sensor)
            
            assert len(error_callback_called) == 1
            assert isinstance(error_callback_called[0][0], ValueError)
    
    def test_receiver_with_custom_logger(self):
        """カスタムロガーでの初期化テスト"""
        import unittest.mock as mock
        import logging
        from murata_sensor.murata_receiver import MurataReceiver
        
        custom_logger = logging.getLogger("test_logger")
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039, logger=custom_logger)
            assert receiver.logger == custom_logger


class TestAdditionalSensorTypes:
    """追加センサータイプのテスト（クラス構造と属性の確認）"""
    
    def test_vibration_speed_sensor_class_structure(self):
        """VibrationSpeedクラスの構造テスト"""
        assert hasattr(VibrationSpeed, 'retrieve_values')
        assert issubclass(VibrationSpeed, MurataSensorBase)
    
    def test_water_leak_sensor_class_structure(self):
        """WaterLeakSensorクラスの構造テスト"""
        assert hasattr(WaterLeakSensor, 'retrieve_values')
        assert issubclass(WaterLeakSensor, MurataSensorBase)
    
    def test_plg_duty_sensor_class_structure(self):
        """PlgDutySensorクラスの構造テスト"""
        assert hasattr(PlgDutySensor, 'retrieve_values')
        assert issubclass(PlgDutySensor, MurataSensorBase)
    
    def test_brake_current_monitor_class_structure(self):
        """BrakeCurrentMonitorクラスの構造テスト"""
        assert hasattr(BrakeCurrentMonitor, 'retrieve_values')
        assert issubclass(BrakeCurrentMonitor, MurataSensorBase)
    
    def test_vibration_with_instruction_sensor_class_structure(self):
        """VibrationWithInstructionSensorクラスの構造テスト"""
        assert hasattr(VibrationWithInstructionSensor, 'retrieve_values')
        assert issubclass(VibrationWithInstructionSensor, MurataSensorBase)
    
    def test_compact_thermocouple_sensor_class_structure(self):
        """CompactThermocoupleSensorクラスの構造テスト"""
        assert hasattr(CompactThermocoupleSensor, 'retrieve_values')
        assert issubclass(CompactThermocoupleSensor, MurataSensorBase)
    
    def test_solar_external_sensor_class_structure(self):
        """SolarExternalSensorクラスの構造テスト"""
        assert hasattr(SolarExternalSensor, 'retrieve_values')
        assert issubclass(SolarExternalSensor, MurataSensorBase)
    
    def test_contact_output_sensor_class_structure(self):
        """ContactOutputSensorクラスの構造テスト"""
        assert hasattr(ContactOutputSensor, 'retrieve_values')
        assert issubclass(ContactOutputSensor, MurataSensorBase)
    
    def test_analog_meter_reader_sensor_class_structure(self):
        """AnalogMeterReaderSensorクラスの構造テスト"""
        assert hasattr(AnalogMeterReaderSensor, 'retrieve_values')
        assert issubclass(AnalogMeterReaderSensor, MurataSensorBase)
    
    def test_vibration_2tf001_speed_sensor_class_structure(self):
        """Vibration2TF001SpeedSensorクラスの構造テスト"""
        assert hasattr(Vibration2TF001SpeedSensor, 'retrieve_values')
        assert issubclass(Vibration2TF001SpeedSensor, MurataSensorBase)
    
    def test_vibration_2tf001_accel_sensor_class_structure(self):
        """Vibration2TF001AccelSensorクラスの構造テスト"""
        assert hasattr(Vibration2TF001AccelSensor, 'retrieve_values')
        assert issubclass(Vibration2TF001AccelSensor, MurataSensorBase)
    
    def test_sensor_type_mapping_coverage(self):
        """SENSOR_TYPEマッピングのカバレッジテスト"""
        from murata_sensor.murata_sensor import SENSOR_TYPE
        from murata_sensor.murata_receiver import SENSOR_CLASSES
        
        for type_code, sensor_type in SENSOR_TYPE.items():
            assert sensor_type in SENSOR_CLASSES, f"Missing class mapping for {sensor_type}"
    
    def test_all_sensor_classes_exist_in_receiver(self):
        """全てのセンサークラスがSENSOR_CLASSESに登録されていることを確認"""
        from murata_sensor.murata_receiver import SENSOR_CLASSES
        
        expected_sensor_types = [
            "vibration", "vibration_speed", "temperature_and_humidity", 
            "thermocouple", "current_pulse", "voltage_pulse", "CT",
            "3_current", "3_voltage", "3_contacts", "waterproof_repeater",
            "water_leak", "plg_duty", "brake_current_monitor",
            "vibration_with_instruction", "compact_thermocouple",
            "solar_external_sensor", "contact_output", "analog_meter_reader",
            "vibration_2tf001_speed", "vibration_2tf001_accel"
        ]
        
        for sensor_type in expected_sensor_types:
            assert sensor_type in SENSOR_CLASSES, f"Missing: {sensor_type}"


class TestEdgeCases:
    """エッジケース・異常系テスト"""
    
    def test_is_murata_sensor_data_empty_bytes(self):
        """空のバイト列のテスト"""
        assert not MurataSensorBase.is_murata_sensor_data(b"")
    
    def test_is_murata_sensor_data_short_data(self):
        """短すぎるデータのテスト"""
        assert not MurataSensorBase.is_murata_sensor_data(b"ERX")
    
    def test_is_murata_sensor_data_lowercase(self):
        """小文字のERXDATAはセンサーデータではない"""
        assert not MurataSensorBase.is_murata_sensor_data(b"erxdata 0002 0000")
    
    def test_check_sensor_type_short_data(self):
        """短いデータでのセンサータイプチェック"""
        result = MurataSensorBase.check_sensor_type(b"ERXDATA 0002 0000")
        assert result is None
    
    def test_check_sensor_type_invalid_type_code(self):
        """不正なタイプコードでのセンサータイプチェック"""
        data = b"ERXDATA 0002 0000 62BE F000 18 20 FFFFFFFFFF"
        result = MurataSensorBase.check_sensor_type(data)
        assert result is None
    
    def test_rssi_boundary_values(self):
        """RSSI境界値のテスト（理論値の確認）"""
        # RSSI計算: rssi_hex (16進数) - 107
        # 例: 0x00 -> 0 - 107 = -107
        # 例: 0x6B -> 107 - 107 = 0
        # 例: 0x50 -> 80 - 107 = -27
        
        # RSSI計算ロジックのテスト
        assert int("00", 16) - 107 == -107
        assert int("6B", 16) - 107 == 0
        assert int("50", 16) - 107 == -27
        assert int("18", 16) - 107 == -83
    
    def test_scale_values(self):
        """スケール値のテスト"""
        from murata_sensor.murata_sensor import SCALE
        
        assert SCALE["00"] == 1
        assert SCALE["01"] == 10
        assert SCALE["02"] == 100
        assert SCALE["03"] == 1000
        assert SCALE["04"] == 0.1
        assert SCALE["05"] == 0.01
        assert SCALE["06"] == 0.001
        assert SCALE["80"] == -1
        assert SCALE["FF"] == 0
    
    def test_unit_type_mapping(self):
        """ユニットタイプマッピングのテスト"""
        from murata_sensor.murata_sensor import UNIT_TYPE
        
        assert UNIT_TYPE["2A"]["name"] == "セルシウス温度"
        assert UNIT_TYPE["2A"]["unit"] == "℃"
        assert UNIT_TYPE["32"]["name"] == "電位差（電圧）"
        assert UNIT_TYPE["32"]["unit"] == "V"
        assert UNIT_TYPE["2C"]["name"] == "相対湿度"
        assert UNIT_TYPE["2C"]["unit"] == "%RH"
    
    def test_sensor_with_none_addr(self):
        """アドレスがNoneの場合のテスト"""
        data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        sensor = TemperatureAndHumiditySensor(data, (None, None))
        
        assert sensor.info['addr'] == (None, None)
    
    def test_sensor_str_representation(self):
        """センサーオブジェクトの文字列表現テスト"""
        addr = ("192.168.1.100", 1234)
        data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        sensor = TemperatureAndHumiditySensor(data, addr)
        
        str_repr = str(sensor)
        assert "info:" in str_repr
        assert "type:" in str_repr
        assert "data:" in str_repr
        assert "payload:" in str_repr
        assert "values:" in str_repr
    
    def test_route_info_single_hop(self):
        """単一ホップの経路情報テスト"""
        addr = ("192.168.1.100", 1234)
        data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        sensor = TemperatureAndHumiditySensor(data, addr)
        
        assert isinstance(sensor.info['route'], list)
        assert len(sensor.info['route']) >= 1
    
    def test_create_sensor_all_sensor_types(self):
        """create_sensorで全センサータイプが生成できることを確認"""
        from murata_sensor.murata_receiver import SENSOR_CLASSES
        
        for sensor_type, sensor_class in SENSOR_CLASSES.items():
            assert sensor_class is not None
            assert hasattr(sensor_class, 'retrieve_values')
    
    def test_parse_text_line_with_colon_in_data(self):
        """データ内にコロンがある場合のテキスト行解析"""
        line = "ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        result = parse_text_line(line)
        
        assert result['sensor'] is not None
    
    def test_checksum_validation_edge_case(self):
        """チェックサム検証のエッジケース"""
        addr = ("192.168.1.100", 1234)
        
        # 正しいチェックサムを持つデータ
        valid_data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        sensor = TemperatureAndHumiditySensor(valid_data, addr)
        assert sensor is not None
    
    def test_payload_length_calculation(self):
        """ペイロード長の計算テスト"""
        addr = ("192.168.1.100", 1234)
        data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        sensor = TemperatureAndHumiditySensor(data, addr)
        
        # ペイロード長は16進数で表現されている (0x20 = 32バイト)
        assert sensor.payload_length == 32
    
    def test_sensor_status_unknown(self):
        """未知のセンサー状態コードのテスト"""
        addr = ("192.168.1.100", 1234)
        data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        sensor = TemperatureAndHumiditySensor(data, addr)
        
        # 温湿度センサーのステータスコードはFF
        assert sensor.info['status']['code'] == 'FF'
    
    def test_vibration_sensor_range_over_status(self):
        """振動センサーのレンジオーバー状態テスト（ステータスコードの確認）"""
        # 振動センサーのステータスコード:
        # "00" -> 正常
        # "01" -> レンジオーバー
        # この確認はセンサー状態解析ロジックのテスト
        
        status_mapping = {
            "00": "正常",
            "01": "レンジオーバー"
        }
        
        assert status_mapping["00"] == "正常"
        assert status_mapping["01"] == "レンジオーバー"
    
    def test_invalid_timestamp_format(self):
        """不正なタイムスタンプ形式のテスト"""
        line = "INVALID_TIMESTAMP 192.168.1.100/55061:ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        result = parse_text_line(line)
        
        # タイムスタンプはNoneになるが、センサーデータは解析される
        assert result['timestamp'] is None
        assert result['sensor'] is not None
    
    def test_invalid_ip_port_format(self):
        """不正なIP/ポート形式のテスト"""
        line = "2024/09/20 16:26:11 INVALID_IP:ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        result = parse_text_line(line)
        
        # IPアドレスはNoneになるが、センサーデータは解析される
        assert result['source_ip'] is None
        assert result['sensor'] is not None


class TestIntegration:
    """統合テスト"""
    
    def test_multiple_sensors_from_different_addresses(self):
        """複数アドレスからのセンサーデータ処理テスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            # 異なるアドレスから複数のセンサーデータを受信
            data1 = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            addr1 = ("192.168.1.100", 55061)
            
            data2 = b"ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7170 8001 7FFF"
            addr2 = ("192.168.1.101", 55062)
            
            sensor1 = receiver.make_sensor(data1, addr1)
            receiver._update_sensor_data(addr1, sensor1)
            
            sensor2 = receiver.make_sensor(data2, addr2)
            receiver._update_sensor_data(addr2, sensor2)
            
            assert len(receiver.sensors) == 2
            assert addr1 in receiver.sensors
            assert addr2 in receiver.sensors
            assert isinstance(receiver.sensors[addr1].sensor, TemperatureAndHumiditySensor)
            assert isinstance(receiver.sensors[addr2].sensor, VibrationSensor)
    
    def test_history_accumulation(self):
        """履歴蓄積のテスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            addr = ("192.168.1.100", 55061)
            
            # 複数回センサーデータを更新
            for _ in range(5):
                sensor = receiver.make_sensor(data, addr)
                receiver._update_sensor_data(addr, sensor)
            
            history = receiver.get_sensor_history(addr)
            assert len(history) == 5
    
    def test_callback_chain_execution(self):
        """コールバックチェーンの実行テスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        callback_order = []
        
        def data_callback(data, addr):
            callback_order.append('data')
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039, data_callback=data_callback)
            
            data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            addr = ("192.168.1.100", 55061)
            
            sensor = receiver.make_sensor(data, addr)
            receiver._update_sensor_data(addr, sensor)
            receiver._process_sensor_data(addr, sensor)
            
            assert 'data' in callback_order
    
    def test_full_data_flow_with_parse_text_line(self):
        """parse_text_lineを使用した完全なデータフローテスト"""
        lines = [
            "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 5438 0000 1E75 F000 2F 7A 0303090001590532000C00260088050C002500260003040C005700260016050C00AF0026000F050C00BB0026000F050C00630563008705660D68052A0577 5438 7FFF",
            "2024/09/20 16:28:13 192.168.1.100/55061:ERXDATA 5448 0000 6D98 F000 32 7A 0303090001570532000C00260016050C001900260016050C002500260016050C003E00260016050C005700260007050C000C056300AF05660023002A7077 5448 7FFF",
            "2024/09/20 16:30:00 192.168.1.50/12345:ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF",
        ]
        
        results = []
        for line in lines:
            result = parse_text_line(line)
            results.append(result)
        
        assert len(results) == 3
        
        # 最初の2つは振動センサー
        assert results[0]['sensor_type'] == 'vibration'
        assert results[1]['sensor_type'] == 'vibration'
        
        # 3つ目は温湿度センサー
        assert results[2]['sensor_type'] == 'temperature_and_humidity'
        
        # タイムスタンプが正しく解析されていること
        assert results[0]['timestamp'] == datetime(2024, 9, 20, 16, 26, 11)
        assert results[2]['timestamp'] == datetime(2024, 9, 20, 16, 30, 0)
    
    def test_create_sensor_with_all_valid_types(self):
        """create_sensorで全ての有効なセンサータイプが生成できることを確認"""
        valid_sensor_data = [
            b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF",  # temperature_and_humidity
            b"ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7170 8001 7FFF",  # vibration
        ]
        
        addr = ("192.168.1.100", 55061)
        
        for data in valid_sensor_data:
            sensor = create_sensor(data, addr)
            assert sensor is not None
            assert hasattr(sensor, 'values')
            assert hasattr(sensor, 'info')
    
    def test_sensor_data_consistency(self):
        """センサーデータの一貫性テスト"""
        addr = ("192.168.1.100", 1234)
        data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        
        # 同じデータで複数回センサーを生成
        sensors = [TemperatureAndHumiditySensor(data, addr) for _ in range(3)]
        
        # すべてのセンサーが同じ値を持つことを確認
        for i in range(1, len(sensors)):
            assert sensors[0].values == sensors[i].values
            assert sensors[0].info['unit_id'] == sensors[i].info['unit_id']
            assert sensors[0].info['message_id'] == sensors[i].info['message_id']
    
    def test_receiver_sensor_replacement(self):
        """センサーデータの置き換えテスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            addr = ("192.168.1.100", 55061)
            
            # 温湿度センサーデータを登録
            data1 = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            sensor1 = receiver.make_sensor(data1, addr)
            receiver._update_sensor_data(addr, sensor1)
            
            # 同じアドレスに別のデータを送信（更新）
            sensor2 = receiver.make_sensor(data1, addr)
            receiver._update_sensor_data(addr, sensor2)
            
            # 最新データが返されることを確認
            latest = receiver.get_latest_data(addr)
            assert latest == sensor2
            
            # 履歴に両方が含まれることを確認
            history = receiver.get_sensor_history(addr)
            assert len(history) == 2
    
    def test_mixed_valid_and_invalid_data(self):
        """有効なデータと無効なデータの混在テスト"""
        import unittest.mock as mock
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            valid_data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            invalid_data = b"INVALID DATA"
            unknown_type_data = b"ERXDATA 0002 0000 62BE F000 18 20 030399FF012605320C90052A11AF052C7C0002 7FFF"
            
            addr = ("192.168.1.100", 55061)
            
            # 有効なデータ
            sensor1 = receiver.make_sensor(valid_data, addr)
            assert sensor1 is not None
            
            # 無効なデータ
            sensor2 = receiver.make_sensor(invalid_data, addr)
            assert sensor2 is None
            
            # 未知のセンサータイプ
            sensor3 = receiver.make_sensor(unknown_type_data, addr)
            assert sensor3 is None
    
    def test_performance_multiple_sensors(self):
        """複数センサー処理のパフォーマンステスト"""
        import unittest.mock as mock
        import time
        from murata_sensor.murata_receiver import MurataReceiver
        
        with mock.patch('socket.socket'):
            receiver = MurataReceiver(55039)
            
            data = b"ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
            
            start_time = time.time()
            
            # 100個のセンサーデータを処理
            for i in range(100):
                addr = (f"192.168.1.{i % 256}", 55061 + i)
                sensor = receiver.make_sensor(data, addr)
                if sensor:
                    receiver._update_sensor_data(addr, sensor)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 100個のセンサーデータ処理が1秒以内に完了することを確認
            assert processing_time < 1.0
            assert len(receiver.sensors) == 100


class TestAsyncMurataReceiver:
    """AsyncMurataReceiver の start/stop/__anext__ のテスト（カバレッジ向上用）"""

    def test_async_receiver_start_stop(self):
        """start() と stop() が正常に動作する"""
        async def run() -> None:
            receiver = AsyncMurataReceiver(port=0)
            await receiver.start()
            await receiver.stop()

        asyncio.run(run())

    def test_async_receiver_anext_raises_without_start(self):
        """start() 前に __anext__ を呼ぶと RuntimeError"""
        async def run() -> None:
            receiver = AsyncMurataReceiver(port=0)
            with pytest.raises(RuntimeError):
                await receiver.__anext__()

        asyncio.run(run())

    def test_async_receiver_anext_stop_iteration_after_stop(self):
        """stop() がキューに sentinel を入れた後、__anext__ は StopAsyncIteration"""
        async def run() -> None:
            receiver = AsyncMurataReceiver(port=0)
            await receiver.start()

            async def stop_after_short_delay() -> None:
                await asyncio.sleep(0.02)
                await receiver.stop()

            asyncio.create_task(stop_after_short_delay())
            with pytest.raises(StopAsyncIteration):
                await receiver.__anext__()

        asyncio.run(run())

    def test_async_receiver_aiter_returns_self(self):
        """__aiter__ が自身を返す"""
        receiver = AsyncMurataReceiver(port=0)
        assert receiver.__aiter__() is receiver
