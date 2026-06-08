export type SignalKey =
  | "tailwind"
  | "headwind"
  | "risk_on"
  | "risk_off"
  | "normal"
  | "warning"
  | "stress"
  | "neutral"
  | "unknown";

export type FreshnessStatus = "fresh" | "caution" | "stale" | "excluded";

export type Indicator = {
  indicator_key: string;
  label: string;
  signal: SignalKey;
  signal_label: string;
  value: number | null;
  change_abs: number | null;
  change_pct: number | null;
  value_text: string;
  change_text: string;
  reason: string;
  source_name: string;
  source_series: string;
  source_url: string;
  as_of: string;
  data_date: string;
  fetched_at: string;
  freshness_status: FreshnessStatus;
  freshness_label: string;
  used_in_market_mode: boolean;
  market_mode_usage: string;
};

export type ReferenceLink = {
  label: string;
  source_name: string;
  source_url: string;
};

export type DashboardPayload = {
  schema_version: 3;
  updated_at_jst: string;
  summary: {
    gold_value_text: string;
    gold_change_text: string;
    market_mode: {
      key: string;
      label: string;
      description: string;
    };
    primary_factor: string;
    warning_signals: string[];
    data_freshness: {
      label: string;
      summary_text: string;
      market_mode_assessment: string;
      counts: Record<FreshnessStatus, number>;
    };
  };
  indicators: Indicator[];
  reference_links: ReferenceLink[];
  disclaimer: string;
};
