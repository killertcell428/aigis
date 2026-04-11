# Aigis — VS Code Extension

Detect prompt injection, PII leaks, jailbreaks, and OWASP LLM Top 10 threats directly
in your editor while you write Python, JavaScript, and TypeScript code.

## Features

- **Right-click → Scan with Aigis** — instantly scan any selected text
- **Scan File** — scan all string literals in the active file at once
- **Inline diagnostics** — red/yellow squiggles on flagged string literals with OWASP refs
- **Sidebar panel** — risk score ring, matched rule list, and remediation hints
- **Status bar** — shows live scan state (clean / N warnings / N issues)
- **Auto-scan on save** — optional, configurable debounce delay

## Requirements

- VS Code 1.85+
- Python 3.10+ with `aigis` installed:

```bash
pip install aigis
```

The extension spawns your configured Python binary and calls `aig scan --json`.
No Python runtime is bundled in the extension.

## Quick Start

1. Install the extension from the VS Code Marketplace.
2. Open a Python/JS/TS file.
3. Select a string that might contain a prompt, then right-click →
   **Scan with Aigis**.
4. View results in the **Aigis** sidebar panel.

For project-wide governance, run `aig init` in your project root to create a policy file.

## Configuration

| Setting                      | Default    | Description                                           |
|------------------------------|------------|-------------------------------------------------------|
| `aiGuardian.pythonPath`      | `"python"` | Path to Python with aigis installed             |
| `aiGuardian.autoScan`        | `true`     | Auto-scan string literals on save/edit                |
| `aiGuardian.blockThreshold`  | `"HIGH"`   | Minimum risk level shown as Error (others = Warning)  |
| `aiGuardian.maxStringLength` | `4096`     | Skip strings longer than this to avoid slowdowns      |
| `aiGuardian.scanDebounceMs`  | `1500`     | Debounce (ms) before scanning after an edit           |
| `aiGuardian.showStatusBar`   | `true`     | Show Aigis item in the status bar               |

### Using a virtual environment

```json
// .vscode/settings.json
{
  "aiGuardian.pythonPath": "${workspaceFolder}/.venv/Scripts/python.exe"
}
```

On macOS/Linux:
```json
{
  "aiGuardian.pythonPath": "${workspaceFolder}/.venv/bin/python"
}
```

## Commands

| Command                         | Keyboard shortcut | Description                        |
|---------------------------------|-------------------|------------------------------------|
| Aigis: Scan with Aigis  | —             | Scan selected text                 |
| Aigis: Scan File          | —                 | Scan all string literals in file   |
| Aigis: Clear Diagnostics  | —                 | Remove all Aigis squiggles   |
| Aigis: Show Output        | —                 | Open the Aigis output channel|

## Threat Categories

| Category          | OWASP Ref   | Example                                   |
|-------------------|-------------|-------------------------------------------|
| Prompt Injection  | LLM01       | "ignore previous instructions"            |
| Jailbreak         | LLM01       | "DAN mode", "act as DAN"                  |
| PII Leak          | LLM02/LLM06 | Credit card numbers, SSN, JP My Number    |
| Data Exfiltration | LLM02       | Requests to send data to external URLs    |
| Indirect Injection| LLM01       | Injection payloads in RAG context         |

## Development

```bash
cd vscode-extension
npm install
npm run compile
# Press F5 in VS Code to launch Extension Development Host
```

To package:
```bash
npm run package    # produces aigis-*.vsix
```

## License

MIT — see [LICENSE](../LICENSE)
