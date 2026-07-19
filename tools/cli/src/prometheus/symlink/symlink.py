"""Symlink management for Prometheus."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class SymlinkManager:
    """Manages symbolic links for Prometheus projects."""

    @staticmethod
    def create_symlink(source: str | Path, target: str | Path) -> None:
        """Create a symbolic link from target pointing to source.

        Args:
            source: Source path (what the symlink points to).
            target: Target path (where the symlink will be created).

        Raises:
            OSError: If symlink creation fails.
            RuntimeError: If the operation is not supported on this platform.
        """
        source = Path(source)
        target = Path(target)

        # Ensure source exists
        if not source.exists():
            raise FileNotFoundError(f"Source path does not exist: {source}")

        # Remove target if it exists
        if target.exists() or target.is_symlink():
            if target.is_symlink():
                target.unlink()
            elif target.is_dir():
                raise FileExistsError(f"Target directory already exists: {target}")
            else:
                target.unlink()

        # Create symlink using OS-appropriate method
        if sys.platform == "win32":
            SymlinkManager._create_symlink_windows(source, target)
        else:
            SymlinkManager._create_symlink_unix(source, target)

    @staticmethod
    def _create_symlink_windows(source: Path, target: Path) -> None:
        """Create a symlink on Windows.

        Tries os.symlink first (Windows 10+ without admin), then falls back to mklink.
        Note: Both methods typically require either Developer Mode or admin privileges.
        """
        # First, try using os.symlink (works on Windows 10+ with Developer Mode or admin)
        try:
            os.symlink(source, target, target_is_directory=True)
            return
        except (OSError, NotImplementedError) as e:
            # Developer Mode not enabled or older Windows, try mklink
            pass

        # Fall back to mklink which requires admin privileges
        try:
            result = subprocess.run(
                ["mklink", "/D", str(target), str(source)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                # Provide clear guidance for Windows
                raise OSError(
                    f"Could not create .github symlink. This typically requires:\n"
                    f"  • Administrator privileges (run PowerShell as admin), OR\n"
                    f"  • Enable Developer Mode on Windows 10+\n"
                    f"  (Settings > Update & Security > For developers > Developer mode)\n"
                    f"\nError details: {error_msg}"
                )
        except FileNotFoundError:
            raise OSError(
                f"Could not create .github symlink. This typically requires:\n"
                f"  • Administrator privileges (run PowerShell as admin), OR\n"
                f"  • Enable Developer Mode on Windows 10+\n"
                f"  (Settings > Update & Security > For developers > Developer mode)\n"
                f"\nThe mklink command was not found in PATH."
            )

    @staticmethod
    def _create_symlink_unix(source: Path, target: Path) -> None:
        """Create a symlink on Unix-like systems using os.symlink."""
        try:
            os.symlink(source, target)
        except OSError as e:
            raise OSError(f"Failed to create Unix symlink: {e}")

    @staticmethod
    def remove_symlink(path: str | Path) -> None:
        """Remove a symbolic link.

        Args:
            path: Path to the symlink.

        Raises:
            FileNotFoundError: If the path does not exist.
            OSError: If removal fails.
        """
        path = Path(path)
        if not path.exists() and not path.is_symlink():
            raise FileNotFoundError(f"Path does not exist: {path}")

        if path.is_symlink() or path.is_dir():
            path.unlink()
        else:
            path.unlink()

    @staticmethod
    def is_symlink(path: str | Path) -> bool:
        """Check if a path is a symbolic link.

        Args:
            path: Path to check.

        Returns:
            True if path is a symlink, False otherwise.
        """
        path = Path(path)
        return path.is_symlink()
