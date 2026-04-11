"""Vaporizer -- secure destruction of sandbox artifacts.

After the sandbox completes, the Vaporizer ensures that only explicitly
declared output files survive.  All other files are overwritten with
random bytes before unlinking, preventing forensic recovery.

On Windows, file-locking is common so the implementation retries with
exponential backoff before reporting a failure.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Default retry parameters for locked files (Windows).
_MAX_RETRIES = 4
_BACKOFF_BASE_S = 0.05  # 50 ms


@dataclass
class VaporizeResult:
    """Outcome of a vaporize operation."""

    files_destroyed: int
    files_kept: int
    files_failed: list[str] = field(default_factory=list)
    verified: bool = False


class Vaporizer:
    """Securely destroy sandbox artifacts.

    Workflow
    --------
    1. Enumerate all files under *work_dir*.
    2. For each file **not** on the *keep* list:
       a. Overwrite contents with ``os.urandom`` (same size as original).
       b. Flush and ``os.unlink`` the file.
    3. Remove empty directories.
    4. Verify that only *keep* files remain.

    On Windows, files may be temporarily locked by antivirus or indexers.
    The implementation retries deletion with exponential backoff before
    recording a failure.
    """

    def __init__(
        self, *, max_retries: int = _MAX_RETRIES, backoff_base: float = _BACKOFF_BASE_S
    ) -> None:
        self._max_retries = max_retries
        self._backoff_base = backoff_base

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def vaporize(
        self,
        work_dir: Path,
        *,
        keep: list[str] | None = None,
    ) -> VaporizeResult:
        """Destroy all files in *work_dir* except those listed in *keep*.

        Args:
            work_dir: Root directory to purge.
            keep: Relative paths (forward slashes) of files to preserve.
                  ``None`` means destroy everything.

        Returns:
            ``VaporizeResult`` summarising what happened.
        """
        keep_set = self._normalise_keep(keep)

        all_files = self._list_files(work_dir)
        destroyed = 0
        kept = 0
        failed: list[str] = []

        for rel_path in sorted(all_files):
            if rel_path in keep_set:
                kept += 1
                continue

            abs_path = work_dir / rel_path
            ok = self._secure_delete(abs_path)
            if ok:
                destroyed += 1
            else:
                failed.append(rel_path)

        # Remove empty directories bottom-up.
        self._prune_empty_dirs(work_dir)

        verified = self.verify_destruction(work_dir, keep)

        return VaporizeResult(
            files_destroyed=destroyed,
            files_kept=kept,
            files_failed=failed,
            verified=verified,
        )

    def verify_destruction(self, work_dir: Path, keep: list[str] | None = None) -> bool:
        """Check that only *keep* files remain under *work_dir*.

        Returns ``True`` when the directory state matches expectations.
        """
        if not work_dir.exists():
            # Directory itself was removed -- that counts as verified.
            return True

        keep_set = self._normalise_keep(keep)
        remaining = self._list_files(work_dir)
        unexpected = remaining - keep_set
        if unexpected:
            logger.warning(
                "Vaporize verification failed -- unexpected files remain: %s",
                sorted(unexpected),
            )
            return False
        return True

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _secure_delete(self, path: Path) -> bool:
        """Overwrite *path* with random data, then unlink.

        Symlinks are unlinked without following (we do NOT overwrite the
        symlink target, which may reside outside the work directory).

        Returns ``True`` on success, ``False`` if the file could not be
        removed (e.g. locked on Windows).
        """
        # Safety: never follow symlinks — just remove the link itself.
        if path.is_symlink():
            logger.warning("Removing symlink without following: %s -> %s", path, os.readlink(path))
            return self._unlink_with_retry(path)

        try:
            size = path.stat().st_size
            # Overwrite with cryptographically random bytes.
            with open(path, "wb") as fh:
                if size > 0:
                    fh.write(os.urandom(size))
                else:
                    fh.write(os.urandom(1))
                fh.flush()
                os.fsync(fh.fileno())
        except OSError as exc:
            logger.debug("Could not overwrite %s: %s", path, exc)
            # Still try to unlink even if overwrite failed.

        return self._unlink_with_retry(path)

    def _unlink_with_retry(self, path: Path) -> bool:
        """Attempt to delete *path*, retrying with backoff on failure."""
        for attempt in range(self._max_retries + 1):
            try:
                path.unlink(missing_ok=True)
                return True
            except PermissionError:
                if attempt < self._max_retries:
                    delay = self._backoff_base * (2**attempt)
                    logger.debug(
                        "Retry %d/%d deleting %s (sleeping %.3fs)",
                        attempt + 1,
                        self._max_retries,
                        path,
                        delay,
                    )
                    time.sleep(delay)
                else:
                    logger.warning("Failed to delete %s after %d retries", path, self._max_retries)
                    return False
            except OSError as exc:
                logger.warning("Unexpected error deleting %s: %s", path, exc)
                return False
        return False  # pragma: no cover

    @staticmethod
    def _prune_empty_dirs(root: Path) -> None:
        """Remove empty directories under *root*, bottom-up."""
        if not root.exists():
            return
        # Walk bottom-up: sorted by depth descending ensures children
        # are processed before parents.
        dirs = sorted(
            (d for d in root.rglob("*") if d.is_dir()),
            key=lambda p: len(p.parts),
            reverse=True,
        )
        for d in dirs:
            try:
                d.rmdir()  # Only succeeds if empty.
            except OSError:
                pass

    @staticmethod
    def _normalise_keep(keep: list[str] | None) -> set[str]:
        """Normalise the keep list to a set of forward-slash relative paths."""
        if not keep:
            return set()
        return {p.replace("\\", "/") for p in keep}

    @staticmethod
    def _list_files(directory: Path) -> set[str]:
        """Return relative file paths (forward slashes) under *directory*.

        Includes symlinks as entries but does NOT follow them into
        directories outside *directory* (prevents symlink traversal attacks).
        """
        result: set[str] = set()
        if not directory.exists():
            return result
        for p in directory.rglob("*"):
            if p.is_symlink() or p.is_file():
                result.add(str(p.relative_to(directory)).replace("\\", "/"))
        return result

    def __repr__(self) -> str:
        return f"Vaporizer(max_retries={self._max_retries})"
