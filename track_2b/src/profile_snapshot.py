"""Create a Git-safe, reviewable snapshot of a project-local Hermes profile."""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path


_LITERAL_SECRET_KEY = re.compile(r"^\s*(api[_-]?key|token|secret|password|authorization|cookie)\s*:\s*(.+?)\s*$", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"^['\"]?\$\{[A-Z][A-Z0-9_]*\}['\"]?$")


def _check_config_for_literal_secrets(content: str) -> None:
    for line in content.splitlines():
        match = _LITERAL_SECRET_KEY.match(line)
        if match and not _PLACEHOLDER.fullmatch(match.group(2).strip()):
            raise ValueError("literal secret in configuration; use an environment placeholder instead")


def _snapshot_sources(runtime_dir: Path) -> list[tuple[Path, Path]]:
    required = [Path("SOUL.md"), Path("config.yaml")]
    sources: list[tuple[Path, Path]] = []
    for relative in required:
        source = runtime_dir / relative
        if not source.is_file():
            raise ValueError(f"required profile file is missing: {relative}")
        sources.append((source, relative))

    instructions = runtime_dir / "instructions"
    if instructions.is_dir():
        for source in sorted(instructions.rglob("*.md")):
            if source.is_file():
                sources.append((source, source.relative_to(runtime_dir)))
    return sources


def export_profile_snapshot(runtime_dir: Path, output_dir: Path) -> dict[str, list[str]]:
    """Export only approved profile sources; chats, state, logs and credentials stay local."""
    runtime_dir = runtime_dir.resolve()
    sources = _snapshot_sources(runtime_dir)
    config = (runtime_dir / "config.yaml").read_text(encoding="utf-8")
    _check_config_for_literal_secrets(config)

    output_dir = output_dir.resolve()
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    try:
        exported: list[str] = []
        for source, relative in sources:
            target = temporary_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            exported.append(relative.as_posix())

        backup_dir = output_dir.with_name(f".{output_dir.name}.backup")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        if output_dir.exists():
            output_dir.replace(backup_dir)
        temporary_dir.replace(output_dir)
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        return {"files": exported}
    except Exception:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        raise


def apply_profile_to_runtime(profile_dir: Path, runtime_dir: Path) -> dict[str, list[str]]:
    """Apply versioned profile sources without touching operational runtime data."""
    profile_dir = profile_dir.resolve()
    sources = _snapshot_sources(profile_dir)
    config = (profile_dir / "config.yaml").read_text(encoding="utf-8")
    _check_config_for_literal_secrets(config)

    runtime_dir = runtime_dir.resolve()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(tempfile.mkdtemp(prefix=".profile-apply-", dir=runtime_dir))
    try:
        exported: list[str] = []
        for source, relative in sources:
            target = staging_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            exported.append(relative.as_posix())

        staged_instructions = staging_dir / "instructions"
        staged_instructions.mkdir(exist_ok=True)
        existing_instructions = runtime_dir / "instructions"
        backup_instructions = staging_dir / ".previous-instructions"
        if existing_instructions.exists():
            existing_instructions.replace(backup_instructions)
        staged_instructions.replace(existing_instructions)

        for filename in ("SOUL.md", "config.yaml"):
            (staging_dir / filename).replace(runtime_dir / filename)
        return {"files": exported}
    except Exception:
        if not (runtime_dir / "instructions").exists() and (staging_dir / ".previous-instructions").exists():
            (staging_dir / ".previous-instructions").replace(runtime_dir / "instructions")
        raise
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)
