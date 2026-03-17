# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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
