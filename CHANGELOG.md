# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.4.0] - 2026-05-01

### Added
- 対応済みセンサー一覧を取得するメタデータAPI
  - `get_supported_sensors()`
  - `get_supported_sensor_types()`
  - `is_supported_sensor_type()`
  - `is_supported_sensor_code()`
- 未解析データの扱い（UDP受信・テキスト解析・非同期受信）
  - `MurataReceiver` / `AsyncMurataReceiver` に `unparsed_callback` を追加
  - 未解析理由の分類（チェックサム不正、非村田形式、未対応センサー種別など）
  - `build_unparsed_data()` による未解析ペイロード辞書の生成
  - `parse_text_line(..., strict=False)` で未解析行を辞書として返却可能に
  - `AsyncMurataReceiver` の `include_unparsed` オプション
- GitHub Actions による CI（テスト・Lint）
- flake8 設定ファイル（`.flake8`）

### Changed
- ビルド・配布まわりの整理（レガシーなアップロード用スクリプト削除、`MANIFEST.in` の除外設定見直し）
- README の開発環境セットアップ（flake8 等）を更新
- README、API仕様書、概要ドキュメント、アーキテクチャ設計書の対応センサー記述を同期
- 非同期受信のテストで `asyncio.run` を用いたイベントループ管理に統一

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

**Note**: v0.x.x is alpha/beta and the API may change.
