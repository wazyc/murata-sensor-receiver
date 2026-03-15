#!/usr/bin/env python3
"""
コールバックパターン: functools.partial

functools.partial を使って既存の関数に追加の引数を部分適用します。

利点:
    - 既存の関数を再利用できる
    - 引数の一部を事前に固定できる
    - テストしやすい

実行方法:
    python examples/callback_partial.py

停止方法:
    Ctrl+C
"""

import sqlite3
from functools import partial
from typing import Any

from murata_sensor import MurataReceiver


def on_data_with_context(
    sensor_data: dict,
    addr: tuple,
    *,  # 以降はキーワード引数のみ
    db_conn: Any,
    tag: str,
    debug: bool = False
) -> None:
    """
    追加の引数を受け取るコールバック関数
    
    Args:
        sensor_data: センサーデータ（MurataReceiverから）
        addr: 送信元アドレス（MurataReceiverから）
        db_conn: データベース接続（部分適用）
        tag: 識別タグ（部分適用）
        debug: デバッグモード（部分適用）
    """
    print(f"[{tag}] {sensor_data['sensor_type']}")
    print(f"  送信元: {addr[0]}:{addr[1]}")
    
    if debug:
        print(f"  詳細: {sensor_data['values']}")
    
    # db_conn を使用してDB操作も可能
    # db_conn.execute(...)


def main():
    # データベース接続を作成
    conn = sqlite3.connect(":memory:")
    
    # partial で追加の引数を固定
    callback = partial(
        on_data_with_context,
        db_conn=conn,
        tag="LINE-1",
        debug=True
    )
    
    receiver = MurataReceiver(port=55039, data_callback=callback)
    
    print("センサーデータを受信中... (Ctrl+Cで停止)")
    print("タグ: LINE-1, デバッグ: ON")
    print()
    
    try:
        receiver.recv()
    except KeyboardInterrupt:
        conn.close()
        print("\n終了しました")


if __name__ == "__main__":
    main()
