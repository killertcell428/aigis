# Aigis VS Code Extension — Architecture Design

## Overview

The VS Code extension provides developer-facing tooling for the `aigis` Python library.
It surfaces prompt injection, PII leaks, jailbreak attempts, and other OWASP LLM Top 10
threats directly in the editor — without bundling Python or requiring a network connection.

---

## Design Principles

1. **Lightweight host process** — The extension contains zero Python and zero LLM inference.
   All detection logic lives in the installed `aigis` Python library and is invoked via
   `aig scan --json` subprocesses.

2. **Graceful degradation** — If Python or `aigis` is not found the extension disables
   scanning features and surfaces a single actionable error message, never a crash.

3. **No bundled Python runtime** — The extension spawns the user's configured Python binary.
   This keeps the `.vsix` small and ensures the extension always uses the same environment as
   the user's project (venv, conda, etc.).

4. **CSP-safe webview** — The sidebar panel uses an inline `nonce` Content Security Policy.
   No remote resources are loaded inside the webview.

---

## Component Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│  VS Code Extension Host (Node.js)                                    │
│                                                                      │
│  extension.ts   ──activates──►  commands / event listeners          │
│       │                                                              │
│       ├── GuardianService  ──spawn──► python -m aigis.cli scan │
│       │        │                         --json  (stdin/stdout)      │
│       │        │                     └── ScanResult JSON             │
│       │        │                                                      │
│       ├── DiagnosticProvider                                         │
│       │     ├── extract string literals (regex, per language)        │
│       │     ├── call GuardianService.scan() per literal              │
│       │     └── push vscode.Diagnostic items                         │
│       │                                                              │
│       ├── SidebarProvider  (WebviewViewProvider)                     │
│       │     └── postMessage ──► Webview HTML/JS                     │
│       │                          └── renders risk score + rules      │
│       │                                                              │
│       └── StatusBarManager                                           │
│             └── reflects scan state in the VS Code status bar        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
vscode-extension/
├── package.json            Extension manifest (commands, config, views)
├── tsconfig.json           TypeScript compiler options
├── README.md               Getting started & configuration reference
├── VSCODE_EXTENSION_DESIGN.md  (this file)
└── src/
    ├── types.ts            Shared TypeScript interfaces (ScanResult, etc.)
    ├── guardian.ts         GuardianService — subprocess management
    ├── diagnosticProvider.ts  String literal extraction + diagnostic emission
    ├── sidebarProvider.ts  WebviewViewProvider for results panel
    ├── statusBar.ts        StatusBarManager
    └── extension.ts        activate() / deactivate() entry point
```

---

## CLI Integration

### Invocation

```
python -m aigis.cli scan --json
```

Text is passed via **stdin** (not as a positional argument) to avoid shell quoting issues
on Windows. The CLI reads from `sys.stdin` when no positional `text` argument is given.

### JSON Output Schema

```jsonc
{
  "risk_score": 75,          // 0–100 composite score
  "risk_level": "HIGH",      // LOW | MEDIUM | HIGH | CRITICAL
  "blocked": true,           // true when score >= policy block_threshold
  "is_safe": false,
  "reasons": ["Prompt Injection - Override Instructions"],
  "matched_rules": [
    {
      "rule_id": "pi_override_en",
      "rule_name": "Prompt Injection - Override Instructions",
      "category": "prompt_injection",
      "score_delta": 75,
      "matched_text": "ignore previous instructions",
      "owasp_ref": "OWASP LLM01",
      "remediation_hint": "..."
    }
  ]
}
```

Exit code: `0` = safe, `1` = threat detected. Stderr is captured by the extension and
written to the "Aigis" output channel; it never surfaces as a UI error on its own.

---

## Diagnostic Severity Mapping

| Risk Level | Severity                          | VS Code indicator   |
|------------|-----------------------------------|---------------------|
| CRITICAL   | `DiagnosticSeverity.Error`        | Red squiggle        |
| HIGH       | `DiagnosticSeverity.Error`        | Red squiggle        |
| MEDIUM     | `DiagnosticSeverity.Warning`      | Yellow squiggle     |
| LOW        | Suppressed (no diagnostic raised) | —                   |

The threshold between Warning and Error is controlled by the `aiGuardian.blockThreshold`
setting (default: `HIGH`). If the user sets it to `CRITICAL`, HIGH results are shown as
warnings instead.

---

## String Literal Extraction

String literals are extracted with per-language regular expressions (not a full AST parser).
This is intentional:

- Zero compile-time dependencies on language parsers.
- Works in any language VS Code supports without additional setup.
- Handles the most common cases: triple-quoted strings (Python), template literals (JS/TS),
  f-strings, raw strings, etc.

Strings shorter than 10 characters or longer than `aiGuardian.maxStringLength` (default 4096)
are skipped. Results are cached per `document.version` to avoid redundant subprocess spawning.

---

## Auto-Scan Behaviour

When `aiGuardian.autoScan` is `true` (default):

- Scan is triggered on **document save** (immediate).
- Scan is also triggered on **document change** after a debounce delay controlled by
  `aiGuardian.scanDebounceMs` (default 1500 ms). This catches pasted content before saving.

Both triggers are no-ops for unsupported language IDs.

---

## Configuration Reference

| Setting                        | Default     | Description                                                   |
|--------------------------------|-------------|---------------------------------------------------------------|
| `aiGuardian.pythonPath`        | `"python"`  | Python executable with `aigis` installed                |
| `aiGuardian.autoScan`          | `true`      | Auto-scan on save and edit                                    |
| `aiGuardian.blockThreshold`    | `"HIGH"`    | Minimum level shown as Error (below = Warning)                |
| `aiGuardian.maxStringLength`   | `4096`      | Skip strings longer than this (chars)                         |
| `aiGuardian.scanDebounceMs`    | `1500`      | Debounce delay before auto-scan on edit (ms)                  |
| `aiGuardian.showStatusBar`     | `true`      | Show status bar item                                          |

---

## Commands

| Command ID                      | Title                          | Context menu |
|---------------------------------|--------------------------------|--------------|
| `aiGuardian.scanSelection`      | Scan with Aigis          | Yes (editor) |
| `aiGuardian.scanFile`           | Scan File with Aigis     | Yes (editor) |
| `aiGuardian.clearDiagnostics`   | Clear Aigis Diagnostics  | No           |
| `aiGuardian.showOutput`         | Show Aigis Output        | No           |
| `aiGuardian.openSettings`       | Open Aigis Settings      | No           |

---

## Sidebar Panel

The sidebar registers a `WebviewViewProvider` under the `aiGuardianSidebar` activity bar
container. It contains two views:

1. **Scan Results** (`aiGuardian.resultsView`) — WebviewView that renders the last scan
   result: risk score ring, level badge, matched rule list with OWASP refs and remediation
   hints, and the first 120 characters of the scanned text.

2. **Project Policy** (`aiGuardian.policyView`) — TreeView showing the active
   `aigis-policy.yaml` metadata (name, version, rule count, default decision).
   The policy data is fetched by running a small inline Python snippet at activation time.

---

## Error Handling

| Failure mode               | Behaviour                                                    |
|----------------------------|--------------------------------------------------------------|
| Python binary not found    | `PythonNotFoundError` → modal error + "Open Settings" action |
| `aigis` not installed | Single notification at activation; scanning silently no-ops  |
| Scan subprocess timeout    | `ScanTimeoutError` logged to output channel; scan skipped    |
| Malformed JSON from CLI    | Parse error logged; scan result discarded                    |
| Policy file missing        | Sidebar shows "Not loaded"; scanning still works             |

---

## Future Work (not in this skeleton)

- **Code Action Provider** — quick-fix to sanitize or wrap dangerous strings.
- **Hover Provider** — show OWASP reference and remediation on hover over a flagged range.
- **TreeView for rules** — replace the WebviewView policy panel with a real TreeView.
- **Custom language servers** — for semantic-aware string extraction beyond regex.
- **Remote scan mode** — call `aigis.server` HTTP API instead of spawning a process.
