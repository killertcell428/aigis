/**
 * SidebarProvider — WebviewViewProvider that renders the Aigis results
 * panel in the activity bar sidebar.
 *
 * The webview receives structured scan results via postMessage and renders:
 *   - A risk score ring with colour coding
 *   - Risk level badge
 *   - Matched rules list with OWASP refs and remediation hints
 *   - A "last scanned" timestamp
 *
 * Design decisions:
 * - Pure HTML/CSS/JS inside the webview — no external frameworks — so the
 *   extension bundle stays small and works in restricted environments.
 * - Content Security Policy is set to block remote resources.
 * - The webview is retained (retainContextWhenHidden: true) to avoid
 *   re-rendering on every sidebar open.
 */

import * as vscode from "vscode";
import type { ScanResult } from "./types";

// Messages sent from the extension host to the webview.
type ToWebviewMessage =
  | { type: "scanResult"; payload: ScanResult; scannedText: string; timestamp: string }
  | { type: "scanning"; payload: { text: string } }
  | { type: "clear" }
  | { type: "policyStatus"; payload: PolicyStatus };

export interface PolicyStatus {
  name: string;
  version: string;
  ruleCount: number;
  defaultDecision: string;
  loaded: boolean;
}

// Messages sent from the webview back to the extension host.
type FromWebviewMessage =
  | { type: "openSettings" }
  | { type: "clearDiagnostics" }
  | { type: "requestPolicyStatus" };

export class SidebarProvider implements vscode.WebviewViewProvider, vscode.Disposable {
  public static readonly VIEW_ID = "aiGuardian.resultsView";

  private _view?: vscode.WebviewView;
  private _disposables: vscode.Disposable[] = [];

  constructor(
    private readonly _extensionUri: vscode.Uri,
    private readonly _onClearDiagnostics: () => void,
    private readonly _onOpenSettings: () => void
  ) {}

  // ---------------------------------------------------------------------------
  // WebviewViewProvider
  // ---------------------------------------------------------------------------

  resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ): void {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri],
    };

    webviewView.webview.html = this._getHtml(webviewView.webview);

    // Handle messages from the webview.
    this._disposables.push(
      webviewView.webview.onDidReceiveMessage((msg: FromWebviewMessage) => {
        switch (msg.type) {
          case "openSettings":
            this._onOpenSettings();
            break;
          case "clearDiagnostics":
            this._onClearDiagnostics();
            break;
          case "requestPolicyStatus":
            // Handled externally; the extension will call postPolicyStatus().
            vscode.commands.executeCommand("aiGuardian.refreshPolicyStatus");
            break;
        }
      })
    );
  }

  // ---------------------------------------------------------------------------
  // Public messaging API (called by extension.ts)
  // ---------------------------------------------------------------------------

  postScanResult(result: ScanResult, scannedText: string): void {
    this._post({
      type: "scanResult",
      payload: result,
      scannedText: scannedText.slice(0, 120) + (scannedText.length > 120 ? "…" : ""),
      timestamp: new Date().toLocaleTimeString(),
    });
  }

  postScanning(text: string): void {
    this._post({ type: "scanning", payload: { text: text.slice(0, 60) } });
  }

  postClear(): void {
    this._post({ type: "clear" });
  }

  postPolicyStatus(status: PolicyStatus): void {
    this._post({ type: "policyStatus", payload: status });
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  private _post(msg: ToWebviewMessage): void {
    this._view?.webview.postMessage(msg);
  }

  private _getHtml(webview: vscode.Webview): string {
    const nonce = this._nonce();
    const csp = [
      `default-src 'none'`,
      `style-src 'nonce-${nonce}'`,
      `script-src 'nonce-${nonce}'`,
    ].join("; ");

    return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="${csp}" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Aigis</title>
  <style nonce="${nonce}">
    :root {
      --color-low:      var(--vscode-charts-green, #4ec9b0);
      --color-medium:   var(--vscode-charts-yellow, #d7ba7d);
      --color-high:     var(--vscode-charts-orange, #ce9178);
      --color-critical: var(--vscode-charts-red, #f44747);
      --radius: 4px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      color: var(--vscode-foreground);
      background: var(--vscode-sideBar-background);
      padding: 8px;
    }
    h2 { font-size: 1em; margin-bottom: 8px; opacity: 0.7; }
    .card {
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: var(--radius);
      padding: 10px 12px;
      margin-bottom: 8px;
    }
    .score-row {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 6px;
    }
    .score-ring {
      width: 48px; height: 48px; flex-shrink: 0;
    }
    .score-ring circle {
      fill: none;
      stroke-width: 5;
      stroke-linecap: round;
    }
    .ring-bg  { stroke: var(--vscode-panel-border); }
    .ring-val { transition: stroke-dashoffset 0.4s ease; transform-origin: center; transform: rotate(-90deg); }
    .score-num {
      font-size: 1.6em;
      font-weight: 700;
      line-height: 1;
    }
    .score-meta { opacity: 0.8; font-size: 0.85em; }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 0.8em;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #000;
    }
    .badge-LOW      { background: var(--color-low); }
    .badge-MEDIUM   { background: var(--color-medium); }
    .badge-HIGH     { background: var(--color-high); }
    .badge-CRITICAL { background: var(--color-critical); color: #fff; }
    .rule-list { list-style: none; padding: 0; margin-top: 6px; }
    .rule-item {
      padding: 6px 0;
      border-top: 1px solid var(--vscode-panel-border);
      font-size: 0.9em;
    }
    .rule-name  { font-weight: 600; }
    .rule-owasp {
      display: inline-block;
      margin-left: 6px;
      font-size: 0.8em;
      opacity: 0.7;
      font-style: italic;
    }
    .rule-hint  { margin-top: 3px; opacity: 0.75; font-size: 0.85em; }
    .rule-matched {
      margin-top: 3px;
      font-family: var(--vscode-editor-font-family, monospace);
      font-size: 0.82em;
      background: var(--vscode-textCodeBlock-background);
      padding: 2px 4px;
      border-radius: 2px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .status-row {
      display: flex; justify-content: space-between;
      align-items: center; margin-top: 4px;
    }
    .timestamp { font-size: 0.78em; opacity: 0.55; }
    .btn {
      font-size: 0.78em;
      padding: 2px 8px;
      border-radius: var(--radius);
      border: 1px solid var(--vscode-button-border, transparent);
      background: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
      cursor: pointer;
    }
    .btn:hover { background: var(--vscode-button-secondaryHoverBackground); }
    .empty-state { text-align: center; opacity: 0.5; padding: 20px 0; font-size: 0.9em; }
    .scanning-state { text-align: center; opacity: 0.7; padding: 12px 0; }
    .spinner {
      display: inline-block;
      width: 14px; height: 14px;
      border: 2px solid var(--vscode-panel-border);
      border-top-color: var(--vscode-focusBorder);
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      vertical-align: middle;
      margin-right: 6px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .policy-card { font-size: 0.85em; }
    .policy-row { display: flex; justify-content: space-between; padding: 2px 0; }
    .policy-label { opacity: 0.65; }
  </style>
</head>
<body>
  <div id="root">
    <div class="empty-state" id="empty">
      No scan results yet.<br/>
      Right-click text → <em>Scan with Aigis</em>
    </div>
  </div>

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const root = document.getElementById('root');

    // ---------------------------------------------------------------------------
    // State
    // ---------------------------------------------------------------------------
    let state = { lastResult: null, policy: null };

    // ---------------------------------------------------------------------------
    // Render helpers
    // ---------------------------------------------------------------------------

    function levelColor(level) {
      return { LOW: '#4ec9b0', MEDIUM: '#d7ba7d', HIGH: '#ce9178', CRITICAL: '#f44747' }[level] || '#888';
    }

    function renderScoreRing(score, level) {
      const r = 18;
      const circ = 2 * Math.PI * r;
      const dash = (score / 100) * circ;
      const color = levelColor(level);
      return \`<svg class="score-ring" viewBox="0 0 48 48">
        <circle class="ring-bg" cx="24" cy="24" r="\${r}" />
        <circle class="ring-val" cx="24" cy="24" r="\${r}"
          stroke="\${color}"
          stroke-dasharray="\${circ}"
          stroke-dashoffset="\${circ - dash}" />
        <text x="24" y="28" text-anchor="middle"
          font-size="13" fill="currentColor" font-weight="700">\${score}</text>
      </svg>\`;
    }

    function renderResult(result, scannedText, timestamp) {
      const topRule = result.matched_rules[0];
      const rulesHtml = result.matched_rules.map(r => \`
        <li class="rule-item">
          <span class="rule-name">\${esc(r.rule_name)}</span>
          \${r.owasp_ref ? \`<span class="rule-owasp">\${esc(r.owasp_ref)}</span>\` : ''}
          \${r.remediation_hint ? \`<div class="rule-hint">Fix: \${esc(r.remediation_hint.slice(0,140))}</div>\` : ''}
          \${r.matched_text ? \`<div class="rule-matched">\${esc(r.matched_text.slice(0,60))}</div>\` : ''}
        </li>
      \`).join('');

      return \`
        <div class="card">
          <div class="score-row">
            \${renderScoreRing(result.risk_score, result.risk_level)}
            <div>
              <div class="score-num">\${result.risk_score}<span style="font-size:0.5em;font-weight:400">/100</span></div>
              <span class="badge badge-\${result.risk_level}">\${result.risk_level}</span>
              \${result.blocked ? '<span style="color:var(--color-critical);margin-left:6px;font-size:0.8em">BLOCKED</span>' : ''}
            </div>
          </div>
          \${result.matched_rules.length > 0 ? \`
            <div style="margin-top:4px;font-size:0.85em;opacity:0.8">
              \${result.matched_rules.length} rule(s) matched
            </div>
            <ul class="rule-list">\${rulesHtml}</ul>
          \` : '<div style="margin-top:4px;font-size:0.85em;opacity:0.7">No threats detected.</div>'}
          <div class="status-row">
            <span class="timestamp">Scanned \${esc(timestamp)}</span>
            <button class="btn" onclick="sendMsg('clearDiagnostics')">Clear</button>
          </div>
        </div>
        \${scannedText ? \`
          <div class="card">
            <div style="font-size:0.8em;opacity:0.6;margin-bottom:4px">Scanned text</div>
            <div style="font-family:var(--vscode-editor-font-family,monospace);font-size:0.82em;word-break:break-all">
              \${esc(scannedText)}
            </div>
          </div>
        \` : ''}
      \`;
    }

    function renderPolicy(policy) {
      if (!policy || !policy.loaded) return '';
      return \`
        <h2>Project Policy</h2>
        <div class="card policy-card">
          <div class="policy-row"><span class="policy-label">Name</span><span>\${esc(policy.name)}</span></div>
          <div class="policy-row"><span class="policy-label">Version</span><span>\${esc(policy.version)}</span></div>
          <div class="policy-row"><span class="policy-label">Rules</span><span>\${policy.ruleCount}</span></div>
          <div class="policy-row"><span class="policy-label">Default</span><span>\${esc(policy.defaultDecision)}</span></div>
        </div>
      \`;
    }

    function render() {
      if (!state.lastResult) {
        root.innerHTML = \`<div class="empty-state" id="empty">
          No scan results yet.<br/>
          Right-click text → <em>Scan with Aigis</em>
        </div>\${renderPolicy(state.policy)}\`;
        return;
      }
      const { result, scannedText, timestamp } = state.lastResult;
      root.innerHTML = \`
        <h2>Scan Results</h2>
        \${renderResult(result, scannedText, timestamp)}
        \${renderPolicy(state.policy)}
        <div style="margin-top:8px">
          <button class="btn" onclick="sendMsg('openSettings')">Settings</button>
        </div>
      \`;
    }

    // ---------------------------------------------------------------------------
    // Utilities
    // ---------------------------------------------------------------------------

    function esc(str) {
      if (typeof str !== 'string') return '';
      return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    function sendMsg(type, payload) {
      vscode.postMessage({ type, payload });
    }

    // ---------------------------------------------------------------------------
    // Message handling
    // ---------------------------------------------------------------------------

    window.addEventListener('message', event => {
      const msg = event.data;
      switch (msg.type) {
        case 'scanResult':
          state.lastResult = { result: msg.payload, scannedText: msg.scannedText, timestamp: msg.timestamp };
          render();
          break;
        case 'scanning':
          root.innerHTML = \`<div class="scanning-state">
            <span class="spinner"></span>Scanning…
          </div>\`;
          break;
        case 'clear':
          state.lastResult = null;
          render();
          break;
        case 'policyStatus':
          state.policy = msg.payload;
          render();
          break;
      }
    });

    // Initial render.
    render();
  </script>
</body>
</html>`;
  }

  private _nonce(): string {
    let text = "";
    const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for (let i = 0; i < 32; i++) {
      text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
  }

  dispose(): void {
    this._disposables.forEach((d) => d.dispose());
  }
}
