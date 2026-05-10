"""Package and publish local tick-depth data assets."""

from __future__ import annotations

import hashlib
import os
import shlex
import shutil
import subprocess
import tarfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rqdata_tick_data import __version__
from rqdata_tick_data.storage import write_json, write_yaml

GITHUB_RELEASE_ASSET_LIMIT_BYTES = 2 * 1024 * 1024 * 1024
DEFAULT_MAX_TAR_BYTES = 1_900_000_000
PART_NAMES = ("raw", "daily", "metadata", "reports", "configs")


@dataclass(frozen=True)
class PackageEntry:
    """A single local file selected for packaging."""

    source: Path
    arcname: str
    size_bytes: int
    source_root: Path
    part: str


def _utc_now() -> datetime:
    return datetime.now(UTC)


def default_as_of() -> str:
    return _utc_now().strftime("%Y%m%d")


def _resolve(path: str | Path, *, repo_root: Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


def _source_label(path: Path) -> str:
    return path.name or path.resolve().anchor.replace(os.sep, "")


def _iter_files(path: Path) -> list[Path]:
    if path.is_file() or path.is_symlink():
        return [path]
    return sorted(
        child
        for child in path.rglob("*")
        if (child.is_file() or child.is_symlink()) and not child.name.startswith(".")
    )


def _entry_size(path: Path) -> int:
    try:
        return int(path.lstat().st_size if path.is_symlink() else path.stat().st_size)
    except FileNotFoundError:
        return 0


def _collect_entries(
    *,
    part: str,
    paths: list[Path],
    repo_root: Path,
) -> tuple[list[PackageEntry], list[str]]:
    entries: list[PackageEntry] = []
    missing: list[str] = []
    for source_root in paths:
        if not source_root.exists() and not source_root.is_symlink():
            missing.append(str(source_root))
            continue
        label = _source_label(source_root)
        for file_path in _iter_files(source_root):
            if source_root.is_file() or source_root.is_symlink():
                relative = Path(file_path.name)
            else:
                relative = file_path.relative_to(source_root)
            arcname = Path(part) / label / relative
            entries.append(
                PackageEntry(
                    source=file_path,
                    arcname=arcname.as_posix(),
                    size_bytes=_entry_size(file_path),
                    source_root=source_root,
                    part=part,
                )
            )
    entries.sort(key=lambda entry: entry.arcname)
    return entries, missing


def _default_preset_paths(repo_root: Path) -> dict[str, list[Path]]:
    candidates = {
        "raw": [repo_root / "artifacts" / "cache" / "rqdata" / "hk_tick_depth"],
        "daily": [repo_root / "artifacts" / "cache" / "rqdata" / "hk_tick_depth_daily"],
        "reports": [repo_root / "artifacts" / "reports"],
        "configs": [repo_root / "configs" / "universe"],
        "metadata": [repo_root / "docs" / "records"],
    }
    return {
        part: [path for path in paths if path.exists() or path.is_symlink()]
        for part, paths in candidates.items()
    }


def _explicit_paths(
    *,
    repo_root: Path,
    raw_sources: list[str],
    daily_sources: list[str],
    metadata_sources: list[str],
    report_sources: list[str],
    config_sources: list[str],
) -> dict[str, list[Path]]:
    return {
        "raw": [_resolve(path, repo_root=repo_root) for path in raw_sources],
        "daily": [_resolve(path, repo_root=repo_root) for path in daily_sources],
        "metadata": [_resolve(path, repo_root=repo_root) for path in metadata_sources],
        "reports": [_resolve(path, repo_root=repo_root) for path in report_sources],
        "configs": [_resolve(path, repo_root=repo_root) for path in config_sources],
    }


def _merge_paths(
    base: dict[str, list[Path]],
    extra: dict[str, list[Path]],
) -> dict[str, list[Path]]:
    merged: dict[str, list[Path]] = {part: list(base.get(part, [])) for part in PART_NAMES}
    for part, paths in extra.items():
        seen = {str(path) for path in merged.setdefault(part, [])}
        for path in paths:
            key = str(path)
            if key not in seen:
                merged[part].append(path)
                seen.add(key)
    return merged


def _chunk_entries(entries: list[PackageEntry], max_input_bytes: int) -> list[list[PackageEntry]]:
    chunks: list[list[PackageEntry]] = []
    current: list[PackageEntry] = []
    current_size = 0
    for entry in entries:
        if current and current_size + entry.size_bytes > max_input_bytes:
            chunks.append(current)
            current = []
            current_size = 0
        current.append(entry)
        current_size += entry.size_bytes
    if current:
        chunks.append(current)
    return chunks


def _tar_name(*, name: str, as_of: str, part: str, index: int, total: int) -> str:
    suffix = f"{part}-part{index:03d}" if total > 1 or part == "raw" else part
    return f"{name}-{as_of}-{suffix}.tar.gz"


def _tar_entries(tar_path: Path, entries: list[PackageEntry]) -> None:
    tar_path.parent.mkdir(parents=True, exist_ok=True)
    if tar_path.exists():
        tar_path.unlink()
    with tarfile.open(tar_path, "w:gz") as tar:
        for entry in entries:
            tar.add(entry.source, arcname=entry.arcname, recursive=False)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _format_readme(manifest: dict[str, Any]) -> str:
    lines = [
        "# RQData Tick-Depth Asset Backup",
        "",
        f"Name: `{manifest['distribution']['name']}`",
        f"As of: `{manifest['distribution']['as_of']}`",
        f"Generated at: `{manifest['distribution']['generated_at']}`",
        "",
        "This directory contains local tarball backups for RQData HK tick-depth assets.",
        "Unpack selected tarballs into an extract directory and point downstream tooling at the",
        "extracted `raw/`, `daily/`, `metadata/`, `reports/`, or `configs/` paths.",
        "",
        "Tarballs:",
    ]
    for tarball in manifest.get("tarballs", []):
        lines.append(
            f"- `{tarball['file']}`: part `{tarball['part']}`, "
            f"{tarball['entry_count']} files, {tarball['size_bytes']} bytes"
        )
    lines.extend(
        [
            "",
            "Integrity:",
            "",
            "Compare each file against `manifest.yml` or `manifest.json`; both contain",
            "`sha256` and byte counts for every tarball.",
            "",
            "Provider note:",
            "",
            "These archives may contain provider-sourced data. Keep distribution aligned with",
            "the account and data-provider terms that apply to the workspace.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_release_notes(manifest: dict[str, Any]) -> str:
    lines = [
        f"Distribution: {manifest['distribution']['name']}",
        f"As of: {manifest['distribution']['as_of']}",
        f"Generated at: {manifest['distribution']['generated_at']}",
        "",
        "Assets:",
    ]
    for tarball in manifest.get("tarballs", []):
        lines.append(
            f"- {tarball['part']}: {tarball['file']} "
            f"({tarball['size_bytes']} bytes, sha256 {tarball['sha256']})"
        )
    return "\n".join(lines) + "\n"


def package_tick_assets(
    *,
    repo_root: str | Path = ".",
    preset: str = "explicit",
    name: str = "tick-depth",
    as_of: str | None = None,
    tar_dir: str | Path | None = None,
    raw_sources: list[str] | None = None,
    daily_sources: list[str] | None = None,
    metadata_sources: list[str] | None = None,
    report_sources: list[str] | None = None,
    config_sources: list[str] | None = None,
    parts: list[str] | None = None,
    max_tar_bytes: int = DEFAULT_MAX_TAR_BYTES,
    overwrite: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    selected_as_of = as_of or default_as_of()
    output_dir = (
        _resolve(tar_dir, repo_root=root)
        if tar_dir is not None
        else root / "artifacts" / "releases" / f"{name}_{selected_as_of}_tarballs"
    )
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite and not dry_run:
        raise FileExistsError(f"tar-dir exists and is not empty: {output_dir}")
    if output_dir.exists() and overwrite and not dry_run:
        shutil.rmtree(output_dir)
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    explicit = _explicit_paths(
        repo_root=root,
        raw_sources=raw_sources or [],
        daily_sources=daily_sources or [],
        metadata_sources=metadata_sources or [],
        report_sources=report_sources or [],
        config_sources=config_sources or [],
    )
    if preset == "current-cache":
        source_map = _merge_paths(_default_preset_paths(root), explicit)
    elif preset == "explicit":
        source_map = explicit
    else:
        raise ValueError(f"Unknown preset: {preset}")

    selected_parts = tuple(dict.fromkeys(parts or PART_NAMES))
    invalid_parts = [part for part in selected_parts if part not in PART_NAMES]
    if invalid_parts:
        raise ValueError(f"Unknown package part(s): {invalid_parts}")

    all_missing: list[str] = []
    tarballs: list[dict[str, Any]] = []
    sources_summary: dict[str, list[str]] = {}
    generated_at = _utc_now().isoformat(timespec="seconds")
    max_input_bytes = max(1, max_tar_bytes - 50 * 1024 * 1024)

    for part in selected_parts:
        entries, missing = _collect_entries(
            part=part,
            paths=source_map.get(part, []),
            repo_root=root,
        )
        all_missing.extend(missing)
        sources_summary[part] = [str(path) for path in source_map.get(part, [])]
        chunks = _chunk_entries(entries, max_input_bytes)
        for chunk_index, chunk in enumerate(chunks, start=1):
            tar_filename = _tar_name(
                name=name,
                as_of=selected_as_of,
                part=part,
                index=chunk_index,
                total=len(chunks),
            )
            tar_path = output_dir / tar_filename
            input_bytes = sum(entry.size_bytes for entry in chunk)
            if not dry_run:
                _tar_entries(tar_path, chunk)
                size_bytes = tar_path.stat().st_size
                sha256 = _sha256(tar_path)
                if size_bytes >= GITHUB_RELEASE_ASSET_LIMIT_BYTES:
                    raise ValueError(
                        f"Tarball exceeds GitHub release asset limit: {tar_path} "
                        f"({size_bytes} bytes). Use a smaller --max-tar-bytes value."
                    )
            else:
                size_bytes = 0
                sha256 = ""
            tarballs.append(
                {
                    "file": tar_filename,
                    "path": str(tar_path),
                    "part": part,
                    "chunk_index": chunk_index,
                    "chunk_count": len(chunks),
                    "entry_count": len(chunk),
                    "input_bytes": input_bytes,
                    "size_bytes": size_bytes,
                    "sha256": sha256,
                    "sample_entries": [entry.arcname for entry in chunk[:5]],
                }
            )

    if not tarballs:
        raise ValueError("No files selected for packaging.")

    manifest: dict[str, Any] = {
        "schema_version": "tick_depth_asset_release.v1",
        "distribution": {
            "name": name,
            "as_of": selected_as_of,
            "generated_at": generated_at,
            "preset": preset,
            "repo_root": str(root),
            "generator": {"package": "rqdata-tick-data", "version": __version__},
            "max_tar_bytes": max_tar_bytes,
        },
        "sources": sources_summary,
        "missing_sources": all_missing,
        "tar_dir": str(output_dir),
        "tarballs": tarballs,
    }
    if not dry_run:
        write_yaml(output_dir / "manifest.yml", manifest)
        write_json(output_dir / "manifest.json", manifest)
        (output_dir / "README.md").write_text(_format_readme(manifest), encoding="utf-8")
        (output_dir / f"{name}_{selected_as_of}_release_notes.txt").write_text(
            _format_release_notes(manifest),
            encoding="utf-8",
        )
    return manifest


def _run(cmd: list[str], *, dry_run: bool, capture: bool = False) -> subprocess.CompletedProcess:
    print("+", " ".join(shlex.quote(part) for part in cmd))
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return subprocess.run(cmd, check=False, capture_output=capture, text=True)


def upload_release_assets(
    *,
    tar_dir: str | Path,
    tag: str,
    repo: str | None = None,
    title: str | None = None,
    notes_file: str | Path | None = None,
    draft: bool = False,
    prerelease: bool = False,
    latest: bool = False,
    clobber: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    tar_root = Path(tar_dir).expanduser().resolve()
    if not tar_root.exists():
        raise FileNotFoundError(f"tar-dir not found: {tar_root}")
    tarballs = sorted(tar_root.glob("*.tar.gz"))
    if not tarballs:
        raise ValueError(f"No .tar.gz files found in {tar_root}")
    if not dry_run and shutil.which("gh") is None:
        raise RuntimeError("GitHub CLI (gh) not found in PATH.")

    repo_args = ["--repo", repo] if repo else []
    view_cmd = ["gh", "release", "view", tag, *repo_args]
    view_result = _run(view_cmd, dry_run=dry_run, capture=True)
    if dry_run:
        view_result = subprocess.CompletedProcess(view_cmd, 1, "", "")
    tar_args = [str(path) for path in tarballs]
    if view_result.returncode == 0:
        upload_cmd = ["gh", "release", "upload", tag, *tar_args, *repo_args]
        if clobber:
            upload_cmd.append("--clobber")
        result = _run(upload_cmd, dry_run=dry_run)
        action = "upload"
    else:
        selected_notes = (
            Path(notes_file).expanduser().resolve()
            if notes_file
            else next(iter(sorted(tar_root.glob("*_release_notes.txt"))), None)
        )
        create_cmd = [
            "gh",
            "release",
            "create",
            tag,
            *tar_args,
            "--title",
            title or tag,
            *repo_args,
        ]
        if selected_notes:
            create_cmd.extend(["--notes-file", str(selected_notes)])
        else:
            create_cmd.extend(["--notes", f"RQData tick-depth asset backup {tag}"])
        if draft:
            create_cmd.append("--draft")
        if prerelease:
            create_cmd.append("--prerelease")
        if latest:
            create_cmd.append("--latest")
        result = _run(create_cmd, dry_run=dry_run)
        action = "create"
    return {
        "tag": tag,
        "repo": repo,
        "tar_dir": str(tar_root),
        "tarballs": [str(path) for path in tarballs],
        "action": action,
        "dry_run": dry_run,
        "returncode": result.returncode,
    }
