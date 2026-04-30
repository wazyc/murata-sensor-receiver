import asyncio
import logging

from murata_sensor.async_receiver import _UDPReceiverProtocol
from murata_sensor.murata_exception import FailedCheckSum


VALID_TEMPERATURE_DATA = (
    b"ERXDATA 0002 0000 62BE F000 18 20 "
    b"030301FF012605320C90052A11AF052C7C0002 7FFF"
)
INVALID_CHECKSUM_DATA = (
    b"ERXDATA 8001 0000 1012 F000 2A 7A "
    b"03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C"
    b"FFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7199 "
    b"8001 7FFF"
)


def test_datagram_received_valid_packet_queues_sensor_data():
    """有効なUDPデータグラムをセンサーデータとしてキューへ投入する"""

    async def run():
        queue = asyncio.Queue()
        protocol = _UDPReceiverProtocol(queue, logging.getLogger("test_async"))
        addr = ("192.168.1.100", 55061)

        protocol.datagram_received(VALID_TEMPERATURE_DATA, addr)
        sensor_data, queued_addr = await queue.get()

        assert queued_addr == addr
        assert sensor_data["sensor_type"] == "temperature_and_humidity"
        assert sensor_data["addr"] == addr
        assert sensor_data["values"]
        assert sensor_data["info"]["unit_id"] == "0002"

    asyncio.run(run())


def test_datagram_received_parse_error_queues_unparsed_when_enabled():
    """include_unparsed=True では解析例外も未解析データとして返す"""

    async def run():
        queue = asyncio.Queue()
        protocol = _UDPReceiverProtocol(
            queue,
            logging.getLogger("test_async"),
            include_unparsed=True,
        )
        addr = ("192.168.1.100", 55061)

        protocol.datagram_received(INVALID_CHECKSUM_DATA, addr)
        unparsed_data, queued_addr = await queue.get()

        assert queued_addr == addr
        assert unparsed_data["parsed"] is False
        assert unparsed_data["reason"] == "checksum_error"
        assert isinstance(unparsed_data["error"], FailedCheckSum)
        assert unparsed_data["raw_data"] == INVALID_CHECKSUM_DATA

    asyncio.run(run())


def test_datagram_received_queue_full_drops_without_raising():
    """キュー満杯時は例外を外へ漏らさずデータを破棄する"""
    queue = asyncio.Queue(maxsize=1)
    queue.put_nowait(({"existing": True}, ("127.0.0.1", 1)))
    protocol = _UDPReceiverProtocol(queue, logging.getLogger("test_async"))

    protocol.datagram_received(VALID_TEMPERATURE_DATA, ("192.168.1.100", 55061))

    assert queue.qsize() == 1
