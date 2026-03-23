#!/usr/bin/env python3
"""
Debug UDP sender for murata-sensor-receiver library.
murata-sensor-receiverライブラリのデバッグ用UDP送信ツール

このスクリプトは、murata-sensor-receiverライブラリのテストやデバッグを目的としたUDPパケット送信ツールです。

動作の詳細:
1. UDPソケットを初期化します
   - 送信元アドレスをlocalhost:11111に設定します
   - 宛先アドレスをlocalhost:55039に設定します（レシーバーのデフォルトポート）

2. 村田センサー形式のテストデータを準備します
   - 実際のセンサーデータサンプルを使用します
   - 振動センサーのサンプルデータ（ERXDATA形式）を含みます
   - チェックサム検証用のテストデータを提供します

3. データ送信機能を実装します
   - 準備したテストデータをUDPパケットとして送信します
   - バイナリ形式でエンコードして送信します

実行例:
    python examples/debug_sender.py

必要な設定:
    - 受信側（murata-sensor-receiver）がポート55039で動作していること
    - 送信元と宛先が同じマシン（localhost）の場合のみ動作します

使用シナリオ:
    - ライブラリの動作テストが必要な場合
    - センサーデータ受信処理の検証が必要な場合
    - 開発環境でのデバッグが必要な場合
    - 実際のセンサーデータがない場合のテストデータ送信が必要な場合

注意事項:
    - このツールは開発・テスト目的のみで使用してください
    - 本番環境での使用は推奨されません
    - データ形式は実際の村田センサーと一致するよう設計されています

データ形式:
    ERXDATA形式の村田センサーパケット
    - 振動センサーデータのサンプル
    - チェックサム付きの完全なパケット形式
"""

import socket
class udpsend():
    def __init__(self):
        SrcIP = "localhost"  # 送信元IP
        # SrcIP = "172.19.4.32"  # 送信元IP
        SrcPort = 11111  # 送信元ポート番号
        self.SrcAddr = (SrcIP, SrcPort)  # アドレスをtupleに格納

        DstIP = "localhost"  # 宛先IP
        # DstIP = "172.19.4.32"  # 宛先IP
        DstPort = 55039  # 宛先ポート番号
        self.DstAddr = (DstIP, DstPort)  # アドレスをtupleに格納

        self.udpClntSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # ソケット作成
        self.udpClntSock.bind(self.SrcAddr)  # 送信元アドレスでバインド

    def send(self, mode="fft_enabled"):
        """テストデータを送信
        
        Args:
            mode: 送信モード
                - "fft_enabled": FFT有効時のデータ（ピーク値有効）
                - "fft_disabled": FFT無効時のデータ（ピーク値無効）
                - "real": 実際のセンサーデータ
        """
        if mode == "fft_enabled":
            # FFT有効時の例（仕様書より）
            # ピーク周波数1-5、ピーク加速度1-5が有効
            data = "ERXDATA 0003 0000 25B3 F000 1A 7A 0303090001290532000C00260002050C002500260001050C000501260001050C003E00260001050C00AF00260001050C00010563014305660019002A0F03 0003 7FFF"
        elif mode == "fft_disabled":
            # FFT無効時の例（ピーク周波数・加速度がすべてFFFFFF##）
            # 加速度RMS=0.0、尖度=0.0、温度=25℃
            data = "ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7170 8001 7FFF"
        elif mode == "real":
            # 実際のセンサーから取れたデータ（FFT有効）
            data = "ERXDATA 1115 0000 0464 F000 4D 7A 03030900014E0532000C00260016050C001900260016050C002500260016050C004B00260007050C005700260007050C000C0563009905660A5C052A070D 1115 7FFF"
        else:
            raise ValueError(f"Unknown mode: {mode}")

        data = data.encode('utf-8')
        self.udpClntSock.sendto(data, self.DstAddr)


if __name__ == "__main__":
    import sys
    udp = udpsend()
    
    # コマンドライン引数でモードを指定可能
    mode = sys.argv[1] if len(sys.argv) > 1 else "fft_enabled"
    print(f"Sending test data: mode={mode}")
    udp.send(mode=mode)  
