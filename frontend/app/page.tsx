import { DashboardPayload, FreshnessStatus, SignalKey } from "../types";
import ThemeToggle from "./theme-toggle";
import VisualModeToggle from "./visual-mode-toggle";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const fallbackPayload: DashboardPayload = {
  schema_version: 3,
  updated_at_jst: "未取得",
  summary: {
    gold_value_text: "データ不足",
    gold_change_text: "前日比: データ不足",
    market_mode: {
      key: "unknown",
      label: "データ不足",
      description: "バックエンドを起動してください。"
    },
    primary_factor: "市場モード判定に必要なデータを取得できません。",
    warning_signals: ["API接続を確認してください"],
    data_freshness: {
      label: "DATA FRESHNESS",
      summary_text: "0指標中 0指標が古い可能性",
      market_mode_assessment: "データ不足",
      counts: { fresh: 0, caution: 0, stale: 0, excluded: 0 }
    }
  },
  indicators: [],
  reference_links: [],
  disclaimer: "このダッシュボードは売買シグナルではなく、市場環境の整理を目的としています。"
};

async function getDashboard(): Promise<DashboardPayload> {
  try {
    const response = await fetch(`${API_BASE}/api/dashboard/current`, { next: { revalidate: 60 } });
    if (!response.ok) return fallbackPayload;
    return response.json();
  } catch {
    return fallbackPayload;
  }
}

const signalClass: Record<SignalKey, string> = {
  tailwind: "signalTailwind",
  headwind: "signalHeadwind",
  risk_on: "signalRiskOn",
  risk_off: "signalRiskOff",
  normal: "signalNormal",
  warning: "signalWarning",
  stress: "signalStress",
  neutral: "signalNeutral",
  unknown: "signalUnknown"
};

const freshnessClass: Record<FreshnessStatus, string> = {
  fresh: "freshnessFresh",
  caution: "freshnessCaution",
  stale: "freshnessStale",
  excluded: "freshnessExcluded"
};

export default async function Home() {
  const data = await getDashboard();
  const modeClass =
    data.summary.market_mode.key === "correlation_break"
      ? "modeAlert"
      : data.summary.market_mode.key === "risk_off_dollar_buying"
        ? "modeWarning"
      : data.summary.market_mode.key === "unknown"
        ? "modeUnknown"
        : "modeNormal";

  return (
    <main className="pageShell">
      <section className="hero">
        <div className="heroTitleRow">
          <div>
            <p className="eyebrow">GOLD MARKET MONITOR</p>
            <h1>GOLD数値監視ダッシュボード</h1>
            <p className="updated">最終更新: {data.updated_at_jst}</p>
          </div>
          <div className="heroControls">
            <ThemeToggle />
            <VisualModeToggle />
          </div>
        </div>
        <div className="goldQuote">
          <span>GOLD現在値</span>
          <strong>{data.summary.gold_value_text}</strong>
          <small>{data.summary.gold_change_text}</small>
        </div>
        <div className="freshnessPanel">
          <span>{data.summary.data_freshness.label}</span>
          <strong>{data.summary.data_freshness.summary_text}</strong>
          <small>相場モード判定: {data.summary.data_freshness.market_mode_assessment}</small>
        </div>
      </section>

      <section className={`modePanel ${modeClass}`}>
        <div>
          <span className="sectionLabel">現在の市場モード</span>
          <h2>{data.summary.market_mode.label}</h2>
          <p>{data.summary.primary_factor}</p>
        </div>
        <div className="warningBox">
          <span className="sectionLabel">警戒シグナル</span>
          {data.summary.warning_signals.length ? (
            <ul>{data.summary.warning_signals.map((warning) => <li key={warning}>{warning}</li>)}</ul>
          ) : (
            <strong>なし</strong>
          )}
        </div>
      </section>

      <section className="sectionHeader">
        <div>
          <p className="eyebrow">MACRO METERS</p>
          <h2>主要7指標</h2>
        </div>
        <p>金利・ドル・リスク心理を前日比で確認</p>
      </section>

      <section className="cardGrid" aria-label="主要7指標">
        {data.indicators.map((item) => (
          <article className={`metricCard ${item.freshness_status === "excluded" ? "metricExcluded" : ""}`} key={item.indicator_key}>
            <div className="cardTop">
              <h3>{item.label}</h3>
              <span className={`signalBadge ${signalClass[item.signal]}`}>{item.signal_label}</span>
            </div>
            <p className="valueText">{item.value_text}</p>
            <p className="changeText">{item.change_text}</p>
            <p className="reasonText">{item.reason}</p>
            <dl className="freshnessMeta">
              <div>
                <dt>データ日付</dt>
                <dd>{item.data_date}</dd>
              </div>
              <div>
                <dt>取得時刻</dt>
                <dd>{item.fetched_at || "未取得"}</dd>
              </div>
              <div>
                <dt>鮮度</dt>
                <dd className={freshnessClass[item.freshness_status]}>{item.freshness_label}</dd>
              </div>
              <div>
                <dt>判定利用</dt>
                <dd>{item.market_mode_usage}</dd>
              </div>
            </dl>
            <div className="cardFooter">
              <span>{item.source_series}</span>
              <a href={item.source_url} target="_blank" rel="noreferrer">{item.source_name}</a>
            </div>
          </article>
        ))}
      </section>

      <section className="sources">
        <div className="sectionHeader">
          <div><p className="eyebrow">SOURCES</p><h2>数値データ参照元</h2></div>
        </div>
        <div className="sourceGrid">
          {data.reference_links.map((link) => (
            <a href={link.source_url} key={`${link.label}-${link.source_name}`} target="_blank" rel="noreferrer">
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
