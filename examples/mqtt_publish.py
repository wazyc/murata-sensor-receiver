#!/usr/bin/env python3
"""
MQTT送信例: UDP受信→MQTTブローカー

村田センサーからのUDPパケットを受信し、MQTTブローカーにpublishします。

実行方法:
    python examples/mqtt_publish.py
    python examples/mqtt_publish.py --broker 192.168.1.100 --port 1883

必要なパッケージ:
    pip install paho-mqtt

停止方法:
    Ctrl+C

MQTTトピック:
    murata/sensors/{sensor_type}/data  - センサーデータ全体（JSON）
"""

import argparse
import json
from datetime import datetime

from murata_sensor import MurataReceiver

# paho-mqttがインストールされているか確認
try:
    import paho.mqtt.client as mqtt

    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False


def create_mqtt_client(broker: str, port: int) -> "mqtt.Client":
    """MQTTクライアントを作成して接続"""
    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"MQTTブローカーに接続: {broker}:{port}")
        else:
            print(f"MQTT接続失敗: code={rc}")

    def on_disconnect(client, userdata, rc):
        if rc != 0:
            print("MQTT接続が切断されました")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(broker, port, keepalive=60)
    client.loop_start()
    return client


def main():
    if not MQTT_AVAILABLE:
        print("paho-mqttがインストールされていません")
        print("インストール: pip install paho-mqtt")
        return

    parser = argparse.ArgumentParser(description="センサーデータをMQTTでpublish")
    parser.add_argument("--broker", default="localhost", help="MQTTブローカー")
    parser.add_argument("--port", type=int, default=1883, help="MQTTポート")
    parser.add_argument("--topic-prefix", default="murata/sensors", help="トピックの接頭辞")
    args = parser.parse_args()

    # MQTT接続
    mqtt_client = create_mqtt_client(args.broker, args.port)
    publish_count = 0

    def on_data(sensor_data: dict, addr: tuple) -> None:
        nonlocal publish_count
        topic = f"{args.topic_prefix}/{sensor_data['sensor_type']}/data"

        payload = {
            "timestamp": datetime.now().isoformat(),
            "source_ip": addr[0],
            "source_port": addr[1],
            "sensor_type": sensor_data["sensor_type"],
            "unit_id": sensor_data["info"].get("unit_id"),
            "rssi": sensor_data["info"].get("RSSI"),
            "values": sensor_data["values"],
        }

        mqtt_client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1)
        publish_count += 1
        print(f"Publish: {topic} ({publish_count}件)")

    receiver = MurataReceiver(port=55039, data_callback=on_data)

    print("センサーデータを受信中... (Ctrl+Cで停止)")
    try:
        receiver.recv()
    except KeyboardInterrupt:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print(f"\n終了しました (送信件数: {publish_count})")


if __name__ == "__main__":
    main()
