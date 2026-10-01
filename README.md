# MAISON — Clienteling

ラグジュアリー販売スタッフの「連絡忘れ・返信忘れ」を防ぐ、顧客管理ポートフォリオ。

- 日本語ダッシュボード、顧客一覧、商談ボード、対応履歴、スタッフ一覧
- 色とラベルで分かるフォロー推奨表示
- 顧客登録・プロフィール編集・連絡記録・次回フォロー日の設定
- 1店舗・10名のスタッフを想定。2店舗目は切り替え用のデモ
- LINE連携のUIプレビュー（実際の連携・送受信なし）
- 25名の架空顧客。変更はブラウザのlocalStorageに保存

## Development

Node.js 22以降、pnpm 11を想定。

```sh
pnpm install --frozen-lockfile
pnpm dev
pnpm build
pnpm start
```

ローカルでファイル監視の上限に達する場合は `pnpm build && pnpm start` で確認できます。

[設計書](docs/design.md) / [将来のDBスキーマ案](docs/schema-proposal.sql)

Vercelは `vercel.json` のNext.js設定でGitHubのmainからデプロイします。環境変数・APIキーは不要です。

認証、店舗間のアクセス制御、サーバー保存、LINE・Teams連携、通知は対象外です。Supabaseは未使用で、SQLは設計資料として同梱しています。Supabaseへの投入は行っていません。

MAISONは自主制作のコンセプトであり、Louis Vuittonの公式サービスではありません。実在のお客様の個人情報を入力する用途には対応していません。
