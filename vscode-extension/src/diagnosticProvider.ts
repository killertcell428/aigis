/**
 * DiagnosticProvider — scans string literals in the active document and
 * raises VS Code diagnostics for detected threats.
 *
 * Design decisions:
 * - We use language-specific regexes to extract string literals rather than
 *   a full AST parser to keep the extension dependency-free and fast.
 * - Each literal is scanned independently. Results are cached per document
 *   version so re-typing the same text does not re-scan.
 * - Diagnostics use the "aiGuardian" source so users can filter them.
 * - Severity mapping:
 *     CRITICAL / HIGH  → DiagnosticSeverity.Error
 *     MEDIUM           → DiagnosticSeverity.Warning
 *     LOW              → DiagnosticSeverity.Information (suppressed by default)
 */

import * as vscode from "vscode";
import type { GuardianConfig, MatchedRule, RiskLevel, ScanResult } from "./types";
import type { GuardianService } from "./guardian";
import { PythonNotFoundError } from "./guardian";

const DIAGNOSTIC_SOURCE = "Aigis";
const DIAGNOSTIC_CODE_PREFIX = "OWASP";

/** Regex patterns to extract string literals per language family. */
const STRING_LITERAL_PATTERNS: Record<string, RegExp[]> = {
  python: [
    // Triple-quoted strings (both ''' and """)
    /"""([\s\S]*?)"""/g,
    /'''([\s\S]*?)'''/g,
    // f-strings, r-strings, b-strings with double/single quotes
    /[fFrRbBuU]{0,2}"([^"\\]|\\.)*"/g,
    /[fFrRbBuU]{0,2}'([^'\\]|\\.)*'/g,
  ],
  javascript: [
    // Template literals
    /`([\s\S]*?)`/g,
    // Regular strings
    /"([^"\\]|\\.)*"/g,
    /'([^'\\]|\\.)*'/g,
  ],
  typescript: [
    /`([\s\S]*?)`/g,
    /"([^"\\]|\\.)*"/g,
    /'([^'\\]|\\.)*'/g,
  ],
};

// JS and TSX share the same patterns
STRING_LITERAL_PATTERNS["javascriptreact"] = STRING_LITERAL_PATTERNS["javascript"];
STRING_LITERAL_PATTERNS["typescriptreact"] = STRING_LITERAL_PATTERNS["typescript"];

/** Minimum string length worth scanning (avoids noise from tiny literals). */
const MIN_SCAN_LENGTH = 10;

interface CacheEntry {
  version: number;
  diagnostics: vscode.Diagnostic[];
}

export class DiagnosticProvider implements vscode.Disposable {
  private readonly _collection: vscode.DiagnosticCollection;
  private readonly _cache = new Map<string, CacheEntry>();
  private readonly _disposables: vscode.Disposable[] = [];

  constructor(
    private readonly _guardian: GuardianService,
    private readonly _getConfig: () => GuardianConfig
  ) {
    this._collection = vscode.languages.createDiagnosticCollection("aiGuardian");
    this._disposables.push(this._collection);
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  /** Scan all extractable string literals in `document`. */
  async scanDocument(document: vscode.TextDocument): Promise<void> {
    const config = this._getConfig();
    const langId = document.languageId;
    const patterns = STRING_LITERAL_PATTERNS[langId];

    if (!patterns) {
      return; // Unsupported language — ignore silently.
    }

    const cacheKey = document.uri.toString();
    const cached = this._cache.get(cacheKey);
    if (cached && cached.version === document.version) {
      return; // Already up-to-date.
    }

    const text = document.getText();
    const literals = this._extractStringLiterals(text, patterns, config.maxStringLength);

    if (literals.length === 0) {
      this._collection.set(document.uri, []);
      this._cache.set(cacheKey, { version: document.version, diagnostics: [] });
      return;
    }

    const diagnostics: vscode.Diagnostic[] = [];

    for (const { value, startIndex } of literals) {
      let result: ScanResult;
      try {
        result = await this._guardian.scan(value, config);
      } catch (err) {
        if (err instanceof PythonNotFoundError) {
          // Surface once via notification then stop scanning.
          vscode.window
            .showErrorMessage(
              err.message,
              "Open Settings"
            )
            .then((choice) => {
              if (choice === "Open Settings") {
                vscode.commands.executeCommand(
                  "workbench.action.openSettings",
                  "aiGuardian.pythonPath"
                );
              }
            });
          return;
        }
        // Other transient errors — log and skip this literal.
        console.error("[Aigis] scan error:", err);
        continue;
      }

      if (result.risk_level === "LOW") {
        continue; // Below noise threshold — do not raise diagnostics.
      }

      const range = this._offsetToRange(document, startIndex, value);
      const diag = this._buildDiagnostic(range, result, config.blockThreshold);
      diagnostics.push(diag);
    }

    this._collection.set(document.uri, diagnostics);
    this._cache.set(cacheKey, { version: document.version, diagnostics });
  }

  /** Scan the user's current text selection and return the result. */
  async scanSelection(
    document: vscode.TextDocument,
    selection: vscode.Selection
  ): Promise<ScanResult | null> {
    const config = this._getConfig();
    const text = document.getText(selection);
    if (text.trim().length < MIN_SCAN_LENGTH) {
      return null;
    }

    try {
      return await this._guardian.scan(text, config);
    } catch (err) {
      if (err instanceof PythonNotFoundError) {
        vscode.window.showErrorMessage(err.message, "Open Settings").then((choice) => {
          if (choice === "Open Settings") {
            vscode.commands.executeCommand(
              "workbench.action.openSettings",
              "aiGuardian.pythonPath"
            );
          }
        });
      } else {
        vscode.window.showErrorMessage(`Aigis scan failed: ${err}`);
      }
      return null;
    }
  }

  /** Remove diagnostics for a specific document. */
  clearDocument(uri: vscode.Uri): void {
    this._collection.delete(uri);
    this._cache.delete(uri.toString());
  }

  /** Remove all diagnostics. */
  clearAll(): void {
    this._collection.clear();
    this._cache.clear();
  }

  /** Get current diagnostics for a document (may be stale). */
  getDiagnostics(uri: vscode.Uri): readonly vscode.Diagnostic[] {
    return this._collection.get(uri) ?? [];
  }

  dispose(): void {
    this._disposables.forEach((d) => d.dispose());
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  private _extractStringLiterals(
    text: string,
    patterns: RegExp[],
    maxLength: number
  ): Array<{ value: string; startIndex: number }> {
    const results: Array<{ value: string; startIndex: number }> = [];
    const seen = new Set<number>(); // deduplicate by start offset

    for (const pattern of patterns) {
      // Reset lastIndex since regexes are reused.
      pattern.lastIndex = 0;
      let match: RegExpExecArray | null;

      while ((match = pattern.exec(text)) !== null) {
        const fullMatch = match[0];
        const inner = match[1] ?? match[0]; // captured group or full
        const startIndex = match.index;

        if (seen.has(startIndex)) continue;
        seen.add(startIndex);

        // Skip too-short or too-long strings.
        if (inner.length < MIN_SCAN_LENGTH || fullMatch.length > maxLength) {
          continue;
        }

        results.push({ value: inner, startIndex });
      }
    }

    return results;
  }

  private _offsetToRange(
    document: vscode.TextDocument,
    startIndex: number,
    value: string
  ): vscode.Range {
    // startIndex points to the opening quote; we highlight the inner content.
    // +1 to skip the opening quote character(s).
    const quoteOffset = 1;
    const contentStart = document.positionAt(startIndex + quoteOffset);
    const contentEnd = document.positionAt(startIndex + quoteOffset + value.length);
    return new vscode.Range(contentStart, contentEnd);
  }

  private _buildDiagnostic(
    range: vscode.Range,
    result: ScanResult,
    blockThreshold: RiskLevel
  ): vscode.Diagnostic {
    const severity = this._toSeverity(result.risk_level, blockThreshold);

    // Build a concise message: lead with the top matched rule name.
    const topRule: MatchedRule | undefined = result.matched_rules[0];
    const ruleLabel = topRule ? topRule.rule_name : result.risk_level;
    const owaspRef = topRule?.owasp_ref ? ` [${topRule.owasp_ref}]` : "";
    const message =
      `Aigis: ${ruleLabel}${owaspRef} ` +
      `(score ${result.risk_score}/100, ${result.matched_rules.length} rule(s) matched)`;

    const diag = new vscode.Diagnostic(range, message, severity);
    diag.source = DIAGNOSTIC_SOURCE;

    // Attach OWASP code as a link when available.
    if (topRule?.owasp_ref) {
      diag.code = {
        value: `${DIAGNOSTIC_CODE_PREFIX}:${topRule.owasp_ref}`,
        target: vscode.Uri.parse(
          `https://owasp.org/www-project-top-10-for-large-language-model-applications/`
        ),
      };
    }

    // Embed the full result for code-action providers.
    diag.relatedInformation = result.matched_rules.map((rule) => {
      const hint = rule.remediation_hint
        ? `Fix: ${rule.remediation_hint.slice(0, 120)}`
        : `Category: ${rule.category}`;
      return new vscode.DiagnosticRelatedInformation(
        new vscode.Location(vscode.Uri.parse(""), range),
        `${rule.rule_name} — ${hint}`
      );
    });

    return diag;
  }

  private _toSeverity(
    level: RiskLevel,
    blockThreshold: RiskLevel
  ): vscode.DiagnosticSeverity {
    const order: RiskLevel[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
    const levelIdx = order.indexOf(level);
    const thresholdIdx = order.indexOf(blockThreshold);

    if (levelIdx >= thresholdIdx) {
      return vscode.DiagnosticSeverity.Error;
    }
    if (level === "MEDIUM") {
      return vscode.DiagnosticSeverity.Warning;
    }
    return vscode.DiagnosticSeverity.Information;
  }
}
