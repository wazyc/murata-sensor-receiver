# PyPI パッケージ登録ガイド
# PyPI Package Publishing Guide

このドキュメントは、murata-sensor-receiver ライブラリをPyPIに登録するための手順を説明します。

**対象環境**: WSL（Windows Subsystem for Linux）。記載のコマンドは WSL の bash で実行することを想定しています。

---

## 目次 / Table of Contents

1. [事前準備](#事前準備--prerequisites)
2. [PyPIアカウントの作成](#pypiアカウントの作成)
3. [APIトークンの取得](#apiトークンの取得)
4. [パッケージのビルド](#パッケージのビルド)
5. [TestPyPIでのテスト](#testpypiでのテスト)
6. [本番PyPIへのアップロード](#本番pypiへのアップロード)
7. [インストール確認](#インストール確認)
8. [トラブルシューティング](#トラブルシューティング)

---

## 事前準備 / Prerequisites

### 1. 必要なツールのインストール

WSL では `python` が `python3` のエイリアスでない場合があるため、必要に応じて `python3` / `pip3` を使用してください。仮想環境（`python -m venv .venv`）内で実行する場合は `python` で問題ありません。

```bash
# ビルドツールのインストール
pip install build twine wheel setuptools

# 開発依存関係のインストール（テスト実行のため）
pip install -e ".[dev]"
```

### 2. パッケージ構成の確認

以下のファイルが存在することを確認してください：

```
murataSensorRcvSrv/
├── murata_sensor/          # メインパッケージ
│   ├── __init__.py        # バージョン情報含む
│   ├── murata_receiver.py
│   ├── murata_sensor.py
│   └── murata_exception.py
├── tests/                  # テストコード
├── examples/               # 使用例
├── docs/                   # ドキュメント
├── pyproject.toml         # パッケージ設定（モダン）
├── setup.py               # パッケージ設定（従来型）
├── MANIFEST.in            # パッケージ含有ファイル指定
├── README.md              # プロジェクト説明
├── LICENSE                # ライセンス
└── CHANGELOG.md           # 変更履歴
```

### 3. バージョン番号の確認

以下のファイルでバージョン番号が一致していることを確認：

- `murata_sensor/__init__.py` の `__version__`
- `pyproject.toml` の `version`
- `setup.py` の `version`

```bash
# バージョン確認コマンド
python -c "import murata_sensor; print(murata_sensor.__version__)"
```

---

## PyPIアカウントの作成

### 1. PyPIアカウント登録

**本番PyPI**: https://pypi.org/account/register/

1. PyPI公式サイトにアクセス
2. 右上の「Register」をクリック
3. 必要事項を入力：
   - Username（ユーザー名）
   - Email（メールアドレス）
   - Password（パスワード）
4. 利用規約に同意してアカウント作成
5. 確認メールが届くので、リンクをクリックして認証

### 2. TestPyPIアカウント登録（推奨）

**TestPyPI**: https://test.pypi.org/account/register/

本番環境の前にテストするため、TestPyPIアカウントも作成することを推奨します。

**注意**: PyPIとTestPyPIは別のアカウントシステムです。両方にそれぞれ登録する必要があります。

---

## APIトークンの取得

パスワードの代わりにAPIトークンを使用することを強く推奨します。

### 1. PyPI APIトークンの作成

1. PyPIにログイン: https://pypi.org/
2. 右上のユーザー名をクリック → 「Account settings」
3. 左メニューから「API tokens」を選択
4. 「Add API token」をクリック
5. トークン情報を入力：
   - **Token name**: `murata-sensor-receiver-upload` など分かりやすい名前
   - **Scope**: 
     - 初回アップロード前: 「Entire account」を選択
     - 初回アップロード後: 「Project: murata-sensor-receiver」を選択（より安全）
6. 「Create token」をクリック
7. **重要**: 表示されたトークン（`pypi-xxx...xxx`）をコピーして安全に保存
   - このトークンは一度しか表示されません
   - 失った場合は新しいトークンを作成する必要があります

### 2. TestPyPI APIトークンの作成

同様の手順でTestPyPIのトークンも作成します：
https://test.pypi.org/manage/account/

### 3. 環境変数の設定（オプション）

毎回入力する手間を省くため、環境変数に設定できます。

**WSL（推奨・この環境）:**
```bash
# 一時的な設定（現在のセッションのみ）
export TWINE_USERNAME=__token__
export TWINE_PASSWORD="pypi-xxx...xxx"

# 永続的な設定: ~/.bashrc に追加して source ~/.bashrc
echo 'export TWINE_USERNAME="__token__"' >> ~/.bashrc
echo 'export TWINE_PASSWORD="pypi-xxx...xxx"' >> ~/.bashrc
source ~/.bashrc
```

トークンをファイルに書きたくない場合は、アップロード時に twine が対話でパスワードを聞くため、環境変数は必須ではありません。

**セキュリティ注意事項**:
- トークンをGitにコミットしないでください
- `.gitignore` に `.env` ファイルを追加してください
- チーム開発の場合は、各メンバーが個別のトークンを使用してください

---

## パッケージのビルド

### 1. テストの実行

アップロード前に必ずテストを実行してください：

```bash
# すべてのテストを実行
pytest

# カバレッジ付きで実行
pytest --cov=murata_sensor --cov-report=html

# コードフォーマットチェック
black --check src/

# 型チェック
mypy src/
```

### 2. 古いビルド成果物のクリーンアップ

```bash
# 自動クリーン（推奨）
python scripts/build_and_upload.py --clean-only

# または手動で削除（WSL）
rm -rf build dist
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
```

### 3. パッケージのビルド

```bash
# 方法1: setuptools を使用
python setup.py sdist bdist_wheel

# 方法2: buildモジュールを使用（推奨）
python -m build

# 方法3: 自動化スクリプトを使用
python scripts/build_and_upload.py --skip-tests
```

ビルドが成功すると、`dist/` ディレクトリに以下のファイルが作成されます：

```
dist/
├── murata_sensor_receiver-0.0.1-py3-none-any.whl  # Wheel形式
└── murata-sensor-receiver-0.0.1.tar.gz            # Source形式
```

### 4. ビルド成果物の検証

```bash
# パッケージの内容確認
python -m twine check dist/*

# 期待される出力
# Checking dist/murata_sensor_receiver-0.0.1-py3-none-any.whl: PASSED
# Checking dist/murata-sensor-receiver-0.0.1.tar.gz: PASSED
```

**エラーがある場合はアップロードせず、修正してください。**

---

## TestPyPIでのテスト

本番環境にアップロードする前に、TestPyPIで動作確認することを強く推奨します。

### 1. TestPyPIへのアップロード

```bash
# 方法1: twineコマンドを直接使用
python -m twine upload --repository testpypi dist/*

# 方法2: 自動化スクリプトを使用
python scripts/build_and_upload.py --test
```

**認証情報の入力**（環境変数未設定の場合）:
```
Enter your username: __token__
Enter your password: pypi-xxx...xxx  # TestPyPIのAPIトークン
```

### 2. アップロード確認

成功すると以下のようなメッセージが表示されます：

```
Uploading distributions to https://test.pypi.org/legacy/
Uploading murata_sensor_receiver-0.0.1-py3-none-any.whl
Uploading murata-sensor-receiver-0.0.1.tar.gz
View at:
https://test.pypi.org/project/murata-sensor-receiver/0.0.1/
```

ブラウザでリンクを開いて確認してください。

### 3. TestPyPIからのインストールテスト

```bash
# 仮想環境を作成してテスト（WSL）
python -m venv test_env
source test_env/bin/activate

# TestPyPIからインストール
pip install -i https://test.pypi.org/simple/ murata-sensor-receiver

# インストール確認
python -c "import murata_sensor; print(murata_sensor.__version__)"

# 簡単な動作テスト
python -c "from murata_sensor import MurataReceiver; print('Import successful!')"
```

### 4. テスト環境のクリーンアップ

```bash
deactivate
rm -rf test_env
```

---

## 本番PyPIへのアップロード

TestPyPIでの動作確認が完了したら、本番環境にアップロードします。

### 1. 最終確認チェックリスト

- [ ] すべてのテストが成功している
- [ ] README.mdが最新の状態である
- [ ] CHANGELOG.mdが更新されている
- [ ] バージョン番号が正しい
- [ ] TestPyPIで動作確認済み
- [ ] GitHubリポジトリのURLが正しい（setup.py, pyproject.toml）
- [ ] ライセンス情報が正確である

### 2. 本番PyPIへのアップロード

```bash
# 方法1: twineコマンドを直接使用
python -m twine upload dist/*

# 方法2: 自動化スクリプトを使用
python scripts/build_and_upload.py
```

**認証情報の入力**（環境変数未設定の場合）:
```
Enter your username: __token__
Enter your password: pypi-xxx...xxx  # 本番PyPIのAPIトークン
```

### 3. アップロード成功の確認

```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading murata_sensor_receiver-0.0.1-py3-none-any.whl
Uploading murata-sensor-receiver-0.0.1.tar.gz

View at:
https://pypi.org/project/murata-sensor-receiver/0.0.1/
```

**重要な注意事項**:
- 同じバージョン番号で再アップロードすることはできません
- ミスがあった場合は、バージョン番号を上げて再アップロードする必要があります

---

## インストール確認

### 1. 新しい環境でインストールテスト

```bash
# 新しい仮想環境を作成（WSL）
python -m venv prod_test_env
source prod_test_env/bin/activate

# PyPIからインストール
pip install murata-sensor-receiver

# バージョン確認
python -c "import murata_sensor; print(f'Version: {murata_sensor.__version__}')"

# 動作確認（examples がプロジェクト内にある場合）
python examples/simple_stdout.py
```

### 2. PyPIページの確認

https://pypi.org/project/murata-sensor-receiver/ にアクセスして以下を確認：

- [ ] プロジェクト説明（README）が正しく表示されている
- [ ] バージョン番号が正しい
- [ ] ライセンス情報が表示されている
- [ ] プロジェクトリンクが正しい
- [ ] Pythonバージョン要件が正しい
- [ ] インストールコマンドが表示されている

---

## トラブルシューティング

### エラー: "Invalid distribution file"

**原因**: パッケージ名やメタデータに問題がある

**解決方法**:
```bash
# パッケージの検証
python -m twine check dist/*

# エラーメッセージを確認し、該当箇所を修正
# 修正後、再ビルド
python scripts/build_and_upload.py --clean-only
python -m build
```

### エラー: "File already exists"

**原因**: 同じバージョンが既にアップロード済み

**解決方法**:
1. バージョン番号を上げる（`__init__.py`, `pyproject.toml`, `setup.py`）
2. `CHANGELOG.md` を更新
3. 再ビルドしてアップロード

### エラー: "Invalid or non-existent authentication"

**原因**: APIトークンが正しくない

**解決方法**:
1. PyPIアカウント設定でトークンを確認
2. 必要に応じて新しいトークンを作成
3. ユーザー名は `__token__` （固定）
4. パスワードは `pypi-` で始まるトークン全体

### エラー: "403 Forbidden"

**原因**: パッケージ名が既に使用されている、または権限がない

**解決方法**:
1. パッケージ名を変更（`pyproject.toml`, `setup.py`）
2. または、既存のパッケージの管理者に連絡

### README.mdが正しく表示されない

**原因**: Markdown形式の問題

**解決方法**:
1. `long_description_content_type="text/markdown"` が設定されているか確認
2. README.mdのMarkdown構文を確認
3. ローカルでMarkdownレンダリングをテスト

---

## 更新版のリリース

### 1. バージョン番号の更新

セマンティックバージョニングに従って更新：

- **MAJOR** (1.0.0): 破壊的変更
- **MINOR** (0.1.0): 新機能追加（後方互換性あり）
- **PATCH** (0.0.2): バグ修正

以下のファイルを更新：
```python
# murata_sensor/__init__.py
__version__ = "0.0.2"
```

```toml
# pyproject.toml
version = "0.0.2"
```

```python
# setup.py
version="0.0.2"
```

### 2. CHANGELOGの更新

```markdown
## [0.0.2] - 2024-10-15

### Fixed / 修正
- Bug fix description

### Added / 追加
- New feature description
```

### 3. リリースフロー

```bash
# 1. 変更をコミット
git add .
git commit -m "Release version 0.0.2"
git tag v0.0.2
git push origin main --tags

# 2. クリーンビルド
python scripts/build_and_upload.py --clean-only

# 3. テスト実行
pytest

# 4. ビルド
python -m build

# 5. TestPyPIでテスト
python -m twine upload --repository testpypi dist/*

# 6. 本番アップロード
python -m twine upload dist/*
```

---

## ベストプラクティス

### セキュリティ

- [ ] APIトークンをGitにコミットしない
- [ ] プロジェクト固有のトークンを使用（アカウント全体ではなく）
- [ ] トークンを定期的にローテーション
- [ ] `.env` ファイルを `.gitignore` に追加

### 品質管理

- [ ] リリース前に必ずテストを実行
- [ ] TestPyPIで動作確認
- [ ] CHANGELOGを常に最新に保つ
- [ ] セマンティックバージョニングに従う
- [ ] ドキュメントを最新に保つ

### コミュニティ

- [ ] 明確なREADMEを提供
- [ ] 使用例を含める
- [ ] ライセンス情報を明記
- [ ] 問題報告の方法を記載
- [ ] コントリビューションガイドラインを提供

---

## 参考リソース

### 公式ドキュメント

- PyPI公式サイト: https://pypi.org/
- TestPyPI: https://test.pypi.org/
- PyPIヘルプ: https://pypi.org/help/
- Packaging Python Projects: https://packaging.python.org/tutorials/packaging-projects/
- Twine Documentation: https://twine.readthedocs.io/

### ツールドキュメント

- setuptools: https://setuptools.pypa.io/
- wheel: https://wheel.readthedocs.io/
- build: https://pypa-build.readthedocs.io/
- twine: https://twine.readthedocs.io/

### その他

- Semantic Versioning: https://semver.org/
- Keep a Changelog: https://keepachangelog.com/

---

## サポート

問題が発生した場合：

1. このガイドのトラブルシューティングセクションを確認
2. PyPI公式ヘルプを参照
3. GitHubのIssuesで報告

---

**作成者 / Author**: Murata Sensor Team  
**対象環境 / Target**: WSL (bash)  
**最終更新 / Last Updated**: 2025-03-15
