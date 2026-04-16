/**
 * API client for Aigis backend.
 * Uses the Next.js rewrite to proxy requests to the backend.
 */

const BASE = "/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("aigis_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail ?? `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface RequestDetail {
  model: string | null;
  messages: Array<{ role: string; content: string }> | null;
  input_risk_score: number;
  input_risk_level: string;
  input_matched_rules: Array<{
    rule_id: string;
    rule_name: string;
    category: string;
    score_delta: number;
    matched_text: string;
  }>;
  client_ip: string | null;
}

export interface ReviewItem {
  id: string;
  request_id: string;
  status: string;
  sla_deadline: string;
  decision: string | null;
  reviewer_note: string | null;
  created_at: string;
  reviewed_at: string | null;
  request_detail?: RequestDetail | null;
}

export interface Policy {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  auto_allow_threshold: number;
  auto_block_threshold: number;
  review_sla_minutes: number;
  sla_fallback: string;
  custom_rules: CustomRule[];
}

export interface CustomRule {
  id: string;
  name: string;
  pattern: string;
  score_delta: number;
  enabled: boolean;
}

export interface AuditLog {
  id: string;
  tenant_id: string;
  request_id: string | null;
  actor_id: string | null;
  event_type: string;
  severity: string;
  summary: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ProxyTestResult {
  response_body: Record<string, unknown>;
  status_code: number;
}

export interface MatchedRule {
  rule_id: string;
  rule_name: string;
  category: string;
  score_delta: number;
  matched_text: string;
}

// ---------------------------------------------------------------------------
// Proxy (Playground)
// ---------------------------------------------------------------------------
export const proxyApi = {
  async test(prompt: string, model = "gpt-4o"): Promise<{ body: Record<string, unknown>; status: number }> {
    const token = getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${BASE}/proxy/test`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        model,
        messages: [{ role: "user", content: prompt }],
      }),
    });

    const body = await res.json();
    return { body, status: res.status };
  },
};

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export const authApi = {
  async login(email: string, password: string): Promise<TokenResponse> {
    const data = await request<TokenResponse>("/admin/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem("aigis_token", data.access_token);
    return data;
  },

  logout() {
    localStorage.removeItem("aigis_token");
  },

  async me() {
    return request("/admin/auth/me");
  },
};

// ---------------------------------------------------------------------------
// Review Queue
// ---------------------------------------------------------------------------
export const reviewApi = {
  list(status = "pending"): Promise<ReviewItem[]> {
    return request(`/review/queue?status=${status}`);
  },

  get(id: string): Promise<ReviewItem> {
    return request(`/review/queue/${id}`);
  },

  decide(
    id: string,
    decision: "approve" | "reject" | "escalate",
    note?: string
  ): Promise<ReviewItem> {
    return request(`/review/queue/${id}/decide`, {
      method: "POST",
      body: JSON.stringify({ decision, note }),
    });
  },
};

// ---------------------------------------------------------------------------
// Policies
// ---------------------------------------------------------------------------
export const policiesApi = {
  list(): Promise<Policy[]> {
    return request("/policies");
  },

  get(id: string): Promise<Policy> {
    return request(`/policies/${id}`);
  },

  create(data: Partial<Policy>): Promise<Policy> {
    return request("/policies", { method: "POST", body: JSON.stringify(data) });
  },

  update(id: string, data: Partial<Policy>): Promise<Policy> {
    return request(`/policies/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  delete(id: string): Promise<void> {
    return request(`/policies/${id}`, { method: "DELETE" });
  },
};

// ---------------------------------------------------------------------------
// Billing
// ---------------------------------------------------------------------------
export interface SubscriptionStatus {
  plan: string;
  status: string;
  trial_ends_at: string | null;
  current_period_end: string | null;
}

export interface UsageStats {
  plan: string;
  monthly_requests_used: number;
  monthly_requests_limit: number | null;
  team_size: number;
  team_limit: number | null;
  retention_days: number | null;
}

export interface TeamMember {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export const billingApi = {
  getStatus(): Promise<SubscriptionStatus> {
    return request("/billing/status");
  },

  createCheckout(plan: string, successUrl: string, cancelUrl: string): Promise<{ url: string }> {
    return request("/billing/checkout", {
      method: "POST",
      body: JSON.stringify({ plan, success_url: successUrl, cancel_url: cancelUrl }),
    });
  },

  createPortal(): Promise<{ url: string }> {
    return request("/billing/portal", { method: "POST" });
  },

  getUsage(): Promise<UsageStats> {
    return request("/billing/usage");
  },
};

// ---------------------------------------------------------------------------
// Team Management
// ---------------------------------------------------------------------------
export const teamApi = {
  list(): Promise<TeamMember[]> {
    return request("/admin/users");
  },

  invite(email: string, fullName: string, role = "reviewer", password: string): Promise<TeamMember> {
    return request("/admin/users", {
      method: "POST",
      body: JSON.stringify({ email, full_name: fullName, password, role }),
    });
  },
};

// ---------------------------------------------------------------------------
// Monitor (Security Monitoring)
// ---------------------------------------------------------------------------
export interface MonitorSnapshot {
  timestamp: string;
  period_hours: number;
  total_scans: number;
  total_blocked: number;
  total_review: number;
  total_allowed: number;
  detection_rate: number;
  asr: number;
  risk_distribution: Record<string, number>;
  category_counts: Record<string, number>;
  category_blocked: Record<string, number>;
  detection_by_layer: Record<string, number>;
}

export interface AsrTrendPoint {
  date: string;
  total_attacks: number;
  blocked: number;
  bypassed: number;
  asr: number;
}

export interface OwaspEntry {
  name: string;
  detections: number;
  blocked: number;
  categories: string[];
  covered: boolean;
  protection_level: string;
  unique_features: string[];
}

export interface PipelineData {
  layers: Record<string, { name: string; description: string; order: number }>;
  unique_capabilities: Array<{
    name: string;
    status: string;
    differentiator: string;
    scan_only: string;
  }>;
}

export const monitorApi = {
  snapshot(hours = 24): Promise<MonitorSnapshot> {
    return request(`/monitor/snapshot?hours=${hours}`);
  },

  asrTrend(days = 30): Promise<AsrTrendPoint[]> {
    return request(`/monitor/asr-trend?days=${days}`);
  },

  owaspScorecard(days = 30): Promise<Record<string, OwaspEntry>> {
    return request(`/monitor/owasp-scorecard?days=${days}`);
  },

  heatmap(days = 30): Promise<Record<string, Record<string, number>>> {
    return request(`/monitor/heatmap?days=${days}`);
  },

  pipeline(): Promise<PipelineData> {
    return request("/monitor/pipeline");
  },
};

// ---------------------------------------------------------------------------
// Weekly Report
// ---------------------------------------------------------------------------
export interface WeeklyReport {
  generated_at: string;
  period_start: string;
  period_end: string;
  total_scans: number;
  total_blocked: number;
  total_review: number;
  total_allowed: number;
  safety_rate: number;
  risk_distribution: Record<string, number>;
  category_counts: Record<string, number>;
  detection_by_layer: Record<string, number>;
  owasp_coverage: Record<string, {
    name: string;
    detections: number;
    blocked: number;
    covered: boolean;
    protection_level: string;
  }>;
  prev_total_scans: number;
  prev_total_blocked: number;
  prev_safety_rate: number;
  trend_scans_pct: number;
  trend_blocked_pct: number;
  trend_safety_pct: number;
  category_trends: Record<string, {
    this_week: number;
    prev_week: number;
    change_pct: number;
    direction: string;
  }>;
  recommendations: Array<{ severity: string; message: string }>;
}

export const reportsApi = {
  weekly(): Promise<WeeklyReport> {
    return request("/reports/weekly");
  },
};

// ---------------------------------------------------------------------------
// Incidents
// ---------------------------------------------------------------------------
export interface IncidentTimeline {
  timestamp: string;
  action: string;
  actor: string;
  detail: string;
}

export interface IncidentItem {
  id: string;
  incident_number: string;
  severity: string;
  status: string;
  title: string;
  request_id: string | null;
  risk_score: number;
  matched_rules: Array<{ rule_id: string; rule_name: string; category: string; score_delta: number }>;
  detection_layers: string[];
  source_ip: string | null;
  trigger_category: string | null;
  assigned_to: string | null;
  resolution: string | null;
  resolution_note: string | null;
  sla_deadline: string | null;
  sla_met: boolean | null;
  timeline: IncidentTimeline[];
  related_event_ids: string[];
  detected_at: string;
  responded_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
}

export interface IncidentStats {
  total: number;
  open: number;
  investigating: number;
  mitigated: number;
  closed: number;
}

export const incidentsApi = {
  list(params?: { status?: string; severity?: string; limit?: number }): Promise<IncidentItem[]> {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.severity) qs.set("severity", params.severity);
    if (params?.limit) qs.set("limit", String(params.limit));
    return request(`/incidents?${qs.toString()}`);
  },
  stats(): Promise<IncidentStats> {
    return request("/incidents/stats");
  },
  get(id: string): Promise<IncidentItem> {
    return request(`/incidents/${id}`);
  },
  updateStatus(id: string, status: string, note?: string): Promise<IncidentItem> {
    return request(`/incidents/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ status, note }),
    });
  },
  resolve(id: string, resolution: string, note?: string): Promise<IncidentItem> {
    return request(`/incidents/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ resolution, note }),
    });
  },
  addNote(id: string, note: string): Promise<IncidentItem> {
    return request(`/incidents/${id}/note`, {
      method: "POST",
      body: JSON.stringify({ note }),
    });
  },
};

// ---------------------------------------------------------------------------
// Audit Logs
// ---------------------------------------------------------------------------
export const auditApi = {
  list(params?: {
    event_type?: string;
    severity?: string;
    limit?: number;
    offset?: number;
  }): Promise<AuditLog[]> {
    const qs = new URLSearchParams();
    if (params?.event_type) qs.set("event_type", params.event_type);
    if (params?.severity) qs.set("severity", params.severity);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    return request(`/audit/logs?${qs.toString()}`);
  },
};
