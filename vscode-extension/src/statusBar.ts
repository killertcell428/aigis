/**
 * StatusBarManager — manages the Aigis item in the VS Code status bar.
 *
 * Shows:
 *   - Idle:        $(shield) Aigis
 *   - Scanning:    $(loading~spin) Aigis: scanning…
 *   - Clean:       $(shield-check) Aigis: clean
 *   - Warnings:    $(warning) Aigis: N warnings
 *   - Errors:      $(error) Aigis: N errors
 *   - Unavailable: $(shield-x) Aigis: unavailable
 */

import * as vscode from "vscode";
import type { StatusBarState } from "./types";

export class StatusBarManager implements vscode.Disposable {
  private readonly _item: vscode.StatusBarItem;

  constructor() {
    this._item = vscode.window.createStatusBarItem(
      "aiGuardian.status",
      vscode.StatusBarAlignment.Right,
      100
    );
    this._item.command = "aiGuardian.showOutput";
    this._item.tooltip = "Aigis — click to open output";
    this.setState("idle");
  }

  show(): void {
    this._item.show();
  }

  hide(): void {
    this._item.hide();
  }

  setState(state: StatusBarState, count?: number): void {
    switch (state) {
      case "idle":
        this._item.text = "$(shield) Aigis";
        this._item.color = undefined;
        this._item.backgroundColor = undefined;
        break;

      case "scanning":
        this._item.text = "$(loading~spin) Aigis: scanning…";
        this._item.color = undefined;
        this._item.backgroundColor = undefined;
        break;

      case "clean":
        this._item.text = "$(pass-filled) Aigis: clean";
        this._item.color = new vscode.ThemeColor("charts.green");
        this._item.backgroundColor = undefined;
        break;

      case "warnings": {
        const n = count ?? 0;
        this._item.text = `$(warning) Aigis: ${n} warning${n !== 1 ? "s" : ""}`;
        this._item.color = new vscode.ThemeColor("charts.yellow");
        this._item.backgroundColor = undefined;
        break;
      }

      case "errors": {
        const n = count ?? 0;
        this._item.text = `$(error) Aigis: ${n} issue${n !== 1 ? "s" : ""}`;
        this._item.color = undefined;
        this._item.backgroundColor = new vscode.ThemeColor(
          "statusBarItem.errorBackground"
        );
        break;
      }

      case "unavailable":
        this._item.text = "$(shield-x) Aigis: unavailable";
        this._item.color = new vscode.ThemeColor("disabledForeground");
        this._item.backgroundColor = undefined;
        break;
    }
  }

  /**
   * Update the status bar to reflect the current diagnostic counts for the
   * active document.
   */
  updateFromDiagnostics(diagnostics: readonly vscode.Diagnostic[]): void {
    if (diagnostics.length === 0) {
      this.setState("clean");
      return;
    }

    const errors = diagnostics.filter(
      (d) => d.severity === vscode.DiagnosticSeverity.Error
    ).length;
    const warnings = diagnostics.filter(
      (d) => d.severity === vscode.DiagnosticSeverity.Warning
    ).length;

    if (errors > 0) {
      this.setState("errors", errors + warnings);
    } else {
      this.setState("warnings", warnings);
    }
  }

  dispose(): void {
    this._item.dispose();
  }
}
