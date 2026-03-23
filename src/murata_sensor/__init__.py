"""
Murata Sensor Receiver Library

A Python library for receiving and processing data from Murata wireless sensor units.
村田製作所製無線センサユニットからのデータ受信・処理ライブラリ

Basic Usage (UDP Receiver):
    from murata_sensor import MurataReceiver

    def data_handler(sensor_data, addr):
        print(f"Received data from {addr}: {sensor_data['values']}")

    receiver = MurataReceiver(port=55039, data_callback=data_handler)
    receiver.recv()

Text Line Parsing:
    from murata_sensor import parse_text_line

    line = "2024/09/20 16:26:11 192.168.1.100/55061:ERXDATA 5438 0000 ..."
    result = parse_text_line(line)
    print(result['sensor_type'])  # 'vibration'
    print(result['values'])       # {'power-supply-voltage': {...}, ...}
"""

__version__ = "0.2.0"
__author__ = "Murata Sensor Team"
__email__ = "sensor-team@example.com"
__license__ = "MIT"

# Main classes and functions
from .murata_receiver import MurataReceiver, SensorData, create_sensor, parse_text_line
from .async_receiver import AsyncMurataReceiver
from .murata_sensor import (
    MurataSensorBase,
    VibrationSensor,
    VibrationSpeed,
    TemperatureAndHumiditySensor,
    ThreeTemperatureSensor,
    CurrentPulseSensor,
    VoltagePulseSensor,
    CTSensor,
    ThreeCurrentSensor,
    ThreeVoltageSensor,
    ThreeContactSensor,
    WaterproofRepeater,
    WaterLeakSensor,
    PlgDutySensor,
    BrakeCurrentMonitor,
    VibrationWithInstructionSensor,
    CompactThermocoupleSensor,
    SolarExternalSensor,
    ContactOutputSensor,
    AnalogMeterReaderSensor,
    Vibration2TF001SpeedSensor,
    Vibration2TF001AccelSensor,
    SENSOR_TYPE,
    UNIT_TYPE,
)
from .murata_exception import (
    MurataExceptionBase,
    FailedCheckSum,
    FailedCheckSumPayload,
)

# Public API
__all__ = [
    # Main receiver class
    "MurataReceiver",
    "AsyncMurataReceiver",
    "SensorData",
    # Text parsing functions
    "parse_text_line",
    "create_sensor",
    # Sensor classes
    "MurataSensorBase",
    "VibrationSensor",
    "VibrationSpeed",
    "TemperatureAndHumiditySensor",
    "ThreeTemperatureSensor",
    "CurrentPulseSensor",
    "VoltagePulseSensor",
    "CTSensor",
    "ThreeCurrentSensor",
    "ThreeVoltageSensor",
    "ThreeContactSensor",
    "WaterproofRepeater",
    "WaterLeakSensor",
    "PlgDutySensor",
    "BrakeCurrentMonitor",
    "VibrationWithInstructionSensor",
    "CompactThermocoupleSensor",
    "SolarExternalSensor",
    "ContactOutputSensor",
    "AnalogMeterReaderSensor",
    "Vibration2TF001SpeedSensor",
    "Vibration2TF001AccelSensor",
    # Constants
    "SENSOR_TYPE",
    "UNIT_TYPE",
    # Exceptions
    "MurataExceptionBase",
    "FailedCheckSum",
    "FailedCheckSumPayload",
]
