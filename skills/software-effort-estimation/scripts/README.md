# Effort Estimation Data Collection Scripts

Automated scripts to collect metrics for software effort estimation analysis.

## Quick Start

Run all collection scripts at once:

```bash
cd /path/to/repository
./collect_all_metrics.sh .
```

This will create an `effort_estimation_output` directory with all collected data.

## Individual Scripts

### 1. collect_git_stats.sh

Collects git repository statistics including commits, contributors, timeline, and activity patterns.

**Usage:**

```bash
./collect_git_stats.sh [repository_path] [output_file]
```

**Output:** Text file with git statistics

**Example:**

```bash
./collect_git_stats.sh /path/to/repo git_stats.txt
```

### 2. collect_code_metrics.sh

Analyzes codebase using `cloc` (Count Lines of Code) to separate production code, test code, and
generate detailed metrics.

**Prerequisites:** `cloc` must be installed

- macOS: `brew install cloc`
- Linux: `apt-get install cloc`

**Usage:**

```bash
./collect_code_metrics.sh [repository_path] [output_dir]
```

**Output:** Multiple files in output directory:

- `cloc_full.json` - Complete analysis in JSON format
- `cloc_summary.txt` - Human-readable summary
- `production_code.txt` - Production code only
- `test_code.txt` - Test code only
- `summary.txt` - Quick statistics

**Example:**

```bash
./collect_code_metrics.sh /path/to/repo metrics
```

### 3. collect_infrastructure.sh

Inventories infrastructure components including AWS CDK resources, Kubernetes manifests, Docker
containers, and file types.

**Usage:**

```bash
./collect_infrastructure.sh [repository_path] [output_file]
```

**Output:** Text file with infrastructure inventory

**Example:**

```bash
./collect_infrastructure.sh /path/to/repo infrastructure.txt
```

### 4. collect_all_metrics.sh (Master Script)

Runs all three collection scripts in sequence and organizes output into a structured directory.

**Usage:**

```bash
./collect_all_metrics.sh [repository_path]
```

**Output:** `effort_estimation_output/` directory containing all metrics

**Example:**

```bash
./collect_all_metrics.sh /path/to/repo
```

## Output Structure

After running `collect_all_metrics.sh`:

```text
effort_estimation_output/
├── git_stats.txt              # Git repository statistics
├── infrastructure.txt         # Infrastructure inventory
└── metrics/
    ├── cloc_full.json        # Complete code metrics (JSON)
    ├── cloc_summary.txt      # Code metrics summary
    ├── production_code.txt   # Production code analysis
    ├── test_code.txt         # Test code analysis
    └── summary.txt           # Quick statistics
```

## Next Steps

After collecting metrics:

1. **Review the data** - Check all output files for accuracy
2. **Apply estimation models** - Use the data with the five models described in `SKILL.md`
3. **Calculate productivity** - Compare traditional estimates with actual effort
4. **Generate report** - Create comprehensive markdown report

See the main `SKILL.md` file for detailed instructions on applying estimation models and generating reports.

## Troubleshooting

### "cloc: command not found"

- Install cloc: `brew install cloc` (macOS) or `apt-get install cloc` (Linux)

### "Not a git repository"

- Ensure you're running scripts on a directory with a `.git` folder
- Check that the repository path is correct

### Scripts not executable

- Run: `chmod +x *.sh` in the scripts directory

### Date calculation errors

- Scripts handle both GNU date (Linux) and BSD date (macOS)
- If errors persist, check that `bc` is installed: `which bc`
