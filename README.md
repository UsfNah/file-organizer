# File Organizer CLI (Python)

A lightweight, config-driven command-line tool that automatically sorts files in a directory into subfolders based on file extension. Built with Python's standard library — no external dependencies required.

---

## Features

- **Extension-based sorting** — maps file types to named folders via `config.json`
- **Dry-run mode** — preview all planned moves without touching the filesystem
- **Auto-generated config** — creates a sensible `config.json` on first run if none exists
- **Rotating log file** — all actions written to `Organizer.log` (max 5 MB, 3 backups)
- **Duplicate handling** — renames conflicting files as `file (2).ext`, `file (3).ext`, etc.
- **Edge case safe** — handles files with no extension, locked/in-use files, and missing source directories
- **Cross-platform** — works on Windows, macOS, and Linux

---

## Requirements

- Python 3.8+
- No third-party packages (standard library only)

---

## Installation

```bash
git clone https://github.com/UsfNah/file-organizer.git
cd file-organizer
```

No `pip install` needed. Optionally create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

---

## Usage

### Basic — organize current directory

```bash
python file_organiser.py
```

### Specify a source folder

```bash
python file_organiser.py --source "~/Downloads"
```

### Preview changes without moving anything (dry-run)

```bash
python file_organiser.py --source "~/Downloads" --dry-run
```

### Use a custom config file

```bash
python file_organiser.py --source "/data/inbox" --config "./my_config.json"
```

### Verbose debug output

```bash
python file_organiser.py --source "~/Downloads" --dry-run --verbose --log_level DEBUG
```

### Full argument reference

| Argument | Short | Default | Description |
|---|---|---|---|
| `--source` | `-s` | From config | Source directory to organize |
| `--config` | `-c` | `config.json` | Path to the JSON config file |
| `--dry_run` | `-n` | `False` | Simulate moves; no files are changed |
| `--verbose` | `-v` | `False` | Print per-file details to the console |
| `--log_level` | `-l` | `INFO` | Logging verbosity: `DEBUG` `INFO` `WARNING` `ERROR` `CRITICAL` |

---

## Configuration (`config.json`)

If `config.json` is not found, the tool auto-generates one with sensible defaults. You can edit it at any time without touching the code.

```json
{
  "source": "./",
  "destination": "./organized",
  "extensions": {
    ".pdf": "Documents",
    ".docx": "Documents",
    ".txt": "Documents",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".mp4": "Videos",
    ".mkv": "Videos",
    ".mp3": "Audio",
    ".wav": "Audio",
    ".zip": "Archives",
    ".rar": "Archives",
    ".py": "Code",
    ".cpp": "Code",
    ".ipynb": "Code"
  },
  "others_folder": "Misc",
  "recursive": false
}
```

### Key descriptions

| Key | Type | Description |
|---|---|---|
| `source` | string | Directory to scan; relative or absolute path |
| `destination` | string | Base output directory; created automatically if missing |
| `extensions` | object | Maps file extension (with dot, lowercase) → subfolder name |
| `others_folder` | string | Destination folder for files with unrecognized or no extension |
| `recursive` | boolean | Reserved for v1.1 recursive mode (currently ignored) |

### Adding a custom extension mapping

```json
".xlsx": "Spreadsheets",
".pptx": "Presentations",
".svg":  "Images"
```

Paths in `source` and `destination` can be absolute (`/home/user/files`) or relative (`./inbox`).

---

## Examples

### Before

```
inbox/
├── report.pdf
├── photo.jpg
├── photo.jpg        ← duplicate
├── script.py
├── archive.zip
├── notes            ← no extension
└── video.mp4
```

### After running `python file_organiser.py --source ./inbox`

```
organized/
├── Documents/
│   └── report.pdf
├── Images/
│   ├── photo.jpg
│   └── photo (2).jpg
├── Code/
│   └── script.py
├── Archives/
│   └── archive.zip
├── Videos/
│   └── video.mp4
└── Misc/
    └── notes
```

---

## Logging

All actions are written to `Organizer.log` in the directory where the script is run.

**Log format:**
```
%(asctime)s - %(levelname)s - %(message)s
```

**Example entries:**

```
2026-04-25 10:00:01,123 - INFO - source: /home/user/inbox, destination: ./organized, dry_run: False, log_level: INFO
2026-04-25 10:00:01,456 - INFO - Moved: /home/user/inbox/report.pdf -> /home/user/organized/Documents/report.pdf
2026-04-25 10:00:01,789 - INFO - [DRY-RUN] Would move: /tmp/photo.jpg -> /tmp/organized/Images/photo.jpg
2026-04-25 10:00:02,012 - DEBUG - Resolved duplicate: photo.jpg -> photo (2).jpg
2026-04-25 10:00:02,345 - ERROR - Permission denied moving /locked/file.docx -> /organized/Documents/file.docx
2026-04-25 10:00:03,000 - INFO - Processed: 7 files, Moved: 6, Errors: 1
```

**Log rotation:** The log file rotates at 5 MB and keeps up to 3 backups (`Organizer.log.1`, `Organizer.log.2`, `Organizer.log.3`).

**Log levels:**

| Level | What is logged |
|---|---|
| `DEBUG` | Duplicate resolution, destination mapping details |
| `INFO` | Planned moves, actual moves, run summary |
| `WARNING` | Non-fatal anomalies (e.g., too many duplicates) |
| `ERROR` | Per-file failures (permission denied, OS errors) |
| `CRITICAL` | Fatal errors (missing source, invalid config) |

---

## Troubleshooting

### Permission denied
**Log:** `ERROR - Permission denied moving /path/file.ext -> /dest/file.ext`  
**Fix:** Ensure the source file is not open in another application and that you have write permissions on the destination directory.

### Config JSON error
**Log:** `Invalid JSON in config.json: Line X, Col Y: ...`  
**Fix:** Validate your `config.json` using a linter (e.g., [jsonlint.com](https://jsonlint.com)). Check for trailing commas or missing quotes.

### Source path not found
**Log:** `CRITICAL - ...`  
**Fix:** Verify the path passed to `--source` exists and is a directory, not a file.

### Extensions not matching
**Cause:** Extension keys in `config.json` must be lowercase and start with a dot (e.g., `.PDF` will not match — use `.pdf`).

---

## Roadmap (v1.1+)

- [ ] **Recursive mode** — organize files in subdirectories with `--recursive`
- [ ] **Undo support** — `--undo` flag to reverse the last session using `undo.jsonl`
- [ ] **Age-based filtering** — `--older-than DAYS` / `--newer-than DAYS` flags
- [ ] **Colored console output** — green for moved, yellow for skipped, red for errors
- [ ] **Regex/prefix rules** — match files by name pattern, not just extension

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

Built by Yousef Elnahrawy · [GitHub](**https://github.com/UsfNah**) 
