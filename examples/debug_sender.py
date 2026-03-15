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

    def send(self):
        # data = "ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C0002 7FFF"
        # data = "ERXDATA 0003 0000 3253 F000 49 82 03031800015A0532000500260001040C00D801260009050C000204630001012600250572001301260003057200CD002600030572001B0574011A05660B51052A0C75 0003 7FF"
        # data = "ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7170 8001 7FFF"
        # data = "ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C"

        # 実際のセンサーから取れたデータ
        # data = "ERXDATA B07C 0000 3D3C F000 4D 3A 030310FF013A05320157000700000362000000070000036200000007727D B07C 7FFF\r\n" # current_pulse
        data = "ERXDATA 1115 0000 0464 F000 4D 7A 03030900014E0532000C00260016050C001900260016050C002500260016050C004B00260007050C005700260007050C000C0563009905660A5C052A070D 1115 7FFF\r\n" # vibration



        # チェックサムに失敗する電文
        # data = "ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7199 8001 7FFF"
        # data = "ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C"
        data = data.encode('utf-8')  # バイナリに変換

        # data = "ERXDATA 0002 0000 62BE F000 18 20 030301FF012605320C90052A11AF052C7C"

        self.udpClntSock.sendto(data, self.DstAddr)  # 宛先アドレスに送信


udp = udpsend()  
udp.send()  
