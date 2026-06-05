import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GOLD Market Brief",
  description: "GOLD環境認識ダッシュボード"
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

