/**
 * Shared TypeScript types for the Aigis VS Code extension.
 *
 * These mirror the JSON output produced by `aig scan --json` which in turn
 * mirrors the `ScanResult` / `MatchedRule` dataclasses in aigis/scanner.py.
 */

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

/** A single detection rule that fired during scanning. */
export interface MatchedRule {
  /** Stable machine-readable identifier, e.g. "pi_override_en" */
  rule_id: string;
  /** Human-readable name, e.g. "Prompt Injection - Override Instructions" */
  rule_name: string;
  /**
   * Threat category.
   * e.g. "prompt_injection" | "pii_leak" | "jailbreak" | "data_exfiltration"
   */
  category: string;
  /** How much this rule contributed to the overall risk_score (0-100). */
  score_delta: number;
  /** The actual text snippet that triggered this rule. */
  matched_text: string;
  /** OWASP LLM Top 10 reference, e.g. "OWASP LLM01" */
  owasp_ref: string;
  /** Short plain-English suggestion for fixing the issue. */
  remediation_hint: string;
}

/** Top-level response from `aig scan --json`. */
export interface ScanResult {
  /** Composite risk score 0–100. */
  risk_score: number;
  /** Normalised risk level derived from risk_score. */
  risk_level: RiskLevel;
  /**
   * True when risk_score is at or above the policy block_threshold.
   * The VS Code extension treats this as an Error-severity diagnostic.
   */
  blocked: boolean;
  /** Short human-readable reason strings (one per matched rule). */
  reasons: string[];
  /** Full rule-level details for all matches. */
  matched_rules: MatchedRule[];
}

/** Metadata attached to a VS Code diagnostic for code-action context. */
export interface DiagnosticData {
  scanResult: ScanResult;
  /** Absolute path to the scanned document. */
  documentUri: string;
}

/** Status bar states the extension cycles through. */
export type StatusBarState =
  | "idle"
  | "scanning"
  | "clean"
  | "warnings"
  | "errors"
  | "unavailable";

/** Extension configuration resolved from vscode.workspace.getConfiguration. */
export interface GuardianConfig {
  pythonPath: string;
  autoScan: boolean;
  blockThreshold: RiskLevel;
  maxStringLength: number;
  scanDebounceMs: number;
  showStatusBar: boolean;
}
