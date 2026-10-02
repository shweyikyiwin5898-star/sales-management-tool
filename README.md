# MAISON — Python Clienteling

ウィンの販売スタッフ向け顧客管理ポートフォリオ。Python 3.12 + Flask + Jinjaで画面と業務ロジックを実装しています。

**公開サイト:** https://sales-management-tool-pi.vercel.app/

- ブラウン／キャメル／クリームの配色、日本語・英語切替
- スマホは顧客カード、下部ナビ、タッチ対応の入力ダイアログ
- 顧客登録・編集・連絡記録・次回フォロー日・商談ステータス
- 返信忘れ／連絡忘れを色とラベルで表示
- ウィンを含む10名、架空顧客25名、店舗切替デモ
- LINE接続は画面プレビューのみ

## ローカル起動

Python 3.12以降を使用します。Node.jsは不要です。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Windowsでは有効化コマンドを `.venv\Scripts\activate` に置き換えます。ブラウザで http://127.0.0.1:5001 を開きます。

```sh
python -m unittest discover -s tests -v
```

## ファイル構成

| ファイル | 役割 |
|---|---|
| `app.py` | Flaskのルーティング、API、画面コンテキスト |
| `domain.py` | 顧客検証、連絡記録、日付・アラート判定 |
| `i18n.py` | 日本語・英語の表示辞書 |
| `templates/` | Jinjaの画面・フォーム |
| `public/assets/` | CSS、通信とブラウザ保存を担うJavaScript |
| `tests/test_app.py` | Python標準unittestによる15テスト |

[設計書](docs/design.md) / [Python課題の説明資料](docs/python-assignment.md)

VercelのFlask対応を使いGitHub mainからデプロイ。APIキーや環境変数は不要です。変更はブラウザのlocalStorageに保存し、画面操作時にPythonサーバーで計算・描画します。サーバー側の永続DBはなく、Supabaseは未接続・SQL未投入です。旧Next.js版のブラウザデータは移行せず、新しいデモとして起動します。

MAISONは自主制作で、Louis Vuittonの公式サービスではありません。架空データ用のポートフォリオです。
