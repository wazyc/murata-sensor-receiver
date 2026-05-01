import unittest.mock as mock

import pytest

from murata_sensor.murata_receiver import MurataReceiver

VALID_TEMPERATURE_DATA = (
    b"ERXDATA 0002 0000 62BE F000 18 20 " b"030301FF012605320C90052A11AF052C7C0002 7FFF"
)
UNKNOWN_SENSOR_DATA = (
    b"ERXDATA 0002 0000 62BE F000 18 20 " b"030399FF012605320C90052A11AF052C7C0002 7FFF"
)


class FakeSocket:
    """recv() の1ループ分を決定的に動かすためのテスト用ソケット"""

    def __init__(self, recv_results):
        self.recv_results = list(recv_results)
        self.bound_addr = None

    def bind(self, addr):
        self.bound_addr = addr

    def recvfrom(self, buffer_size):
        result = self.recv_results.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result


def test_recv_valid_packet_updates_storage_and_invokes_callback():
    """recv() が受信データを保存し、データコールバックへ渡す"""
    addr = ("192.168.1.100", 55061)
    socket_instance = FakeSocket(
        [
            (VALID_TEMPERATURE_DATA, addr),
            KeyboardInterrupt(),
        ]
    )
    callback_results = []

    def data_callback(sensor_data, callback_addr):
        callback_results.append((sensor_data, callback_addr))

    with mock.patch("socket.socket", return_value=socket_instance):
        receiver = MurataReceiver(55039, data_callback=data_callback)

        with pytest.raises(KeyboardInterrupt):
            receiver.recv()

    assert socket_instance.bound_addr == ("0.0.0.0", 55039)
    assert receiver.get_latest_data(addr) is not None
    assert len(callback_results) == 1
    sensor_data, callback_addr = callback_results[0]
    assert callback_addr == addr
    assert sensor_data["sensor_type"] == "temperature_and_humidity"
    assert "temperature" in sensor_data["values"]


def test_recv_unknown_sensor_invokes_unparsed_callback():
    """recv() が未知センサーを未解析コールバックへ渡す"""
    addr = ("192.168.1.100", 55061)
    socket_instance = FakeSocket(
        [
            (UNKNOWN_SENSOR_DATA, addr),
            KeyboardInterrupt(),
        ]
    )
    unparsed_results = []

    def unparsed_callback(unparsed_data, callback_addr):
        unparsed_results.append((unparsed_data, callback_addr))

    with mock.patch("socket.socket", return_value=socket_instance):
        receiver = MurataReceiver(55039, unparsed_callback=unparsed_callback)

        with pytest.raises(KeyboardInterrupt):
            receiver.recv()

    assert receiver.get_latest_data(addr) is None
    assert len(unparsed_results) == 1
    unparsed_data, callback_addr = unparsed_results[0]
    assert callback_addr == addr
    assert unparsed_data["parsed"] is False
    assert unparsed_data["reason"] == "unsupported_sensor_type"
    assert unparsed_data["sensor_type_code"] == "99"


def test_recvfrom_error_invokes_error_callback_without_secondary_error():
    """recvfrom() 失敗時も未定義変数で二次エラーにしない"""
    socket_instance = FakeSocket(
        [
            OSError("network down"),
            KeyboardInterrupt(),
        ]
    )
    error_results = []

    def error_callback(exc, raw_data, callback_addr):
        error_results.append((exc, raw_data, callback_addr))

    with mock.patch("socket.socket", return_value=socket_instance):
        receiver = MurataReceiver(55039, error_callback=error_callback)

        with pytest.raises(KeyboardInterrupt):
            receiver.recv()

    assert len(error_results) == 1
    exc, raw_data, callback_addr = error_results[0]
    assert isinstance(exc, OSError)
    assert raw_data == b""
    assert callback_addr == ("", 0)


def test_run_in_thread_uses_recv_target_and_daemon_flag():
    """run_in_thread() が recv を別スレッドのターゲットにする"""
    with mock.patch("socket.socket"):
        receiver = MurataReceiver(55039)

    with mock.patch("threading.Thread") as thread_class:
        thread = receiver.run_in_thread(daemon=False)

    thread_class.assert_called_once_with(target=receiver.recv, daemon=False)
    thread_class.return_value.start.assert_called_once_with()
    assert thread is thread_class.return_value
