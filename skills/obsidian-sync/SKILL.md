---
name: obsidian-sync
description: >
  Sync project markdown documentation files to an Obsidian vault for unified knowledge management.
  This skill should be used when the user says "sync to obsidian", "obsidian sync",
  "同步到obsidian", "文档同步", "move docs to obsidian", "sync docs",
  or wants to organize project documentation in Obsidian.
---

# Obsidian Sync

Sync `.md` files from the current project to an Obsidian vault.

## Workflow

1. Run the sync script in **dry-run** mode first to preview:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-sync/scripts/sync_to_obsidian.py" --dry-run
   ```

2. Show the user the preview output and ask for confirmation.

3. If confirmed, run without `--dry-run`:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-sync/scripts/sync_to_obsidian.py"
   ```

4. Report the results.

## Modes

- **symlink** (default): Moves files to vault, creates symlinks in project. Requires Windows Developer Mode.
- **copy**: Copies files to vault, originals stay. Use `--mode copy`.

## Options

All parameters are auto-detected by default:

| Flag | Description | Default |
|------|-------------|---------|
| `--project-dir` | Project path | Current working directory |
| `--vault-dir` | Obsidian vault path | Auto-detect from Obsidian config |
| `--project-name` | Name in vault | From git remote or dir name |
| `--mode` | symlink / copy | symlink |
| `--dry-run` | Preview only | off |

## Notes

- Excludes: `CLAUDE.md`, `.claude/`, `.git/`, `node_modules/`, `venv/`, `build/`, `dist/`
- Multi-level paths are flattened: `a/b/c/file.md` → `a-b-c/file.md`
- A `.sync-manifest.json` tracks sync state in the vault
