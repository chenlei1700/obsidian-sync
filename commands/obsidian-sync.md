---
name: obsidian-sync
description: Sync project documentation (.md, .pdf) to Obsidian vault
---

# /obsidian-sync

Sync project documentation files to the user's Obsidian vault for unified knowledge management.

The sync script is located at `D:\Obsidian\obsidian-sync\skills\obsidian-sync\scripts\sync_to_obsidian.py`.

## Steps

1. Run the sync script directly (no confirmation needed):
   ```bash
   python "D:/Obsidian/obsidian-sync/skills/obsidian-sync/scripts/sync_to_obsidian.py" $ARGUMENTS
   ```

2. Report the results.

## Available Options

Users can pass these as arguments:
- `--mode copy` — use copy instead of symlink
- `--extensions .md,.pdf,.txt` — customize file types (default: .md,.pdf)
- `--project-name NAME` — override project name
- `--vault-dir PATH` — override vault path
- `--project-dir PATH` — override project path
