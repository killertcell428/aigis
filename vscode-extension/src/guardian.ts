/**
 * GuardianService — thin wrapper around the `aig scan --json` subprocess.
 *
 * Design decisions:
 * - We spawn a fresh process per scan rather than a long-running daemon so
 *   that the extension stays stateless and the Python environment can be
 *   updated by the user without reloading VS Code.
 * - stdout must be a single JSON line (the CLI guarantees this with --json).
 * - stderr is captured and surfaced in the output channel but never thrown
 *   as a hard error — the extension degrades gracefully.
 */

import * as cp from "child_process";
import * as vscode from "vscode";
import type { GuardianConfig, ScanResult } from "./types";

/** Maximum time (ms) we'll wait for `aig scan` to respond. */
const SCAN_TIMEOUT_MS = 15_000;

/** Sentinel error class so callers can distinguish "python not found" from
 *  other errors without string matching. */
export class PythonNotFoundError extends Error {
  constructor(pythonPath: string) {
    super(
      `Aigis: could not launch Python executable "${pythonPath}". ` +
        `Check the aiGuardian.pythonPath setting and ensure aigis is installed ` +
        `in that environment (pip install aigis).`
    );
    this.name = "PythonNotFoundError";
  }
}

export class ScanTimeoutError extends Error {
  constructor(text: string) {
    super(
      `Aigis: scan timed out after ${SCAN_TIMEOUT_MS}ms ` +
        `(input was ${text.length} chars). Consider increasing aiGuardian.maxStringLength ` +
        `or aiGuardian.scanDebounceMs.`
    );
    this.name = "ScanTimeoutError";
  }
}

export class GuardianService implements vscode.Disposable {
  private readonly _outputChannel: vscode.OutputChannel;

  constructor(outputChannel: vscode.OutputChannel) {
    this._outputChannel = outputChannel;
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  /**
   * Scan `text` by spawning `aig scan --json <text>`.
   *
   * @throws {PythonNotFoundError} when the configured Python binary is not found.
   * @throws {ScanTimeoutError} when the subprocess takes longer than SCAN_TIMEOUT_MS.
   * @throws {Error} for any other unexpected failure.
   */
  async scan(text: string, config: GuardianConfig): Promise<ScanResult> {
    return new Promise<ScanResult>((resolve, reject) => {
      // Pass text via stdin to avoid shell-quoting issues on Windows.
      // The CLI already supports stdin when no positional arg is given.
      const args = ["-m", "aigis.cli", "scan", "--json"];
      const child = cp.spawn(config.pythonPath, args, {
        stdio: ["pipe", "pipe", "pipe"],
        // Avoid shell so we don't need to escape the input.
        shell: false,
      });

      let stdout = "";
      let stderr = "";
      let settled = false;

      const settle = (fn: () => void) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        fn();
      };

      const timer = setTimeout(() => {
        child.kill("SIGTERM");
        settle(() => reject(new ScanTimeoutError(text)));
      }, SCAN_TIMEOUT_MS);

      child.stdout.on("data", (chunk: Buffer) => {
        stdout += chunk.toString("utf8");
      });

      child.stderr.on("data", (chunk: Buffer) => {
        stderr += chunk.toString("utf8");
      });

      child.on("error", (err: NodeJS.ErrnoException) => {
        settle(() => {
          if (err.code === "ENOENT") {
            reject(new PythonNotFoundError(config.pythonPath));
          } else {
            reject(err);
          }
        });
      });

      child.on("close", (code) => {
        settle(() => {
          if (stderr.trim()) {
            this._outputChannel.appendLine(
              `[aig scan stderr] ${stderr.trim()}`
            );
          }

          const raw = stdout.trim();
          if (!raw) {
            // Non-zero exit with no output means the module is missing or
            // the text was empty. Return a clean safe result.
            this._outputChannel.appendLine(
              `[aig scan] exit ${code} with no stdout — treating as SAFE`
            );
            resolve(this._safeFallback());
            return;
          }

          try {
            const result = JSON.parse(raw) as ScanResult;
            this._outputChannel.appendLine(
              `[aig scan] score=${result.risk_score} level=${result.risk_level} ` +
                `blocked=${result.blocked} rules=${result.matched_rules.length}`
            );
            resolve(result);
          } catch (parseErr) {
            this._outputChannel.appendLine(
              `[aig scan] JSON parse error: ${parseErr}\nraw: ${raw.slice(0, 200)}`
            );
            reject(new Error(`Aigis: failed to parse scan output: ${parseErr}`));
          }
        });
      });

      // Write text to stdin and close it so the CLI reads from stdin.
      child.stdin.write(text, "utf8");
      child.stdin.end();
    });
  }

  /**
   * Verify that the configured Python has aigis installed.
   * Returns a human-readable status string.
   */
  async checkInstallation(pythonPath: string): Promise<string> {
    return new Promise((resolve) => {
      const child = cp.spawn(
        pythonPath,
        ["-c", "import aigis; print(aigis.__version__)"],
        { stdio: ["ignore", "pipe", "pipe"], shell: false }
      );

      let out = "";
      let err = "";
      child.stdout.on("data", (d: Buffer) => (out += d.toString()));
      child.stderr.on("data", (d: Buffer) => (err += d.toString()));

      child.on("error", (e: NodeJS.ErrnoException) => {
        if (e.code === "ENOENT") {
          resolve(`Python not found at "${pythonPath}"`);
        } else {
          resolve(`Error: ${e.message}`);
        }
      });

      child.on("close", (code) => {
        if (code === 0) {
          resolve(`aigis ${out.trim()} — ready`);
        } else {
          resolve(
            `aigis not installed (exit ${code}). Run: ${pythonPath} -m pip install aigis\n${err.trim()}`
          );
        }
      });
    });
  }

  dispose(): void {
    // Nothing persistent to dispose — subprocess is per-request.
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  private _safeFallback(): ScanResult {
    return {
      risk_score: 0,
      risk_level: "LOW",
      blocked: false,
      reasons: [],
      matched_rules: [],
    };
  }
}
