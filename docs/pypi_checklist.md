# PyPI登録前チェックリスト
# PyPI Publishing Checklist

このチェックリストを使用して、PyPIへの登録準備が完了しているか確認してください。

**対象環境**: WSL（Windows Subsystem for Linux）。記載のコマンドは WSL の bash で実行することを想定しています。

---

## 📋 必須ファイル / Required Files

### パッケージ設定ファイル / Package Configuration Files

- [x] **pyproject.toml**
  - [x] パッケージ名が定義されている
  - [x] バージョン番号が正しい
  - [x] 著者情報が記載されている
  - [x] ライセンスが指定されている
  - [x] Python要件が指定されている (>=3.8)
  - [x] classifiers（分類）が適切
  - [x] キーワードが設定されている
  - [x] プロジェクトURLが正しい

- [x] **setup.py**
  - [x] パッケージ名が定義されている
  - [x] バージョン番号がpyproject.tomlと一致
  - [x] 長い説明がREADMEから読み込まれる
  - [x] 依存関係が記載されている（または空）
  - [x] find_packages()で適切に除外設定

- [x] **MANIFEST.in**
  - [x] README.mdが含まれる
  - [x] LICENSEが含まれる
  - [x] CHANGELOG.mdが含まれる
  - [x] docsディレクトリが含まれる
  - [x] examplesディレクトリが含まれる
  - [x] テストディレクトリが除外される
  - [x] 開発用ファイルが除外される

### ドキュメント / Documentation

- [x] **README.md**
  - [x] プロジェクト概要
  - [x] インストール方法
  - [x] クイックスタートガイド
  - [x] 使用例
  - [x] APIリファレンス
  - [x] ライセンス情報
  - [x] サポート情報
  - [x] バッジ（Python version, License）

- [x] **LICENSE**
  - [x] 適切なライセンステキスト（MIT）
  - [x] 著作権表示
  - [x] 年度が正しい

- [x] **CHANGELOG.md**
  - [x] バージョン履歴
  - [x] 変更内容の分類（Added, Changed, Fixed等）
  - [x] リリース日
  - [x] セマンティックバージョニングに準拠

### コードファイル / Code Files

- [x] **murata_sensor/__init__.py**
  - [x] `__version__` が定義されている
  - [x] `__author__` が定義されている
  - [x] `__license__` が定義されている
  - [x] 公開APIがエクスポートされている（`__all__`）
  - [x] パッケージのdocstringがある

- [x] **murata_sensor/murata_receiver.py**
  - [x] MurataReceiverクラスが実装されている
  - [x] docstringが充実している
  - [x] 型ヒントが記載されている

- [x] **murata_sensor/murata_sensor.py**
  - [x] センサークラス群が実装されている
  - [x] SENSOR_TYPE定数が定義されている
  - [x] docstringが充実している

- [x] **murata_sensor/murata_exception.py**
  - [x] カスタム例外が定義されている
  - [x] docstringがある

---

## 🧪 コード品質 / Code Quality

### テスト / Testing

- [ ] **pytest実行**
  ```bash
  pytest
  ```
  - すべてのテストがパスする

- [ ] **カバレッジ確認**
  ```bash
  pytest --cov=murata_sensor --cov-report=html
  ```
  - カバレッジが80%以上（目標）

### コードスタイル / Code Style

- [ ] **black（フォーマッター）**
  ```bash
  black --check murata_sensor/
  ```
  - フォーマットが統一されている

- [ ] **flake8（リンター）**
  ```bash
  flake8 murata_sensor/
  ```
  - リンターエラーがない

- [ ] **mypy（型チェック）**
  ```bash
  mypy murata_sensor/
  ```
  - 型エラーがない

---

## 🔧 ビルドテスト / Build Testing

### ローカルビルド / Local Build

- [ ] **ビルド環境確認**
  ```bash
  pip install build twine wheel setuptools
  ```

- [ ] **クリーンビルド**
  ```bash
  # 古い成果物を削除
  python scripts/build_and_upload.py --clean-only
  
  # ビルド実行
  python -m build
  ```

- [ ] **ビルド成果物確認**
  ```bash
  ls dist/
  ```
  - `murata_sensor_receiver-0.0.1-py3-none-any.whl` が存在
  - `murata-sensor-receiver-0.0.1.tar.gz` が存在

- [ ] **パッケージ検証**
  ```bash
  python -m twine check dist/*
  ```
  - すべての成果物が `PASSED` となる

### インストールテスト / Installation Test

- [ ] **ローカルインストール**
  ```bash
  # テスト用仮想環境作成（WSL）
  python -m venv test_venv
  source test_venv/bin/activate
  
  # wheelからインストール
  pip install dist/murata_sensor_receiver-0.0.1-py3-none-any.whl
  
  # インポート確認
  python -c "import murata_sensor; print(murata_sensor.__version__)"
  
  # クリーンアップ
  deactivate
  rm -rf test_venv
  ```

---

## 🔐 セキュリティ / Security

### 情報保護 / Information Protection

- [x] **機密情報チェック**
  - [x] APIキーが含まれていない
  - [x] パスワードが含まれていない
  - [x] 個人情報が含まれていない
  - [x] .gitignoreが適切に設定されている

- [ ] **依存関係チェック**
  ```bash
  pip install safety
  safety check
  ```
  - 既知の脆弱性がない

---

## 📦 PyPI準備 / PyPI Preparation

### アカウント / Accounts

- [ ] **PyPIアカウント作成**
  - https://pypi.org/account/register/
  - メール確認完了

- [ ] **TestPyPIアカウント作成**（推奨）
  - https://test.pypi.org/account/register/
  - メール確認完了

### APIトークン / API Tokens

- [ ] **PyPI APIトークン取得**
  - アカウント設定からAPIトークン作成
  - トークンを安全に保存（`pypi-xxx...xxx`形式）
  - 初回は「Entire account」スコープ
  - リリース後はプロジェクト固有トークンに変更

- [ ] **TestPyPI APIトークン取得**（推奨）
  - TestPyPI用のトークン作成
  - トークンを安全に保存

---

## 🚀 アップロード準備 / Upload Preparation

### TestPyPIテスト / TestPyPI Testing

- [ ] **TestPyPIアップロード**
  ```bash
  python -m twine upload --repository testpypi dist/*
  # または
  python scripts/build_and_upload.py --test
  ```

- [ ] **TestPyPIページ確認**
  - https://test.pypi.org/project/murata-sensor-receiver/
  - README表示確認
  - メタデータ確認

- [ ] **TestPyPIからインストール**
  ```bash
  pip install -i https://test.pypi.org/simple/ murata-sensor-receiver
  python -c "import murata_sensor; print(murata_sensor.__version__)"
  ```

### 最終確認 / Final Checks

- [x] **バージョン番号確認**
  - [ ] `murata_sensor/__init__.py`: `__version__ = "0.0.1"`
  - [ ] `pyproject.toml`: `version = "0.0.1"`
  - [ ] `setup.py`: `version="0.0.1"`
  - すべて一致している

- [x] **URL確認**
  - [ ] GitHubリポジトリURLが正しい
  - [ ] ドキュメントURLが正しい
  - [ ] Issue TrackerのURLが正しい

- [ ] **ドキュメント確認**
  - [ ] READMEが最新
  - [ ] CHANGELOGが最新
  - [ ] docsディレクトリが最新

---

## ✅ 本番リリース / Production Release

### Gitタグ / Git Tag

- [ ] **変更をコミット**
  ```bash
  git add .
  git commit -m "Prepare for release v0.0.1"
  ```

- [ ] **バージョンタグ作成**
  ```bash
  git tag v0.0.1
  git push origin main --tags
  ```

### PyPIアップロード / PyPI Upload

- [ ] **最終確認**
  - すべてのチェック項目が完了している
  - TestPyPIでの動作確認済み

- [ ] **本番PyPIアップロード**
  ```bash
  python -m twine upload dist/*
  # または
  python scripts/build_and_upload.py
  ```

- [ ] **PyPIページ確認**
  - https://pypi.org/project/murata-sensor-receiver/
  - すべての情報が正しく表示されている

- [ ] **実際のインストールテスト**
  ```bash
  # 新しい仮想環境で（WSL）
  python -m venv prod_test
  source prod_test/bin/activate
  pip install murata-sensor-receiver
  python -c "import murata_sensor; print(f'v{murata_sensor.__version__} installed!')"
  ```

---

## 📢 リリース後 / Post-Release

### 通知 / Announcements

- [ ] **GitHub Release作成**
  - リリースノート記載
  - CHANGELOG.mdの内容を含める
  - バイナリ添付（オプション）

- [ ] **ドキュメント更新**
  - プロジェクトREADMEの更新
  - 変更履歴の確認

### モニタリング / Monitoring

- [ ] **PyPI統計確認**
  - ダウンロード数のモニタリング
  - エラーレポートの確認

- [ ] **ユーザーフィードバック**
  - GitHubのIssuesを監視
  - 質問への対応

---

## 🔄 次バージョン準備 / Next Version Preparation

### 開発継続 / Continue Development

- [ ] **次のバージョン計画**
  - 機能追加リストの作成
  - バグ修正リストの作成
  - CHANGELOG.mdの[Unreleased]セクション更新

- [ ] **プロジェクト固有トークン**
  - PyPIアカウント設定から作成
  - Scope: "Project: murata-sensor-receiver"
  - より安全な運用へ移行

---

## 📝 チェックリスト完了基準

### 必須項目（これらがすべて完了していること）

- [x] すべての必須ファイルが存在する
- [ ] バージョン番号が統一されている
- [ ] テストがパスする
- [ ] ビルドが成功する
- [ ] twine checkがパスする
- [ ] ローカルインストールが成功する
- [ ] TestPyPIでの動作確認が完了
- [ ] PyPIアカウントとAPIトークンが準備済み

### 推奨項目（品質向上のため）

- [ ] コードカバレッジ80%以上
- [ ] コードスタイルチェックがパスする
- [ ] 型チェックがパスする
- [ ] セキュリティチェックが完了
- [ ] ドキュメントが充実している
- [ ] 使用例が動作する

---

## 🎯 クイックスタート（初回リリース時）

以下のコマンドを順番に実行してください：

```bash
# 1. テスト実行
pytest

# 2. クリーンビルド
python scripts/build_and_upload.py --clean-only
python -m build

# 3. パッケージ検証
python -m twine check dist/*

# 4. TestPyPIにアップロード（テスト）
python -m twine upload --repository testpypi dist/*

# 5. TestPyPIから動作確認
pip install -i https://test.pypi.org/simple/ murata-sensor-receiver

# 6. 問題なければ本番PyPIにアップロード
python -m twine upload dist/*

# 7. Gitタグ作成
git tag v0.0.1
git push origin main --tags
```

---

**重要**: 同じバージョン番号で再アップロードすることはできません。ミスがあった場合はバージョン番号を上げて再度アップロードする必要があります。

---

**作成者 / Author**: Murata Sensor Team  
**対象環境 / Target**: WSL (bash)  
**最終更新 / Last Updated**: 2025-03-15
