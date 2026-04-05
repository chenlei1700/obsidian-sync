# obsidian-sync

**A Claude Code plugin that syncs project documentation to your Obsidian vault — one command, zero config.**

[中文文档](README-zh.md)

---

## The Problem

You clone repos. Each has scattered documentation — `.md` files, `.pdf` references — buried in nested directories. You want to read and search them in one place, but they live across dozens of project folders.

**obsidian-sync** moves all project documentation into your Obsidian vault with a single command, keeping them browsable both in Obsidian and in the original project.

## How It Works

```
your-project/                          Obsidian vault/projects/your-project/
  ai/gnn/docs/SETUP.md      ──→         ai-gnn-docs/SETUP.md
  docs/design.md             ──→         docs/design.md
  README.md                  ──→         README.md
```

1. **Scans** the project for all `.md` and `.pdf` files (configurable)
2. **Flattens** deep directory paths into readable single-level folders (`a/b/c/file.md` → `a-b-c/file.md`)
3. **Moves** files to vault and creates **symlinks** in the original locations (or copies, your choice)
4. **Tracks** sync state via manifest — re-run safely anytime

## Quick Start

### Install

```bash
claude plugins add github.com/chenlei1700/obsidian-sync
```

### Use

In any project directory with Claude Code:

```bash
# Preview what will be synced (recommended first time)
/obsidian-sync --dry-run

# Sync with symlinks (default)
/obsidian-sync

# Sync with copy mode (no special permissions needed)
/obsidian-sync --mode copy
```

Or run the script directly:

```bash
python sync_to_obsidian.py --dry-run
python sync_to_obsidian.py
```

**Zero configuration needed** — the script auto-detects:
- Project directory (current working directory)
- Project name (from `git remote` or folder name)
- Obsidian vault location (from Obsidian's config file)

## Sync Modes

| Mode | How it works | Requirements |
|------|-------------|--------------|
| **symlink** (default) | Moves files to vault, creates symlinks in project | Windows: Developer Mode ON |
| **copy** | Copies files to vault, originals unchanged | None |

In symlink mode, files are transparent — git, editors, and code references all work as before. The file just physically lives in your vault.

If symlinks aren't available, the script tells you how to enable them and exits. No silent fallbacks.

## Options

All optional — zero arguments works out of the box.

| Flag | Description | Default |
|------|-------------|---------|
| `--project-dir PATH` | Project root directory | Current directory |
| `--vault-dir PATH` | Obsidian vault path | Auto-detect |
| `--project-name NAME` | Project folder name in vault | From git remote / dir name |
| `--mode {symlink,copy}` | Sync strategy | `symlink` |
| `--extensions EXTS` | File types to sync (comma-separated) | `.md,.pdf` |
| `--dry-run` | Preview without making changes | Off |

## What Gets Synced

**Included:** All `.md` and `.pdf` files by default. Customize with `--extensions`.

**Excluded automatically:**
- `CLAUDE.md` — Claude Code config
- `.claude/`, `.git/`, `.github/`
- `node_modules/`, `venv/`, `.venv/`, `env/`
- `build/`, `dist/`, `__pycache__/`, `.pytest_cache/`

## Path Flattening

Deep directory nesting is collapsed into flat, readable folder names:

| Original path | In vault |
|---------------|----------|
| `README.md` | `README.md` |
| `docs/guide.md` | `docs/guide.md` |
| `src/api/docs/SETUP.md` | `src-api-docs/SETUP.md` |
| `a/b/c/d/notes.md` | `a-b-c-d/notes.md` |

Single-level directories are kept as-is. Only multi-level paths get flattened.

## Vault Structure

After syncing multiple projects:

```
Your Obsidian Vault/
  projects/
    my-app/
      .sync-manifest.json
      README.md
      docs/
      src-components-docs/
    another-repo/
      .sync-manifest.json
      README.md
      api-docs/
```

Each project is isolated in its own folder. The `.sync-manifest.json` tracks what was synced and when.

## Platform Support

| Platform | symlink mode | copy mode |
|----------|-------------|-----------|
| Windows (Developer Mode ON) | Yes | Yes |
| Windows (Developer Mode OFF) | No (clear error message) | Yes |
| macOS | Yes | Yes |
| Linux | Yes | Yes |

## Requirements

- Python 3.10+
- Obsidian installed (for auto-detection of vault path)
- Claude Code (for plugin usage) — or run the script standalone

## License

MIT
