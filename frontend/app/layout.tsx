import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";

export const metadata: Metadata = {
  title: "GOLD数値監視ダッシュボード",
  description: "GOLDに影響する主要7指標と市場モードを確認するダッシュボード"
};

const themeScript = `
(function () {
  try {
    var stored = localStorage.getItem("gold-dashboard-theme");
    var theme = stored === "light" || stored === "dark"
      ? stored
      : window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches
        ? "light"
        : "dark";
    document.documentElement.dataset.theme = theme;
    var visualMode = localStorage.getItem("gold-dashboard-visual-mode") === "on" ? "on" : "off";
    document.documentElement.dataset.visualMode = visualMode;
  } catch (_) {
    document.documentElement.dataset.theme = "dark";
    document.documentElement.dataset.visualMode = "off";
  }
})();
`;

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" data-theme="dark" data-visual-mode="off" suppressHydrationWarning>
      <head>
        <Script id="theme-init" strategy="beforeInteractive" dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
