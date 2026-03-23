#!/usr/bin/env python3
"""
振動センサ1LZのFFT有効/無効時のテストスクリプト

FFT有効時と無効時のデータを直接解析して、出力結果を確認します。
"""

from murata_sensor import create_sensor
import json


def test_fft_enabled():
    """FFT有効時のテスト（ピーク値が有効）"""
    print("=" * 80)
    print("【テスト1】FFT有効時のデータ解析")
    print("=" * 80)
    
    # FFT有効時のデータ（仕様書の例）
    data = b"ERXDATA 0003 0000 25B3 F000 1A 7A 0303090001290532000C00260002050C002500260001050C000501260001050C003E00260001050C00AF00260001050C00010563014305660019002A0F03 0003 7FFF"
    
    sensor = create_sensor(data)
    
    print(f"センサータイプ: {sensor.info.get('sensor_type_code', 'N/A')}")
    print(f"ユニットID: {sensor.info['unit_id']}")
    print(f"センサー状態: {sensor.info['status']['description']}")
    print()
    print("解析結果:")
    
    for key, value in sensor.values.items():
        status = "✓" if value['value'] is not None else "✗"
        print(f"  {status} {key:25s}: {value['value']} {value['unit']}")
    
    # ピーク値が有効であることを確認
    assert sensor.values['peak-frequency-1']['value'] == 12, "ピーク周波数1が正しく解析されていません"
    assert sensor.values['peak-acceleration-1']['value'] == 0.02, "ピーク加速度1が正しく解析されていません"
    assert sensor.values['peak-frequency-5']['value'] == 175, "ピーク周波数5が正しく解析されていません"
    
    print("\n✓ FFT有効時のテスト: 成功")
    return sensor


def test_fft_disabled():
    """FFT無効時のテスト（ピーク値が無効）"""
    print("\n" + "=" * 80)
    print("【テスト2】FFT無効時のデータ解析")
    print("=" * 80)
    
    # FFT無効時のデータ（ピーク値がすべてFFFFFF##）
    data = b"ERXDATA 8001 0000 1012 F000 2A 7A 03030900012F0532FFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0CFFFFFF26FFFFFF0C00000063000000660019002A7170 8001 7FFF"
    
    sensor = create_sensor(data)
    
    print(f"センサータイプ: {sensor.info.get('sensor_type_code', 'N/A')}")
    print(f"ユニットID: {sensor.info['unit_id']}")
    print(f"センサー状態: {sensor.info['status']['description']}")
    print()
    print("解析結果:")
    
    for key, value in sensor.values.items():
        status = "✓" if value['value'] is not None else "✗(無効)"
        print(f"  {status} {key:25s}: {value['value']} {value['unit']}")
    
    # ピーク値が無効（None）であることを確認
    assert sensor.values['peak-frequency-1']['value'] is None, "ピーク周波数1はNoneであるべきです"
    assert sensor.values['peak-acceleration-1']['value'] is None, "ピーク加速度1はNoneであるべきです"
    assert sensor.values['peak-frequency-5']['value'] is None, "ピーク周波数5はNoneであるべきです"
    
    # RMS、尖度は有効な値（0.0）
    assert sensor.values['acceleration-RMS']['value'] == 0.0, "加速度RMSは0.0であるべきです"
    assert sensor.values['kurtosis']['value'] == 0.0, "尖度は0.0であるべきです"
    assert sensor.values['temperature']['value'] == 25, "温度は有効であるべきです"
    
    print("\n✓ FFT無効時のテスト: 成功")
    return sensor


def test_real_sensor_data():
    """実際のセンサーデータでのテスト"""
    print("\n" + "=" * 80)
    print("【テスト3】実際のセンサーデータ解析")
    print("=" * 80)
    
    # 実際のセンサーから取得したデータ
    data = b"ERXDATA 1115 0000 0464 F000 4D 7A 03030900014E0532000C00260016050C001900260016050C002500260016050C004B00260007050C005700260007050C000C0563009905660A5C052A070D 1115 7FFF"
    
    sensor = create_sensor(data)
    
    print(f"センサータイプ: {sensor.info.get('sensor_type_code', 'N/A')}")
    print(f"ユニットID: {sensor.info['unit_id']}")
    print()
    print("解析結果:")
    
    for key, value in sensor.values.items():
        status = "✓" if value['value'] is not None else "✗(無効)"
        print(f"  {status} {key:25s}: {value['value']} {value['unit']}")
    
    print("\n✓ 実データのテスト: 成功")
    return sensor


if __name__ == "__main__":
    print("振動センサ1LZ FFT解析テスト\n")
    
    try:
        sensor1 = test_fft_enabled()
        sensor2 = test_fft_disabled()
        sensor3 = test_real_sensor_data()
        
        print("\n" + "=" * 80)
        print("全テスト成功！")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"\n✗ テスト失敗: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
