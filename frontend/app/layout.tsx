import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GOLD数値監視ダッシュボード",
  description: "GOLDに影響する主要7指標と市場モードを確認するダッシュボード"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
