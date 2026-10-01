import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'MAISON — Clienteling', description: '大切なお客様と、次のつながりを。接客スタッフのための顧客管理ポートフォリオ。', robots: { index: false, follow: false } };
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) { return <html lang="ja"><body>{children}</body></html>; }
