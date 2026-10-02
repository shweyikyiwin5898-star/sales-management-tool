-- Python版にも未接続。スタッフUUID、商品配列、翻訳辞書への変換は移行実装時に必要。
-- MAISON: 将来の移行用スキーマ案。現行アプリはlocalStorageを使用。
-- 未投入・未実機検証。DB接続・認証・公開APIは別途実装が必要。
-- 新規のデモ用DBで管理者としてレビュー後に実行するための資料。
begin;
create schema maison_demo;
create table maison_demo.stores (
  id text primary key,
  name text not null
);
create table maison_demo.staff (
  id uuid primary key default gen_random_uuid(),
  store_id text not null references maison_demo.stores(id),
  name text not null,
  unique (store_id, id)
);
create table maison_demo.customers (
  id uuid primary key default gen_random_uuid(),
  store_id text not null references maison_demo.stores(id),
  staff_id uuid not null,
  name text not null check (length(trim(name)) between 1 and 80),
  kana text not null default '',
  email text not null default '',
  phone text not null default '',
  birthday date,
  size text not null default '',
  tier text not null default 'Regular' check (tier in ('Regular', 'VIC')),
  interests text[] not null default '{}',
  stage text not null default 'visit' check (stage in ('visit','proposal','considering','return','purchased','aftercare')),
  next_date date not null,
  note text not null default '',
  purchase text not null default '',
  total integer not null default 0 check (total >= 0),
  foreign key (store_id, staff_id) references maison_demo.staff(store_id, id)
);
create table maison_demo.activities (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references maison_demo.customers(id),
  date date not null,
  type text not null check (type in ('sent','received','meeting','memo')),
  body text not null check (length(trim(body)) between 1 and 2000),
  created_at timestamptz not null default now()
);
create index customers_staff_followup_idx on maison_demo.customers (store_id, staff_id, next_date);
create index activities_customer_date_idx on maison_demo.activities (customer_id, date desc, created_at desc);
-- 最終連絡日と未返信は最新のメモ以外の活動から導出する。
-- このスキーマはData APIに公開せず、権限・ポリシーは将来の仕様で設計する。
alter table maison_demo.stores enable row level security;
alter table maison_demo.staff enable row level security;
alter table maison_demo.customers enable row level security;
alter table maison_demo.activities enable row level security;
revoke all on schema maison_demo from public, anon, authenticated;
revoke all on all tables in schema maison_demo from public, anon, authenticated;
commit;
