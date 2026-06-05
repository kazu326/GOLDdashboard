import { DashboardPayload, StatusKey } from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const fallbackPayload: DashboardPayload = {
  updated_at_jst: "未取得",
  summary: {
    overall_status: "unknown",
    overall_label: "要確認",
    caution_level: "中",
    headline: "GOLD環境を30秒で確認",
    important_event_summary: "バックエンドを起動してください"
  },
  indicators: [
    {
      indicator_key: "us10y",
      label: "米10年金利",
      status: "unknown",
      status_label: "要確認",
      value_text: "要確認",
      change_text: "前回比は要確認",
      comment: "無料データ取得後に表示します。",
      reason: "バックエンド未接続です。",
      source_name: "U.S. Treasury",
      source_url: "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates",
      as_of: "未取得"
    },
    {
      indicator_key: "dollar_index",
      label: "ドル指数または代替ドル指数",
      status: "unknown",
      status_label: "要確認",
      value_text: "要確認",
      change_text: "前回比は要確認",
      comment: "DXY取得不可時は代替ドル指数を明示します。",
      reason: "バックエンド未接続です。",
      source_name: "Federal Reserve / FRED",
      source_url: "https://www.federalreserve.gov/Releases/H10/summary/default.htm",
      as_of: "未取得"
    },
    {
      indicator_key: "vix",
      label: "VIX",
      status: "unknown",
      status_label: "要確認",
      value_text: "要確認",
      change_text: "前回比は要確認",
      comment: "Cboe/FREDから取得します。",
      reason: "バックエンド未接続です。",
      source_name: "Cboe",
      source_url: "https://www.cboe.com/tradable_products/vix/vix_historical_data/",
      as_of: "未取得"
    },
    {
      indicator_key: "gold",
      label: "GOLD価格",
      status: "unknown",
      status_label: "要確認",
      value_text: "要確認",
      change_text: "前回比は要確認",
      comment: "APIキー未設定時は原典確認に寄せます。",
      reason: "バックエンド未接続です。",
      source_name: "Alpha Vantage / FMP",
      source_url: "https://www.alphavantage.co/documentation/",
      as_of: "未取得"
    },
    {
      indicator_key: "sp500",
      label: "S&P500",
      status: "unknown",
      status_label: "要確認",
      value_text: "要確認",
      change_text: "前回比は要確認",
      comment: "リスク選好の補助確認です。",
      reason: "バックエンド未接続です。",
      source_name: "FRED / FMP",
      source_url: "https://fred.stlouisfed.org/series/SP500",
      as_of: "未取得"
    }
  ],
  economic_events: [
    {
      title: "重要経済指標リンク",
      source_name: "BLS / BEA / Fed",
      source_url: "https://www.bls.gov/schedule/news_release/",
      note: "Phase 1ではリンク確認を優先します。"
    }
  ],
  geo_news: [
    {
      title: "地政学ニュースリンク",
      source_name: "ReliefWeb / GDELT",
      source_url: "https://reliefweb.int/updates",
      note: "Phase 1では高度スコアリングを行いません。"
    }
  ],
  reference_links: [],
  disclaimer: "このダッシュボードは投資助言ではなく、市場環境の整理と原典確認を目的としています。"
};

async function getDashboard(): Promise<DashboardPayload> {
  try {
    const response = await fetch(`${API_BASE}/api/dashboard/current`, {
      next: { revalidate: 60 }
    });
    if (!response.ok) {
      return fallbackPayload;
    }
    return response.json();
  } catch {
    return fallbackPayload;
  }
}

const statusClass: Record<StatusKey, string> = {
  green: "statusGreen",
  yellow: "statusYellow",
  red: "statusRed",
  unknown: "statusUnknown"
};

export default async function Home() {
  const data = await getDashboard();
  const allLinks = [
    ...data.reference_links,
    ...data.economic_events.map((item) => ({
      label: item.title,
      source_name: item.source_name,
      source_url: item.source_url
    })),
    ...data.geo_news.map((item) => ({
      label: item.title,
      source_name: item.source_name,
      source_url: item.source_url
    }))
  ];

  return (
    <main className="pageShell">
      <section className="summaryBand">
        <div>
          <p className="eyebrow">GOLD Market Brief</p>
          <h1>{data.summary.headline}</h1>
          <p className="updated">最終更新: {data.updated_at_jst}</p>
        </div>
        <div className="summaryMetrics" aria-label="市場環境サマリー">
          <div className={`summaryPill ${statusClass[data.summary.overall_status]}`}>
            <span>総合評価</span>
            <strong>{data.summary.overall_label}</strong>
          </div>
          <div className="summaryPill caution">
            <span>本日の注意度</span>
            <strong>{data.summary.caution_level}</strong>
          </div>
          <div className="eventBox">
            <span>重要イベント</span>
            <strong>{data.summary.important_event_summary}</strong>
          </div>
        </div>
      </section>

      <section className="cardGrid" aria-label="主要指標">
        {data.indicators.map((item) => (
          <article className="metricCard" key={item.indicator_key}>
            <div className="cardTop">
              <h2>{item.label}</h2>
              <span className={`statusBadge ${statusClass[item.status]}`}>{item.status_label}</span>
            </div>
            <p className="valueText">{item.value_text}</p>
            <p className="changeText">{item.change_text}</p>
            <p className="commentText">{item.comment}</p>
            <a className="sourceLink" href={item.source_url} target="_blank" rel="noreferrer">
              原典: {item.source_name}
            </a>
          </article>
        ))}

        <article className="metricCard linkCard">
          <div className="cardTop">
            <h2>重要経済指標</h2>
            <span className="statusBadge statusUnknown">要確認</span>
          </div>
          {data.economic_events.slice(0, 3).map((item) => (
            <a className="stackedLink" href={item.source_url} key={item.source_url} target="_blank" rel="noreferrer">
              <strong>{item.title}</strong>
              <span>{item.note}</span>
            </a>
          ))}
        </article>

        <article className="metricCard linkCard">
          <div className="cardTop">
            <h2>地政学ニュース</h2>
            <span className="statusBadge statusUnknown">要確認</span>
          </div>
          {data.geo_news.slice(0, 3).map((item) => (
            <a className="stackedLink" href={item.source_url} key={item.source_url} target="_blank" rel="noreferrer">
              <strong>{item.title}</strong>
              <span>{item.note}</span>
            </a>
          ))}
        </article>
      </section>

      <section className="sources">
        <h2>参考リンク</h2>
        <div className="sourceGrid">
          {allLinks.map((link, index) => (
            <a href={link.source_url} key={`${link.source_url}-${index}`} target="_blank" rel="noreferrer">
              <span>{link.label}</span>
              <strong>{link.source_name}</strong>
            </a>
          ))}
        </div>
      </section>

      <footer>{data.disclaimer}</footer>
    </main>
  );
}

