"""Tests for the Atomic Execution Pipeline (AEP) -- Layer 5."""

import os
import platform
import tempfile
from pathlib import Path

import pytest

from aigis.aep import (
    AEPResult,
    AtomicPipeline,
    ProcessSandbox,
    SandboxResult,
    Vaporizer,
    VaporizeResult,
)


# =====================================================================
# ProcessSandbox
# =====================================================================


class TestProcessSandbox:
    """Tests for ProcessSandbox."""

    def setup_method(self):
        self.sandbox = ProcessSandbox()

    def test_simple_echo(self):
        result = self.sandbox.execute("echo hello")
        assert result.exit_code == 0
        assert "hello" in result.stdout
        assert result.execution_time_ms > 0

    def test_stderr_capture(self):
        if platform.system() == "Windows":
            result = self.sandbox.execute("echo error 1>&2")
        else:
            result = self.sandbox.execute("echo error >&2")
        assert "error" in result.stderr

    def test_exit_code(self):
        if platform.system() == "Windows":
            result = self.sandbox.execute("exit /b 42")
        else:
            result = self.sandbox.execute("exit 42")
        assert result.exit_code == 42

    def test_timeout(self):
        if platform.system() == "Windows":
            result = self.sandbox.execute("ping -n 10 127.0.0.1 >nul", timeout=0.5)
        else:
            result = self.sandbox.execute("sleep 10", timeout=0.5)
        assert result.exit_code == -1

    def test_artifact_detection(self):
        work_dir = Path(tempfile.mkdtemp(prefix="aep_test_"))
        try:
            if platform.system() == "Windows":
                result = self.sandbox.execute(
                    "echo data > artifact.txt",
                    work_dir=work_dir,
                )
            else:
                result = self.sandbox.execute(
                    "echo data > artifact.txt",
                    work_dir=work_dir,
                )
            assert result.exit_code == 0
            assert "artifact.txt" in result.artifacts
        finally:
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)

    def test_env_stripping(self):
        """Environment should only contain safe keys."""
        if platform.system() == "Windows":
            result = self.sandbox.execute("set")
        else:
            result = self.sandbox.execute("env")
        # SECRET_VALUE should never leak through.
        os.environ["AEP_TEST_SECRET"] = "super_secret_123"
        try:
            if platform.system() == "Windows":
                result = self.sandbox.execute("set AEP_TEST_SECRET")
            else:
                result = self.sandbox.execute("echo $AEP_TEST_SECRET")
            # The secret should not appear in output (it was stripped).
            assert "super_secret_123" not in result.stdout
        finally:
            del os.environ["AEP_TEST_SECRET"]

    def test_custom_env_passed_through(self):
        if platform.system() == "Windows":
            result = self.sandbox.execute(
                "echo %MY_VAR%",
                env={"MY_VAR": "hello_world"},
            )
        else:
            result = self.sandbox.execute(
                "echo $MY_VAR",
                env={"MY_VAR": "hello_world"},
            )
        assert "hello_world" in result.stdout

    def test_sandbox_result_dataclass(self):
        r = SandboxResult(
            stdout="out", stderr="err", exit_code=0,
            execution_time_ms=1.5, artifacts=["a.txt"],
        )
        assert r.stdout == "out"
        assert r.artifacts == ["a.txt"]

    def test_repr(self):
        assert "ProcessSandbox" in repr(self.sandbox)


# =====================================================================
# Vaporizer
# =====================================================================


class TestVaporizer:
    """Tests for Vaporizer."""

    def setup_method(self):
        self.vaporizer = Vaporizer()

    def _make_files(self, work_dir: Path, names: list[str]) -> None:
        for name in names:
            p = work_dir / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"content of {name}")

    def test_vaporize_all(self):
        work_dir = Path(tempfile.mkdtemp(prefix="aep_vap_"))
        self._make_files(work_dir, ["a.txt", "b.txt", "sub/c.txt"])
        result = self.vaporizer.vaporize(work_dir)
        assert result.files_destroyed == 3
        assert result.files_kept == 0
        assert result.verified is True
        assert result.files_failed == []

    def test_vaporize_with_keep(self):
        work_dir = Path(tempfile.mkdtemp(prefix="aep_vap_"))
        self._make_files(work_dir, ["keep_me.txt", "destroy_me.txt", "also_destroy.txt"])
        result = self.vaporizer.vaporize(work_dir, keep=["keep_me.txt"])
        assert result.files_destroyed == 2
        assert result.files_kept == 1
        assert result.verified is True
        assert (work_dir / "keep_me.txt").exists()
        assert not (work_dir / "destroy_me.txt").exists()

    def test_vaporize_with_subdirectory_keep(self):
        work_dir = Path(tempfile.mkdtemp(prefix="aep_vap_"))
        self._make_files(work_dir, ["out/result.txt", "tmp/junk.txt"])
        result = self.vaporizer.vaporize(work_dir, keep=["out/result.txt"])
        assert result.files_kept == 1
        assert result.files_destroyed == 1
        assert (work_dir / "out" / "result.txt").exists()

    def test_verify_destruction_empty_dir(self):
        work_dir = Path(tempfile.mkdtemp(prefix="aep_vap_"))
        assert self.vaporizer.verify_destruction(work_dir) is True

    def test_verify_destruction_nonexistent(self):
        work_dir = Path(tempfile.mkdtemp(prefix="aep_vap_"))
        import shutil
        shutil.rmtree(work_dir)
        assert self.vaporizer.verify_destruction(work_dir) is True

    def test_secure_overwrite(self):
        """Files should be overwritten before deletion."""
        work_dir = Path(tempfile.mkdtemp(prefix="aep_vap_"))
        target = work_dir / "secret.txt"
        original_content = "TOP SECRET DATA"
        target.write_text(original_content)

        # We cannot directly observe the overwrite, but we can verify
        # the file is gone after vaporize.
        result = self.vaporizer.vaporize(work_dir)
        assert result.files_destroyed == 1
        assert not target.exists()

    def test_vaporize_result_dataclass(self):
        r = VaporizeResult(files_destroyed=5, files_kept=1)
        assert r.files_destroyed == 5
        assert r.files_failed == []
        assert r.verified is False

    def test_repr(self):
        assert "Vaporizer" in repr(self.vaporizer)


# =====================================================================
# AtomicPipeline
# =====================================================================


class TestAtomicPipeline:
    """Tests for the full Scan -> Execute -> Vaporize pipeline."""

    def setup_method(self):
        self.pipeline = AtomicPipeline()

    def test_simple_execution(self):
        result = self.pipeline.execute("echo hello_from_aep")
        assert result.exit_code == 0
        assert "hello_from_aep" in result.output
        assert result.scan_result is not None
        assert result.scan_result.blocked is False
        assert result.artifacts_destroyed is True
        assert result.sandbox_type == "process"
        assert result.opted_out is False

    def test_blocked_by_scan(self):
        """Dangerous code should be blocked before execution."""
        # SQL injection patterns should trigger the scanner.
        malicious = "UNION SELECT * FROM users; DROP TABLE users; --"
        result = self.pipeline.execute(malicious)
        assert result.exit_code == -2
        assert result.scan_result is not None
        assert result.scan_result.blocked is True
        assert result.output == ""
        assert "blocked" in result.stderr.lower()

    def test_vaporize_opt_out(self):
        pipe = AtomicPipeline(vaporize=False)
        result = pipe.execute("echo opted_out")
        assert result.opted_out is True
        assert result.artifacts_destroyed is False
        assert "opted_out" in result.output

    def test_declared_outputs_kept(self):
        if platform.system() == "Windows":
            code = "echo result_data > output.txt"
        else:
            code = "echo result_data > output.txt"
        result = self.pipeline.execute(code, declared_outputs=["output.txt"])
        assert result.exit_code == 0
        # The output.txt should have been in the keep list.
        if result.vaporize_result is not None:
            assert result.vaporize_result.files_kept >= 1

    def test_timeout_in_pipeline(self):
        if platform.system() == "Windows":
            code = "ping -n 20 127.0.0.1 >nul"
        else:
            code = "sleep 20"
        result = self.pipeline.execute(code, timeout=0.5)
        assert result.exit_code == -1

    def test_execution_time_recorded(self):
        result = self.pipeline.execute("echo fast")
        assert result.execution_time_ms > 0

    def test_aep_result_dataclass(self):
        r = AEPResult(
            output="hi",
            scan_result=None,
            execution_time_ms=5.0,
            artifacts_destroyed=True,
            sandbox_type="process",
            exit_code=0,
        )
        assert r.output == "hi"
        assert r.opted_out is False

    def test_repr(self):
        assert "AtomicPipeline" in repr(self.pipeline)


# =====================================================================
# Integration: end-to-end with file creation and destruction
# =====================================================================


class TestAEPIntegration:
    """End-to-end integration tests."""

    def test_create_and_destroy_artifacts(self):
        pipe = AtomicPipeline()
        if platform.system() == "Windows":
            code = "echo secret > temp.txt && echo output > result.txt"
        else:
            code = "echo secret > temp.txt && echo output > result.txt"
        result = pipe.execute(code, declared_outputs=["result.txt"])
        assert result.exit_code == 0
        assert result.artifacts_destroyed is True
        if result.vaporize_result:
            # temp.txt should have been destroyed
            assert result.vaporize_result.files_destroyed >= 1
            # result.txt should have been kept
            assert result.vaporize_result.files_kept >= 1

    def test_safe_code_full_cycle(self):
        pipe = AtomicPipeline()
        result = pipe.execute("echo 'Aigis AEP working'")
        assert result.exit_code == 0
        assert result.scan_result is not None
        assert result.scan_result.blocked is False
        assert result.artifacts_destroyed is True
        assert "Aigis AEP working" in result.output
