---
name: obsidian-sync
description: Sync project documentation (.md, .pdf) to Obsidian vault
---

Run the obsidian-sync script to sync project documentation files to the user's Obsidian vault.

## Steps

1. First run in **dry-run** mode to preview:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-sync/scripts/sync_to_obsidian.py" --dry-run $ARGUMENTS
   ```

2. Show the preview output to the user. If there are files to sync, ask the user to confirm.

3. If confirmed, run without `--dry-run`:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/obsidian-sync/scripts/sync_to_obsidian.py" $ARGUMENTS
   ```

4. Report the results.

## Available Options

Users can pass these as arguments:
- `--mode copy` — use copy instead of symlink
- `--extensions .md,.pdf,.txt` — customize file types
- `--project-name NAME` — override project name
- `--vault-dir PATH` — override vault path
- `--project-dir PATH` — override project path
