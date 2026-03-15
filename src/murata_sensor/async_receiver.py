"""
非同期（asyncio）対応の村田センサーUDP受信モジュール

標準ライブラリのasyncioのみを使用し、追加依存なしで動作する。
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, cast

from murata_sensor.murata_receiver import create_sensor


class _UDPReceiverProtocol(asyncio.DatagramProtocol):
    """UDP受信用のasyncio Protocol実装。受信データをキューに投入する。"""

    def __init__(self, queue: asyncio.Queue, logger: logging.Logger):
        self._queue = queue
        self._logger = logger
        self._transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        try:
            sensor = create_sensor(data, addr)
            if sensor is None:
                return
            sensor_data: Dict[str, Any] = {
                "sensor_type": sensor.check_sensor_type(sensor.data),
                "timestamp": datetime.now().isoformat(),
                "values": sensor.values,
                "info": sensor.info,
                "addr": addr,
            }
            try:
                self._queue.put_nowait((sensor_data, addr))
            except asyncio.QueueFull:
                self._logger.warning("受信キューが満杯のためデータを破棄しました")
        except Exception as e:
            self._logger.debug("パースエラー: %s", e)

    def error_received(self, exc: Optional[Exception]) -> None:
        if exc:
            self._logger.error("UDP受信エラー: %s", exc)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if exc:
            self._logger.debug("接続終了: %s", exc)


# イテレーション終了用の sentinel
_ITER_SENTINEL = object()


class AsyncMurataReceiver:
    """
    asyncio対応の非同期UDP受信クラス。

    村田製作所製センサーからのUDPデータを非同期で受信する。
    async for でイテレートするか、start() で受信を開始したうえで
    キュー経由でデータを取得できる。

    Attributes:
        port (int): 受信ポート番号
        buffer_size (int): 受信バッファサイズ（Protocolでは未使用、将来用）
    """

    def __init__(
        self,
        port: int,
        buffer_size: int = 1024,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Args:
            port: 受信ポート番号
            buffer_size: 受信バッファサイズ（デフォルト1024）
            logger: ロガー（指定しない場合はデフォルトロガーを使用）
        """
        self.port = port
        self.buffer_size = buffer_size
        self.logger = logger or logging.getLogger(__name__)
        self._queue: asyncio.Queue = asyncio.Queue()
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._protocol: Optional[_UDPReceiverProtocol] = None
        self._running = False
        self._receive_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """
        受信を開始する。

        UDPソケットをバインドし、バックグラウンドで受信を開始する。
        """
        if self._running:
            return
        loop = asyncio.get_running_loop()
        protocol = _UDPReceiverProtocol(self._queue, self.logger)
        self._protocol = protocol
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: protocol,
            local_addr=("0.0.0.0", self.port),
        )
        self._running = True
        self.logger.info("非同期受信を開始しました (port=%s)", self.port)

    async def stop(self) -> None:
        """
        受信を停止する。

        ソケットをクローズし、イテレーション待ちの場合は終了用 sentinel を投入する。
        """
        if not self._running:
            return
        self._running = False
        if self._transport:
            self._transport.close()
            self._transport = None
        self._protocol = None
        try:
            self._queue.put_nowait((_ITER_SENTINEL, (None, None)))
        except asyncio.QueueFull:
            pass
        self.logger.info("非同期受信を停止しました (port=%s)", self.port)

    def __aiter__(self) -> "AsyncMurataReceiver":
        """async for でイテレートするために自身を返す。"""
        return self

    async def __anext__(self) -> Tuple[Dict[str, Any], Tuple[str, int]]:
        """
        次のセンサーデータを返す。

        Returns:
            (sensor_data, addr) のタプル。
            sensor_data は 'sensor_type', 'timestamp', 'values', 'info', 'addr' を持つ辞書。

        Raises:
            StopAsyncIteration: stop() が呼ばれた場合
        """
        if not self._running:
            raise RuntimeError("start() を先に呼び出してください")
        item = await self._queue.get()
        if item[0] is _ITER_SENTINEL:
            raise StopAsyncIteration
        return cast(Tuple[Dict[str, Any], Tuple[str, int]], item)
