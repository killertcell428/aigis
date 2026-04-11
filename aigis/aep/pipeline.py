"""Atomic Execution Pipeline -- Scan -> Execute -> Vaporize.

The ``AtomicPipeline`` guarantees that:

1. Input is **always** scanned before execution.
2. Execution happens in an **isolated** sandbox.
3. Only declared outputs survive; everything else is **destroyed**.
4. The entire operation is logged atomically.
5. Opting out of vaporize requires an explicit flag and emits an
   audit-level warning.
"""

from __future__ import annotations

import logging
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path

from aigis.aep.sandbox import ProcessSandbox, Sandbox, SandboxResult
from aigis.aep.vaporizer import Vaporizer, VaporizeResult
from aigis.guard import Guard
from aigis.types import CheckResult

logger = logging.getLogger(__name__)


@dataclass
class AEPResult:
    """Outcome of an Atomic Execution Pipeline run."""

    output: str
    """Captured stdout from the sandbox."""

    scan_result: CheckResult | None
    """Result of the pre-execution security scan."""

    execution_time_ms: float
    """Wall-clock time for the sandbox execution step."""

    artifacts_destroyed: bool
    """``True`` if vaporize ran successfully."""

    sandbox_type: str
    """Kind of sandbox used: ``"process"`` | ``"wasm"`` | ``"none"``."""

    exit_code: int
    """Process exit code (``-1`` for timeout, ``-2`` for scan block)."""

    opted_out: bool = False
    """``True`` when vaporize was explicitly skipped."""

    stderr: str = ""
    """Captured stderr from the sandbox."""

    vaporize_result: VaporizeResult | None = None
    """Detailed vaporize metrics, if vaporize ran."""

    artifacts: list[str] = field(default_factory=list)
    """Files created during execution (before vaporize)."""


class AtomicPipeline:
    """Scan -> Execute -> Vaporize as an indivisible security primitive.

    Guarantees
    ----------
    1. Input is always scanned before execution.
    2. Execution happens in isolation (default: ``ProcessSandbox``).
    3. Only declared outputs survive; all else is destroyed.
    4. The entire operation is logged atomically.
    5. Opting out of vaporize requires an explicit flag **and** an audit
       log warning.

    Example::

        from aigis.aep import AtomicPipeline

        pipe = AtomicPipeline()
        result = pipe.execute("echo hello", declared_outputs=["output.txt"])
        print(result.output)      # "hello\\n"
        print(result.exit_code)   # 0
    """

    def __init__(
        self,
        guard: Guard | None = None,
        sandbox: Sandbox | None = None,
        *,
        vaporize: bool = True,
    ) -> None:
        """Create an AtomicPipeline.

        Args:
            guard: Security scanner.  Defaults to ``Guard()`` with the
                default policy.
            sandbox: Execution sandbox.  Defaults to ``ProcessSandbox()``.
            vaporize: If ``False``, the vaporize step is skipped and an
                audit warning is emitted for every execution.
        """
        self._guard = guard or Guard()
        self._sandbox: Sandbox = sandbox or ProcessSandbox()
        self._vaporize = vaporize
        self._vaporizer = Vaporizer()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(
        self,
        code: str,
        *,
        declared_outputs: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> AEPResult:
        """Run the full Scan -> Execute -> Vaporize pipeline.

        Args:
            code: Shell code to execute.
            declared_outputs: Relative file paths that should survive
                vaporization.  ``None`` means nothing survives.
            env: Extra environment variables passed into the sandbox.
            timeout: Maximum wall-clock seconds for execution.

        Returns:
            ``AEPResult`` with captured output, scan results, and
            destruction status.
        """
        with self._lock:
            return self._execute_atomic(code, declared_outputs, env, timeout)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _execute_atomic(
        self,
        code: str,
        declared_outputs: list[str] | None,
        env: dict[str, str] | None,
        timeout: float,
    ) -> AEPResult:
        sandbox_type = self._sandbox_type_name()
        work_dir = Path(tempfile.mkdtemp(prefix="aep_pipeline_"))

        # ---- STEP 1: SCAN ----
        scan_result = self._guard.check_input(code)
        if scan_result.blocked:
            logger.warning(
                "AEP scan blocked execution (score=%d, reasons=%s)",
                scan_result.risk_score,
                scan_result.reasons,
            )
            # Clean up the temp directory -- nothing was written.
            self._cleanup_dir(work_dir)
            return AEPResult(
                output="",
                scan_result=scan_result,
                execution_time_ms=0.0,
                artifacts_destroyed=True,
                sandbox_type=sandbox_type,
                exit_code=-2,
                stderr="Execution blocked by security scan.",
            )

        # ---- STEP 2: EXECUTE ----
        sandbox_result: SandboxResult | None = None
        try:
            sandbox_result = self._sandbox.execute(
                code=code,
                env=env or {},
                timeout=timeout,
                work_dir=work_dir,
            )
        except Exception:
            logger.exception("Sandbox execution failed -- vaporizing work_dir")
            # Ensure we still vaporize even if execution raises.
            self._force_vaporize(work_dir)
            raise

        # ---- STEP 3: VAPORIZE ----
        vaporize_result: VaporizeResult | None = None
        artifacts_destroyed = False
        opted_out = False

        if self._vaporize:
            vaporize_result = self._vaporizer.vaporize(work_dir, keep=declared_outputs)
            artifacts_destroyed = vaporize_result.verified
            if not vaporize_result.verified:
                logger.error(
                    "Vaporize verification FAILED -- %d files could not be destroyed: %s",
                    len(vaporize_result.files_failed),
                    vaporize_result.files_failed,
                )
        else:
            opted_out = True
            logger.warning(
                "AUDIT: vaporize=False -- sandbox artifacts in %s are NOT destroyed. "
                "This weakens the security guarantee of the Atomic Execution Pipeline.",
                work_dir,
            )

        return AEPResult(
            output=sandbox_result.stdout,
            scan_result=scan_result,
            execution_time_ms=sandbox_result.execution_time_ms,
            artifacts_destroyed=artifacts_destroyed,
            sandbox_type=sandbox_type,
            exit_code=sandbox_result.exit_code,
            stderr=sandbox_result.stderr,
            vaporize_result=vaporize_result,
            artifacts=sandbox_result.artifacts,
            opted_out=opted_out,
        )

    def _sandbox_type_name(self) -> str:
        """Return a human-readable sandbox type string."""
        cls_name = type(self._sandbox).__name__.lower()
        if "process" in cls_name:
            return "process"
        if "wasm" in cls_name:
            return "wasm"
        return "unknown"

    def _force_vaporize(self, work_dir: Path) -> None:
        """Best-effort vaporize on error paths."""
        try:
            self._vaporizer.vaporize(work_dir)
        except Exception:
            logger.exception("Force-vaporize also failed for %s", work_dir)

    @staticmethod
    def _cleanup_dir(work_dir: Path) -> None:
        """Remove an empty temp directory (no artifacts to destroy)."""
        try:
            if work_dir.exists():
                import shutil

                shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass

    def __repr__(self) -> str:
        return (
            f"AtomicPipeline(guard={self._guard!r}, "
            f"sandbox={self._sandbox!r}, "
            f"vaporize={self._vaporize})"
        )
