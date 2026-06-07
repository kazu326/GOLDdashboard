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
  source_url: string;
  as_of: string;
};

export type ReferenceLink = {
  label: string;
  source_name: string;
  source_url: string;
};

export type DashboardPayload = {
  schema_version: 2;
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
  };
  indicators: Indicator[];
  reference_links: ReferenceLink[];
  disclaimer: string;
};
