/**
 * Aigis VS Code Extension — main entry point.
 *
 * Lifecycle:
 *   activate()   → registers commands, providers, listeners
 *   deactivate() → disposes all resources
 *
 * Key collaborators:
 *   GuardianService      — spawns `aig scan --json` subprocesses
 *   DiagnosticProvider   — extracts string literals, raises diagnostics
 *   SidebarProvider      — WebviewViewProvider for the results panel
 *   StatusBarManager     — reflects current scan state in the status bar
 */

import * as vscode from "vscode";
import { GuardianService, PythonNotFoundError } from "./guardian";
import { DiagnosticProvider } from "./diagnosticProvider";
import { SidebarProvider, PolicyStatus } from "./sidebarProvider";
import { StatusBarManager } from "./statusBar";
import type { GuardianConfig, RiskLevel, ScanResult } from "./types";

// Languages the extension activates on and auto-scans.
const SUPPORTED_LANGUAGES = new Set([
  "python",
  "javascript",
  "typescript",
  "javascriptreact",
  "typescriptreact",
]);

export function activate(context: vscode.ExtensionContext): void {
  const outputChannel = vscode.window.createOutputChannel("Aigis");
  outputChannel.appendLine("Aigis extension activated.");

  // ---------------------------------------------------------------------------
  // Core services
  // ---------------------------------------------------------------------------

  const guardian = new GuardianService(outputChannel);
  const statusBar = new StatusBarManager();
  const config = () => resolveConfig();

  const diagnosticProvider = new DiagnosticProvider(guardian, config);

  const sidebarProvider = new SidebarProvider(
    context.extensionUri,
    () => {
      diagnosticProvider.clearAll();
      statusBar.setState("idle");
    },
    () => {
      vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "aiGuardian.pythonPath"
      );
    }
  );

  // ---------------------------------------------------------------------------
  // Status bar
  // ---------------------------------------------------------------------------

  const cfg = resolveConfig();
  if (cfg.showStatusBar) {
    statusBar.show();
  }

  // ---------------------------------------------------------------------------
  // Register sidebar
  // ---------------------------------------------------------------------------

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      SidebarProvider.VIEW_ID,
      sidebarProvider,
      { webviewOptions: { retainContextWhenHidden: true } }
    )
  );

  // ---------------------------------------------------------------------------
  // Commands
  // ---------------------------------------------------------------------------

  // Command: scan the current text selection.
  const scanSelectionCmd = vscode.commands.registerCommand(
    "aiGuardian.scanSelection",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("Aigis: no active editor.");
        return;
      }
      if (editor.selection.isEmpty) {
        vscode.window.showWarningMessage(
          "Aigis: select some text first, then run Scan with Aigis."
        );
        return;
      }

      const text = editor.document.getText(editor.selection);
      statusBar.setState("scanning");
      sidebarProvider.postScanning(text);

      try {
        const result = await diagnosticProvider.scanSelection(
          editor.document,
          editor.selection
        );

        if (!result) {
          statusBar.setState("idle");
          return;
        }

        sidebarProvider.postScanResult(result, text);
        // Also push a one-time diagnostic on the selection range.
        await applySelectionDiagnostic(editor, result);
        statusBar.updateFromDiagnostics(
          diagnosticProvider.getDiagnostics(editor.document.uri)
        );

        // Show a non-intrusive notification for HIGH/CRITICAL.
        if (result.risk_level === "HIGH" || result.risk_level === "CRITICAL") {
          const msg =
            `Aigis: ${result.risk_level} threat detected ` +
            `(score ${result.risk_score}) — ${result.reasons[0] ?? "see sidebar"}`;
          vscode.window.showWarningMessage(msg);
        } else if (result.risk_level === "MEDIUM") {
          outputChannel.appendLine(
            `MEDIUM risk in selection: ${result.reasons.join(", ")}`
          );
        }
      } catch (err) {
        statusBar.setState("unavailable");
        if (err instanceof PythonNotFoundError) {
          vscode.window.showErrorMessage(err.message, "Open Settings").then((c) => {
            if (c === "Open Settings") {
              vscode.commands.executeCommand(
                "workbench.action.openSettings",
                "aiGuardian.pythonPath"
              );
            }
          });
        } else {
          vscode.window.showErrorMessage(`Aigis error: ${err}`);
          outputChannel.appendLine(`[ERROR] scanSelection: ${err}`);
        }
      }
    }
  );

  // Command: scan all string literals in the active file.
  const scanFileCmd = vscode.commands.registerCommand(
    "aiGuardian.scanFile",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("Aigis: no active editor.");
        return;
      }
      if (!SUPPORTED_LANGUAGES.has(editor.document.languageId)) {
        vscode.window.showWarningMessage(
          `Aigis: file type "${editor.document.languageId}" is not supported.`
        );
        return;
      }

      statusBar.setState("scanning");
      outputChannel.appendLine(`Scanning file: ${editor.document.fileName}`);

      await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: "Aigis: scanning file…",
          cancellable: false,
        },
        async () => {
          await diagnosticProvider.scanDocument(editor.document);
        }
      );

      const diags = diagnosticProvider.getDiagnostics(editor.document.uri);
      statusBar.updateFromDiagnostics(diags);

      const errors = diags.filter(
        (d) => d.severity === vscode.DiagnosticSeverity.Error
      ).length;
      const warnings = diags.filter(
        (d) => d.severity === vscode.DiagnosticSeverity.Warning
      ).length;

      if (errors + warnings === 0) {
        vscode.window.showInformationMessage(
          "Aigis: no threats detected in this file."
        );
      } else {
        vscode.window.showWarningMessage(
          `Aigis: found ${errors} error(s) and ${warnings} warning(s). ` +
            `See Problems panel for details.`
        );
      }
    }
  );

  // Command: clear all Aigis diagnostics.
  const clearCmd = vscode.commands.registerCommand(
    "aiGuardian.clearDiagnostics",
    () => {
      diagnosticProvider.clearAll();
      statusBar.setState("idle");
      sidebarProvider.postClear();
      outputChannel.appendLine("Diagnostics cleared.");
    }
  );

  // Command: show output channel.
  const showOutputCmd = vscode.commands.registerCommand(
    "aiGuardian.showOutput",
    () => {
      outputChannel.show(true);
    }
  );

  // Command: open settings.
  const openSettingsCmd = vscode.commands.registerCommand(
    "aiGuardian.openSettings",
    () => {
      vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "@ext:aigis.vscode-aigis"
      );
    }
  );

  // Internal command triggered by the webview to refresh policy status.
  const refreshPolicyCmd = vscode.commands.registerCommand(
    "aiGuardian.refreshPolicyStatus",
    async () => {
      const status = await loadPolicyStatus(resolveConfig().pythonPath, outputChannel);
      sidebarProvider.postPolicyStatus(status);
    }
  );

  // ---------------------------------------------------------------------------
  // Auto-scan on save
  // ---------------------------------------------------------------------------

  const onSave = vscode.workspace.onDidSaveTextDocument(async (doc) => {
    const cfg = resolveConfig();
    if (!cfg.autoScan) return;
    if (!SUPPORTED_LANGUAGES.has(doc.languageId)) return;

    statusBar.setState("scanning");
    await diagnosticProvider.scanDocument(doc);
    const diags = diagnosticProvider.getDiagnostics(doc.uri);

    if (vscode.window.activeTextEditor?.document.uri.toString() === doc.uri.toString()) {
      statusBar.updateFromDiagnostics(diags);
    }
  });

  // Auto-scan debounced on change (only if autoScan is on).
  let debounceTimer: ReturnType<typeof setTimeout> | undefined;
  const onChange = vscode.workspace.onDidChangeTextDocument((e) => {
    const cfg = resolveConfig();
    if (!cfg.autoScan) return;
    if (!SUPPORTED_LANGUAGES.has(e.document.languageId)) return;
    if (e.contentChanges.length === 0) return;

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      statusBar.setState("scanning");
      await diagnosticProvider.scanDocument(e.document);
      if (
        vscode.window.activeTextEditor?.document.uri.toString() ===
        e.document.uri.toString()
      ) {
        statusBar.updateFromDiagnostics(
          diagnosticProvider.getDiagnostics(e.document.uri)
        );
      }
    }, cfg.scanDebounceMs);
  });

  // Clear diagnostics when a document is closed.
  const onClose = vscode.workspace.onDidCloseTextDocument((doc) => {
    diagnosticProvider.clearDocument(doc.uri);
  });

  // Update status bar when the active editor changes.
  const onEditorChange = vscode.window.onDidChangeActiveTextEditor((editor) => {
    if (!editor) {
      statusBar.setState("idle");
      return;
    }
    const diags = diagnosticProvider.getDiagnostics(editor.document.uri);
    if (diags.length === 0) {
      statusBar.setState("idle");
    } else {
      statusBar.updateFromDiagnostics(diags);
    }
  });

  // React to configuration changes.
  const onConfigChange = vscode.workspace.onDidChangeConfiguration((e) => {
    if (e.affectsConfiguration("aiGuardian.showStatusBar")) {
      const cfg = resolveConfig();
      cfg.showStatusBar ? statusBar.show() : statusBar.hide();
    }
  });

  // ---------------------------------------------------------------------------
  // Startup: verify installation and load policy
  // ---------------------------------------------------------------------------

  const cfg2 = resolveConfig();
  guardian.checkInstallation(cfg2.pythonPath).then((status) => {
    outputChannel.appendLine(`Installation check: ${status}`);
    if (status.includes("not installed") || status.includes("not found")) {
      statusBar.setState("unavailable");
      vscode.window
        .showErrorMessage(
          `Aigis: ${status}`,
          "Open Settings",
          "Dismiss"
        )
        .then((choice) => {
          if (choice === "Open Settings") {
            vscode.commands.executeCommand(
              "workbench.action.openSettings",
              "aiGuardian.pythonPath"
            );
          }
        });
    }
  });

  loadPolicyStatus(cfg2.pythonPath, outputChannel).then((status) => {
    sidebarProvider.postPolicyStatus(status);
  });

  // ---------------------------------------------------------------------------
  // Register all disposables
  // ---------------------------------------------------------------------------

  context.subscriptions.push(
    outputChannel,
    guardian,
    diagnosticProvider,
    sidebarProvider,
    statusBar,
    scanSelectionCmd,
    scanFileCmd,
    clearCmd,
    showOutputCmd,
    openSettingsCmd,
    refreshPolicyCmd,
    onSave,
    onChange,
    onClose,
    onEditorChange,
    onConfigChange
  );
}

export function deactivate(): void {
  // Subscriptions are disposed automatically by VS Code via context.subscriptions.
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function resolveConfig(): GuardianConfig {
  const ws = vscode.workspace.getConfiguration("aiGuardian");
  return {
    pythonPath: ws.get<string>("pythonPath", "python"),
    autoScan: ws.get<boolean>("autoScan", true),
    blockThreshold: ws.get<RiskLevel>("blockThreshold", "HIGH"),
    maxStringLength: ws.get<number>("maxStringLength", 4096),
    scanDebounceMs: ws.get<number>("scanDebounceMs", 1500),
    showStatusBar: ws.get<boolean>("showStatusBar", true),
  };
}

async function applySelectionDiagnostic(
  editor: vscode.TextEditor,
  result: ScanResult
): Promise<void> {
  // We delegate back to the diagnostic provider to build the diagnostic,
  // but for a selection scan we just forward the full document scan to
  // cover the whole document including any newly highlighted range.
  // For an immediate single-range highlight, we create a lightweight one here.
  if (result.risk_level === "LOW") return;

  const diags = vscode.languages.createDiagnosticCollection("aiGuardian-selection");
  // The selection diagnostic is ephemeral — it will be replaced on the next
  // full document scan or cleared explicitly.
  const severity =
    result.risk_level === "HIGH" || result.risk_level === "CRITICAL"
      ? vscode.DiagnosticSeverity.Error
      : vscode.DiagnosticSeverity.Warning;

  const message =
    `Aigis: ${result.risk_level} — ` +
    (result.reasons[0] ?? "threat detected") +
    ` (score ${result.risk_score})`;

  const diag = new vscode.Diagnostic(editor.selection, message, severity);
  diag.source = "Aigis";
  diags.set(editor.document.uri, [diag]);

  // Auto-clear after 30 s so it doesn't persist after the user edits.
  setTimeout(() => diags.dispose(), 30_000);
}

async function loadPolicyStatus(
  pythonPath: string,
  outputChannel: vscode.OutputChannel
): Promise<PolicyStatus> {
  return new Promise((resolve) => {
    const cp = require("child_process") as typeof import("child_process");
    const script = [
      "import json, sys",
      "try:",
      "    from aigis.policy import load_policy",
      "    from pathlib import Path",
      "    p = load_policy('aigis-policy.yaml')",
      "    print(json.dumps({'name': p.name, 'version': str(p.version), ",
      "        'ruleCount': len(p.rules), 'defaultDecision': p.default_decision, 'loaded': True}))",
      "except Exception as e:",
      "    print(json.dumps({'name': 'Not loaded', 'version': '—', ",
      "        'ruleCount': 0, 'defaultDecision': '—', 'loaded': False, 'error': str(e)}))",
    ].join("\n");

    const child = cp.spawn(pythonPath, ["-c", script], {
      stdio: ["ignore", "pipe", "pipe"],
      shell: false,
      cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
    });

    let out = "";
    child.stdout.on("data", (d: Buffer) => (out += d.toString()));
    child.stderr.on("data", (d: Buffer) =>
      outputChannel.appendLine(`[policy check stderr] ${d.toString().trim()}`)
    );

    child.on("error", () =>
      resolve({
        name: "Unavailable",
        version: "—",
        ruleCount: 0,
        defaultDecision: "—",
        loaded: false,
      })
    );

    child.on("close", () => {
      try {
        const data = JSON.parse(out.trim());
        resolve(data as PolicyStatus);
      } catch {
        resolve({
          name: "Parse error",
          version: "—",
          ruleCount: 0,
          defaultDecision: "—",
          loaded: false,
        });
      }
    });
  });
}
