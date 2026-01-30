---
name: obsidian-file-recovery-extraction
description: Extract Obsidian File Recovery snapshots from Chrome IndexedDB using CCL Chromium Reader
tags: [obsidian, data-recovery, leveldb, electron, forensics]
---

# Obsidian File Recovery Data Extraction

When Obsidian vault files are corrupted or lost, the File Recovery core plugin maintains historical snapshots in Chrome/Electron IndexedDB format.

## The Problem

Standard tools cannot read Obsidian's backup data:
- Data stored in IndexedDB at `~/Library/Application Support/obsidian/IndexedDB/app_obsidian.md_0.indexeddb.leveldb/`
- Chrome/Electron uses V8/Blink serialization, NOT standard LevelDB
- Node.js `level`, `classic-level`, Python `plyvel` all fail
- Raw `strings` extraction produces mangled text

## The Solution: CCL Chromium Reader

Use the forensics tool that properly deserializes Chrome IndexedDB:

```bash
# Install
git clone https://github.com/cclgroupltd/ccl_chromium_reader /tmp/ccl_chromium_reader

# CRITICAL: Close Obsidian first (database locks!)

# Copy DB to clean location
cp -r "~/Library/Application Support/obsidian/IndexedDB/app_obsidian.md_0.indexeddb.leveldb" /tmp/obsidian-db-clean/
```

## Extraction Script

```python
import sys
sys.path.insert(0, '/tmp/ccl_chromium_reader')

from ccl_chromium_reader import ccl_chromium_indexeddb

LEVELDB_PATH = "/tmp/obsidian-db-clean/app_obsidian.md_0.indexeddb.leveldb"
BLOB_PATH = "~/Library/Application Support/obsidian/IndexedDB/app_obsidian.md_0.indexeddb.blob"

wrapper = ccl_chromium_indexeddb.WrappedIndexDB(LEVELDB_PATH, BLOB_PATH)

# Find backup database (name contains "backup")
for db_id in wrapper.database_ids:
    if 'backup' in db_id.name:
        backup_db = wrapper[db_id.dbid_no]
        break

# Access "backups" object store
backups_store = backup_db["backups"]

# Each record has: path, ts (timestamp), data (content)
for record in backups_store.iterate_records():
    val = record.value
    path = val.get('path', '')
    ts = val.get('ts', 0)
    data = val.get('data', '')
```

## CRITICAL: Keep Best Version, Not Latest

File Recovery keeps multiple snapshots. If a file was emptied/corrupted later, the **latest** backup has empty data. Always keep the **longest content version**:

```python
best_backups = {}  # path -> {data, len}

for record in backups_store.iterate_records():
    path = val.get('path', '')
    data = val.get('data', '')
    data_len = len(str(data)) if data else 0

    # Keep LONGEST, not latest
    if path not in best_backups or data_len > best_backups[path]['len']:
        best_backups[path] = {'data': data, 'len': data_len}
```

## Key Locations (macOS)

| Component | Path |
|-----------|------|
| LevelDB | `~/Library/Application Support/obsidian/IndexedDB/app_obsidian.md_0.indexeddb.leveldb/` |
| Blob storage | `~/Library/Application Support/obsidian/IndexedDB/app_obsidian.md_0.indexeddb.blob` |
| Database name | Contains "backup" (e.g., `d4fd49d66ec66ec4-backup`) |
| Object store | `backups` |
| Record fields | `path`, `ts`, `data` |

## Why Standard Tools Fail

Chrome IndexedDB uses V8's internal serialization:
- Type markers for objects, arrays, strings
- Variable-length integer encoding
- Blob references for large data
- Custom Blink object serialization

The `strings` command extracts readable portions but mangles:
- Non-ASCII characters
- Markdown formatting
- YAML frontmatter

## Restoration Script

```python
import os

VAULT_PATH = "/path/to/obsidian/vault"

for rel_path, info in best_backups.items():
    data = info.get('data', '')
    if len(str(data)) < 50:
        continue  # Skip empty

    full_path = os.path.join(VAULT_PATH, rel_path)

    # Only restore if file needs it
    if os.path.exists(full_path):
        with open(full_path) as f:
            current = f.read()
        if len(current) > 100 and 'needs-regeneration' not in current:
            continue  # Already good

    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        f.write(str(data))
```

## References

- CCL Chromium Reader: https://github.com/cclgroupltd/ccl_chromium_reader
- Chrome IndexedDB format in Chromium source
