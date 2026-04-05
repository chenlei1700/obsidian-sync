"""
obsidian-sync: Sync project documentation files (.md, .pdf, ...) to Obsidian vault.

Modes:
  symlink (default) - Move files to vault, create symlinks in project
  copy              - Copy files to vault, originals stay in project

Usage:
  python sync_to_obsidian.py                          # auto-detect everything
  python sync_to_obsidian.py --dry-run                # preview only
  python sync_to_obsidian.py --mode copy              # use copy mode
  python sync_to_obsidian.py --extensions .md,.pdf    # specify file types
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

# ── Exclusion rules ──────────────────────────────────────────────

EXCLUDED_FILENAMES = {
    "CLAUDE.md",
    "__context__.md",
}

EXCLUDED_DIRS = {
    ".claude",
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "build",
    "dist",
    ".pytest_cache",
    "__pycache__",
    ".github",
    ".claude-plugin",
}


def is_excluded(rel_path: Path) -> bool:
    """Check if a relative path should be excluded from sync."""
    if rel_path.name in EXCLUDED_FILENAMES:
        return True
    for part in rel_path.parts:
        if part in EXCLUDED_DIRS:
            return True
    return False


# ── Path flattening ──────────────────────────────────────────────

def flatten_path(rel_path: Path) -> Path:
    """Flatten multi-level directories into single-level with hyphens.

    Rules:
      - Root files: unchanged (README.md → README.md)
      - Single-level dir: unchanged (docs/file.md → docs/file.md)
      - Multi-level dirs: join with hyphen (a/b/c/file.md → a-b-c/file.md)
    """
    parts = rel_path.parts
    if len(parts) <= 2:
        # Root file or single-level dir — keep as-is
        return rel_path
    # Multi-level: join parent dirs with hyphen
    dir_parts = parts[:-1]
    filename = parts[-1]
    flat_dir = "-".join(dir_parts)
    return Path(flat_dir) / filename


# ── Auto-detection ───────────────────────────────────────────────

def detect_project_name(project_dir: Path) -> str:
    """Detect project name from git remote or directory name."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Handle both https and ssh URLs
            name = url.rstrip("/").rsplit("/", 1)[-1]
            if name.endswith(".git"):
                name = name[:-4]
            if name:
                return name
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return project_dir.name


def detect_vault_dir() -> Path | None:
    """Auto-detect Obsidian vault from config file."""
    if platform.system() == "Windows":
        config_path = Path(os.environ.get("APPDATA", "")) / "obsidian" / "obsidian.json"
    elif platform.system() == "Darwin":
        config_path = Path.home() / "Library" / "Application Support" / "obsidian" / "obsidian.json"
    else:
        config_path = Path.home() / ".config" / "obsidian" / "obsidian.json"

    if not config_path.exists():
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    vaults = config.get("vaults", {})
    if not vaults:
        return None

    # Prefer the open vault, otherwise pick the most recently used
    best = None
    best_ts = 0
    for vault_info in vaults.values():
        path = vault_info.get("path")
        if not path:
            continue
        if vault_info.get("open"):
            return Path(path)
        ts = vault_info.get("ts", 0)
        if ts > best_ts:
            best_ts = ts
            best = path

    return Path(best) if best else None


def check_symlink_capability() -> bool:
    """Test if symlinks work on this system."""
    tmp_dir = Path(tempfile.gettempdir())
    target = tmp_dir / ".obsidian_sync_symlink_test"
    link = tmp_dir / ".obsidian_sync_symlink_test_link"
    try:
        target.write_text("test")
        if link.exists() or link.is_symlink():
            link.unlink()
        os.symlink(target, link)
        link.unlink()
        target.unlink()
        return True
    except OSError:
        if target.exists():
            target.unlink()
        if link.exists() or link.is_symlink():
            link.unlink()
        return False


# ── Manifest ─────────────────────────────────────────────────────

def load_manifest(manifest_path: Path) -> dict:
    """Load sync manifest from vault."""
    if not manifest_path.exists():
        return {"files": {}, "mode": None, "last_sync": None}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupted manifest — back up and start fresh
        backup = manifest_path.with_suffix(".json.bak")
        shutil.copy2(manifest_path, backup)
        print(f"  Warning: manifest corrupted, backed up to {backup.name}")
        return {"files": {}, "mode": None, "last_sync": None}


def save_manifest(manifest_path: Path, manifest: dict):
    """Save sync manifest."""
    manifest["last_sync"] = datetime.now(timezone.utc).isoformat()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


# ── Scanning ─────────────────────────────────────────────────────

DEFAULT_EXTENSIONS = {".md", ".pdf"}


def scan_files(project_dir: Path, extensions: set[str] | None = None) -> list[Path]:
    """Scan project for files matching extensions, applying exclusion rules.

    Returns list of relative paths.
    """
    exts = extensions or DEFAULT_EXTENSIONS
    files = []
    for path in project_dir.rglob("*"):
        if path.suffix.lower() not in exts:
            continue
        rel = path.relative_to(project_dir)
        if not is_excluded(rel) and not path.is_symlink():
            files.append(rel)
    files.sort()
    return files


# ── Sync actions ─────────────────────────────────────────────────

def compute_actions(
    md_files: list[Path],
    project_dir: Path,
    vault_project_dir: Path,
    mode: str,
    manifest: dict,
) -> list[dict]:
    """Compute sync actions for each file.

    Returns list of action dicts with keys:
      rel_path, flat_path, action, source, dest
    """
    actions = []
    manifest_files = manifest.get("files", {})

    for rel_path in md_files:
        flat_path = flatten_path(rel_path)
        source = project_dir / rel_path
        dest = vault_project_dir / flat_path
        rel_key = str(rel_path)

        if dest.exists():
            # Compare modification times
            src_mtime = source.stat().st_mtime
            dst_mtime = dest.stat().st_mtime
            if src_mtime <= dst_mtime and rel_key in manifest_files:
                actions.append({
                    "rel_path": rel_path,
                    "flat_path": flat_path,
                    "action": "skip",
                    "reason": "up to date",
                })
                continue
            action_type = "update"
        else:
            action_type = "new"

        actions.append({
            "rel_path": rel_path,
            "flat_path": flat_path,
            "action": action_type,
            "source": source,
            "dest": dest,
        })

    return actions


def execute_actions(
    actions: list[dict],
    project_dir: Path,
    mode: str,
    manifest: dict,
):
    """Execute computed sync actions."""
    synced = 0
    skipped = 0
    errors = 0

    for act in actions:
        if act["action"] == "skip":
            skipped += 1
            continue

        source: Path = act["source"]
        dest: Path = act["dest"]
        rel_path = act["rel_path"]

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)

            if mode == "symlink":
                # Move file to vault, create symlink at original location
                shutil.copy2(source, dest)
                source.unlink()
                os.symlink(dest, source)
            else:
                # Copy mode: just copy to vault
                shutil.copy2(source, dest)

            # Update manifest
            manifest.setdefault("files", {})[str(rel_path)] = {
                "flat_path": str(act["flat_path"]),
                "synced_at": datetime.now(timezone.utc).isoformat(),
                "mode": mode,
            }
            synced += 1

        except PermissionError:
            print(f"  ERROR: Permission denied: {rel_path}")
            errors += 1
        except OSError as e:
            print(f"  ERROR: {rel_path}: {e}")
            errors += 1

    return synced, skipped, errors


# ── Display ──────────────────────────────────────────────────────

def print_actions(actions: list[dict], mode: str):
    """Print action table."""
    new_count = sum(1 for a in actions if a["action"] == "new")
    update_count = sum(1 for a in actions if a["action"] == "update")
    skip_count = sum(1 for a in actions if a["action"] == "skip")

    print(f"\n  Mode: {mode}")
    print(f"  New: {new_count}  Update: {update_count}  Skip: {skip_count}")
    print()

    actionable = [a for a in actions if a["action"] != "skip"]
    if not actionable:
        print("  Nothing to sync — all files up to date.")
        return

    # Print table
    print(f"  {'Action':<8} {'Source':<45} {'→ Vault'}")
    print(f"  {'─' * 8} {'─' * 45} {'─' * 35}")
    for act in actionable:
        tag = "NEW" if act["action"] == "new" else "UPDATE"
        print(f"  {tag:<8} {str(act['rel_path']):<45} {str(act['flat_path'])}")

    print()


# ── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sync project documentation files to Obsidian vault"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=None,
        help="Project directory (default: current directory)",
    )
    parser.add_argument(
        "--vault-dir",
        type=Path,
        default=None,
        help="Obsidian vault directory (default: auto-detect from Obsidian config)",
    )
    parser.add_argument(
        "--project-name",
        default=None,
        help="Project name in vault (default: from git remote or dir name)",
    )
    parser.add_argument(
        "--mode",
        choices=["symlink", "copy"],
        default="symlink",
        help="Sync mode (default: symlink)",
    )
    parser.add_argument(
        "--extensions",
        default=None,
        help="Comma-separated file extensions to sync (default: .md,.pdf)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without executing",
    )
    args = parser.parse_args()

    # ── Resolve project dir
    project_dir = (args.project_dir or Path.cwd()).resolve()
    if not project_dir.is_dir():
        print(f"ERROR: Project directory not found: {project_dir}")
        sys.exit(1)

    # ── Resolve vault dir
    vault_dir = args.vault_dir
    if vault_dir is None:
        vault_dir = detect_vault_dir()
        if vault_dir is None:
            print("ERROR: Cannot auto-detect Obsidian vault.")
            print("  Obsidian config not found or no vaults configured.")
            print("  Use --vault-dir to specify manually.")
            sys.exit(1)
    vault_dir = vault_dir.resolve()
    if not vault_dir.is_dir():
        print(f"ERROR: Vault directory not found: {vault_dir}")
        sys.exit(1)

    # ── Check symlink capability
    if args.mode == "symlink":
        if not check_symlink_capability():
            print("ERROR: Symlink not available on this system.")
            print()
            print("  To enable symlinks on Windows:")
            print("    Settings → Privacy & Security → For developers → Developer Mode: ON")
            print()
            print("  Or use copy mode: --mode copy")
            sys.exit(1)

    # ── Resolve project name
    project_name = args.project_name or detect_project_name(project_dir)
    vault_project_dir = vault_dir / "projects" / project_name

    # ── Parse extensions
    if args.extensions:
        extensions = {
            ext.strip() if ext.strip().startswith(".") else f".{ext.strip()}"
            for ext in args.extensions.split(",")
        }
    else:
        extensions = DEFAULT_EXTENSIONS

    # ── Print header
    print(f"\n  obsidian-sync")
    print(f"  {'─' * 50}")
    print(f"  Project:  {project_dir}")
    print(f"  Name:     {project_name}")
    print(f"  Vault:    {vault_project_dir}")
    print(f"  Mode:     {args.mode}")
    print(f"  Types:    {', '.join(sorted(extensions))}")

    # ── Scan files
    files = scan_files(project_dir, extensions)
    print(f"  Found:    {len(files)} files")

    if not files:
        print("\n  No files to sync.")
        return

    # ── Load manifest & compute actions
    manifest_path = vault_project_dir / ".sync-manifest.json"
    manifest = load_manifest(manifest_path)
    actions = compute_actions(files, project_dir, vault_project_dir, args.mode, manifest)

    # ── Display actions
    print_actions(actions, args.mode)

    if args.dry_run:
        print("  [dry-run] No changes made.")
        return

    # ── Execute
    actionable = [a for a in actions if a["action"] != "skip"]
    if not actionable:
        return

    manifest["mode"] = args.mode
    manifest["project_dir"] = str(project_dir)
    synced, skipped, errors = execute_actions(actions, project_dir, args.mode, manifest)

    # ── Save manifest
    save_manifest(manifest_path, manifest)

    # ── Summary
    print(f"  Done: {synced} synced, {skipped} skipped, {errors} errors")
    if args.mode == "symlink":
        print(f"  Symlinks created in project, files moved to vault.")
    else:
        print(f"  Files copied to vault, originals unchanged.")
    print()


if __name__ == "__main__":
    main()
