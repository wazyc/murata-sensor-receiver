# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- 電文仕様K対応: 熱電対ユニット 2PF（`thermocouple_unit` / `ThermocoupleUnitSensor`）
  - `03033FFF` / `03033F02` / `03033F03` を識別
  - CH1-3 の熱電対タイプと温度を解析（無効値は `None`）
- 1ZS / 2DB / 2SL / 2ZS / 2ZU の状態コード（SS）変種を `SENSOR_TYPE` に追記

### Changed
- 対応電文仕様表記を K に更新（README / overview）
- 非振動センサーの `info.status` を仕様の状態表に合わせて更新
  - `00`=正常 / `02`=無線異常 / `03`=センサ異常 / `FF`=RFU
- アナログメーター読取ユニット 2YT の角度(Min/Max)・補正値の単位を単位なし（`-`）に訂正
- README / API仕様書に経路別の `timestamp` 型契約を追記
  - UDP / 未解析は ISO8601 `str`（組み込み向けの正）
  - `parse_text_line` 成功時は naive `datetime | None`（JSON化時は要文字列化）

### Notes (2.0 candidates)
- 公開辞書の `timestamp` をすべて ISO8601 `str` に揃える
  - `parse_text_line` 成功時の `datetime` → `str` への変更を含む破壊的変更
  - 1.x では型変更しない（現行契約を維持）

## [1.0.0] - 2026-08-22

### Fixed
- Async 解析済みデータに `sensor_type_code` を追加（Sync と共通の `build_sensor_data`）
- `SolarExternalSensor` の緯度・経度を values 規約 `{value, unit, unit_name}` に統一
- 振動系センサータイプ全体で SS=00/01 の状態解析（正常/レンジオーバー）を適用
- README / API仕様書を実装のコールバック経路・データ形状に合わせて修正

### Added
- 対応済みセンサー一覧を取得するメタデータAPIを追加
  - `get_supported_sensors()`
  - `get_supported_sensor_types()`
  - `is_supported_sensor_type()`
  - `is_supported_sensor_code()`
- `get_supported_sensors()` に `parse_verified` を追加し、実電文による値解析の自動テスト済み範囲を明示
- GitHub Actions による CI（テスト・Lint）
- flake8 設定ファイル（`.flake8`）

### Changed
- README、API仕様書、概要ドキュメント、アーキテクチャ設計書の対応センサー記述を同期
- 対応センサー一覧で「登録済み」と「解析検証済み」を区別して記載

## [0.3.0] - 2026-04-27

### Added
- 防水防塵接点パルスユニット 2ZS に対応
  - `030338FF` を `waterproof_contact_pulse` として識別
  - 状態1-3、エッジカウント1-3、桁上がりカウント1-3を解析
- 防水防塵アナログ出力無線化ユニット 2ZU に対応
  - `030339FF` を `waterproof_analog_output` として識別
  - 電流値1-3、電圧値1-3、測定モードを解析

### Changed
- README、API仕様書、概要ドキュメントの対応センサー一覧を更新

## [0.2.0] - 2026-03-23

### Added
- ドキュメントバージョンGに対応
- 振動センサー（1LZ）のFFT解析結果出力に対応
  - FFT有効時にピーク周波数（peak-frequency-1 ~ 5）を出力
  - FFT有効時にピーク加速度（peak-acceleration-1 ~ 5）を出力
  - 合計14項目のデータを提供
- 無効値の自動検出機能を追加
  - ペイロード内の無効値（`FFFFFF##`）を検出
  - 検出した無効値を `value: None` として返す
  - 全センサータイプで統一的に処理
- 新しいテストスクリプトを追加
  - `examples/test_fft_modes.py`: FFT有効/無効時の動作確認
  - `examples/test_invalid_values.py`: 無効値処理の動作確認
 
### Changed
- VibrationSensorクラスの出力項目を拡張（4項目→14項目、FFT有効時）
- ドキュメントを全面更新
  - API仕様書に無効値処理セクション追加
  - アーキテクチャ設計書に無効値検出フロー追加
  - READMEに詳細な出力例を追加

### Fixed
- FFT無効時にピーク周波数・加速度が無効値として適切に処理されるように改善
- 小型熱電対（2FW）など各センサーで無効値が正しく`None`として返されるように修正

## [0.1.0] - 2026-03-17

### Added
- センサ種別コード（sensor_type_code）を解析結果に追加
  - UDP受信時のコールバックデータに `sensor_type_code` フィールドを追加
  - テキスト解析（parse_text_line）の戻り値に `sensor_type_code` フィールドを追加
  - MurataSensorBase.info に `sensor_type_code` を格納
- README に「解析結果のデータ構造」セクションを追加
  - 温湿度センサーと振動センサーの具体的なサンプルを提示
  - UDP受信とテキスト解析の両方の例を記載

### Changed
- docs/api_specification.md を更新（sensor_type_code の追加に対応）
- docs/architecture.md のデータフロー図を更新

### Fixed
- 不要な SENSOR_TYPE_CODE マッピング辞書を削除（データから直接抽出する実装に統一）

## [0.0.1] - 2026-03-15

### Added
- Initial release of Murata Sensor Receiver library
---

## Versioning Rules

This project adheres to Semantic Versioning:

- **MAJOR**: Breaking changes (API changes)
- **MINOR**: Backward-compatible feature additions
- **PATCH**: Bug fixes

---

**Note**: v1.0.0 以降は安定版として扱います。破壊的変更がある場合はメジャーバージョンを上げます。
