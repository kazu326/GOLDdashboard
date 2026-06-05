export type StatusKey = "green" | "yellow" | "red" | "unknown";

export type Indicator = {
  indicator_key: string;
  label: string;
  status: StatusKey;
  status_label: string;
  value_text: string;
  change_text: string;
  comment: string;
  reason: string;
  source_name: string;
  source_url: string;
  as_of: string;
};

export type LinkItem = {
  title: string;
  source_name: string;
  source_url: string;
  note: string;
};

export type ReferenceLink = {
  label: string;
  source_name: string;
  source_url: string;
};

export type DashboardPayload = {
  updated_at_jst: string;
  summary: {
    overall_status: StatusKey;
    overall_label: string;
    caution_level: string;
    headline: string;
    important_event_summary: string;
  };
  indicators: Indicator[];
  economic_events: LinkItem[];
  geo_news: LinkItem[];
  reference_links: ReferenceLink[];
  disclaimer: string;
};

