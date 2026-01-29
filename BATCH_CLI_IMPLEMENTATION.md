# CLI Batch Processing Implementation Summary

## Overview

Implemented a complete CLI batch processing mode for AI Agent Guards that shares code with the UI. This allows scanning multiple session files in batch, generating markdown reports, and integrating with CI/CD pipelines.

**Date:** 2026-01-29

---

## ✅ What Was Implemented

### 1. Core Shared Logic (`multi_agent_demo/core/`)

**NEW FILES:**
- `__init__.py` - Module exports
- `scanner_runner.py` - Shared scanner execution logic

**Purpose:** Extract scanner execution into reusable functions that both UI and CLI can use.

**Key Functions:**
- `run_scanners_on_session()` - Run scanners on single session
- `aggregate_results()` - Aggregate statistics across multiple sessions

### 2. Report Generation (`multi_agent_demo/reports/`)

**NEW FILES:**
- `__init__.py` - Module exports
- `markdown_generator.py` - Markdown report formatting

**Purpose:** Generate copyable markdown reports for CLI output.

**Features:**
- Overall statistics (total, safe, unsafe)
- Per-scanner breakdown (blocks, warnings, safe)
- Detailed results for sessions with issues
- Smart filtering (only shows problematic sessions)

### 3. CLI Entry Point (`multi_agent_demo/cli.py`)

**NEW FILE:** `cli.py`

**Purpose:** Command-line interface for batch processing.

**Features:**
- Argument parsing (`-d` directory, `-s` scanners, `-o` output, `--show-safe`)
- Progress bar with color-coded status
- Batch session processing with error handling
- Console and file output
- ANSI color support for terminal

**Usage:**
```bash
python -m multi_agent_demo.cli -d ./sessions
python -m multi_agent_demo.cli -d ./sessions -s AlignmentCheck FactsChecker
python -m multi_agent_demo.cli -d ./sessions -o report.md
```

### 4. Testing Scripts

**NEW FILES:**
- `test_batch_cli.py` - Manual test (creates sample sessions)
- `test_batch_cli_automated.py` - Automated CI/CD test

**Purpose:** Verify CLI works correctly.

### 5. Documentation

**NEW FILES:**
- `BATCH_CLI_GUIDE.md` - Comprehensive usage guide

**UPDATED FILES:**
- `README.md` - Added CLI sections
  - Updated Overview (3 modes: UI, CLI, Deviations)
  - Added "Batch Processing CLI" feature section
  - Added CLI usage examples
  - Added core modules documentation
- `CLAUDE.md` - Added CLI commands
  - Updated running commands
  - Updated module structure

---

## 📊 Architecture

### Code Sharing Between UI and CLI

```
┌─────────────────────────────────────────────┐
│            User Interfaces                  │
├──────────────────┬──────────────────────────┤
│   app.py (UI)    │   cli.py (CLI)          │
└────────┬─────────┴──────────┬───────────────┘
         │                    │
         │  ┌─────────────────┴───────────┐
         │  │  core/scanner_runner.py     │
         │  │  - run_scanners_on_session()│
         └──┤  - aggregate_results()      │
            └─────────────┬───────────────┘
                          │
            ┌─────────────┴───────────────┐
            │     firewall.py             │
            │  - run_scanner_tests()      │
            └─────────────┬───────────────┘
                          │
            ┌─────────────┴───────────────┐
            │     scanners/               │
            │  - PromptGuard              │
            │  - AlignmentCheck           │
            │  - FactsChecker             │
            │  - DataDisclosureGuard      │
            └─────────────────────────────┘
```

**Benefits:**
- Single source of truth for scanner logic
- Changes automatically apply to both UI and CLI
- Consistent results across modes
- Easier maintenance

---

## 🎯 Use Cases

### 1. CI/CD Integration
```bash
# In GitHub Actions
python -m multi_agent_demo.cli -d ./test_sessions -o scan_report.md
```

### 2. Regression Testing
```bash
# Before deployment
python -m multi_agent_demo.cli -d ./baseline_sessions -o before.md
# After changes
python -m multi_agent_demo.cli -d ./baseline_sessions -o after.md
diff before.md after.md
```

### 3. Large-Scale Analysis
```bash
# Process production logs
python -m multi_agent_demo.cli -d ./prod_sessions -o analysis.md
```

### 4. Compliance Reporting
```bash
# Generate monthly report
python -m multi_agent_demo.cli -d ./sessions/2026-01 -o report.md --show-safe
```

---

## 📋 File Changes Summary

### Created Files (9 new files)

```
multi_agent_demo/
├── core/
│   ├── __init__.py                    # NEW
│   └── scanner_runner.py              # NEW
├── reports/
│   ├── __init__.py                    # NEW
│   └── markdown_generator.py          # NEW
└── cli.py                             # NEW

# Root directory
├── test_batch_cli.py                  # NEW
├── test_batch_cli_automated.py        # NEW
├── BATCH_CLI_GUIDE.md                 # NEW
└── BATCH_CLI_IMPLEMENTATION.md        # NEW (this file)
```

### Updated Files (2 files)

```
├── README.md                          # UPDATED
│   - Added CLI overview
│   - Added batch processing features
│   - Added CLI usage examples
│   - Added core modules documentation
│
└── CLAUDE.md                          # UPDATED
    - Added CLI commands
    - Updated module structure
```

---

## 🧪 Testing

### Manual Test

```bash
# Create test sessions
python test_batch_cli.py

# Run CLI on test sessions
python -m multi_agent_demo.cli -d /tmp/cli_test_sessions_XXXXX
```

### Automated Test

```bash
# Run automated test
python test_batch_cli_automated.py

# Expected: ✅ ALL CHECKS PASSED
```

### CI/CD Integration

Add to `.github/workflows/test.yml`:
```yaml
- name: Test CLI batch processing
  run: python test_batch_cli_automated.py
```

---

## 📖 Example Output

### Console

```
================================================================================
🛡️  AI AGENT GUARDS - BATCH SCANNER
================================================================================

📂 Scanning directory: ./sessions
✅ Found 51 session file(s)

🔍 Enabled scanners: PromptGuard, AlignmentCheck, FactsChecker

⚙️  Processing sessions...

[████████████████████████████████████████] 100% | 51/51 | 🟢 session_051.json

✅ Processing complete!

================================================================================
📊 SUMMARY
================================================================================

Total Sessions: 51
Safe Sessions: 35 ✅
Sessions with Issues: 16 ⚠️

Total Blocks: 6 🚫
Total Warnings: 43 ⚠️
Total Safe: 198 ✅
```

### Markdown Report

````markdown
# 🛡️ AI Agent Guards - Batch Scan Report

## 📊 Overall Statistics

- **Total Sessions Scanned:** 51
- **Safe Sessions:** 35 ✅
- **Sessions with Issues:** 16 ⚠️

**Accumulated Counts:**
- 🚫 **Blocks:** 6
- ⚠️ **Warnings:** 43
- ✅ **Safe:** 198

## 🔍 Results by Scanner

### AlignmentCheck

| Metric | Count |
|--------|-------|
| 🚫 Blocks | 3 |
| ⚠️ Warnings | 0 |
| ✅ Safe | 48 |

## 📋 Detailed Results per Session

_Only showing sessions with issues._

### Session 5: `session_005.json`

**Overall Decision:** 🔴 BLOCK

**Scanner Results:**

- **AlignmentCheck:** 🔴 BLOCK
  - Total: 4 | Safe: 2 | Warnings: 0 | Blocks: 2
````

---

## 🔧 Configuration

### Session JSON Format

```json
{
  "session_id": "session_001",
  "purpose": "Banking assistant",
  "messages": [
    {"type": "user", "content": "What's my balance?"},
    {"type": "assistant", "content": "Your balance is $1,250."}
  ]
}
```

### CLI Arguments

| Argument | Required | Description | Example |
|----------|----------|-------------|---------|
| `-d, --directory` | Yes | Directory with JSON files | `-d ./sessions` |
| `-s, --scanners` | No | Scanners to run (default: all) | `-s AlignmentCheck FactsChecker` |
| `-o, --output` | No | Output file (default: console) | `-o report.md` |
| `--show-safe` | No | Show safe session details | `--show-safe` |

### Available Scanners

- `PromptGuard` - Malicious prompts/injections (BLOCK/WARNING/SAFE)
- `AlignmentCheck` - Goal hijacking/drift (BLOCK/SAFE)
- `FactsChecker` - Contradictions/ungrounded (BLOCK/WARNING/SAFE)
- `DataDisclosureGuard` - PII disclosure (BLOCK/WARNING/SAFE)

---

## 🚀 Next Steps

### For Users

1. **Try the CLI:**
   ```bash
   python test_batch_cli.py  # Create samples
   python -m multi_agent_demo.cli -d /tmp/cli_test_sessions_XXXXX
   ```

2. **Read the guide:**
   See [BATCH_CLI_GUIDE.md](./BATCH_CLI_GUIDE.md)

3. **Integrate with CI/CD:**
   Add to your pipeline for automated scanning

### For Developers

1. **Test the implementation:**
   ```bash
   python test_batch_cli_automated.py
   ```

2. **Extend functionality:**
   - Add new scanners → automatically available in CLI
   - Modify report format → edit `markdown_generator.py`
   - Add custom aggregations → edit `scanner_runner.py`

3. **Update CI/CD:**
   - Add `test_batch_cli_automated.py` to GitHub Actions

---

## ✨ Key Features

1. **Shared Code:** UI and CLI use same scanner logic
2. **Smart Filtering:** Only shows sessions with issues
3. **Progress Display:** Real-time colored progress bar
4. **Markdown Reports:** Copyable format for documentation
5. **Flexible Scanner Selection:** Choose which scanners to run
6. **Batch Processing:** Process hundreds of sessions at once
7. **CI/CD Ready:** Exit codes and file output for automation
8. **Detailed Statistics:** Per-scanner and per-session breakdowns

---

## 📚 Documentation

- **[BATCH_CLI_GUIDE.md](./BATCH_CLI_GUIDE.md)** - Complete usage guide
- **[README.md](./README.md)** - Main documentation
- **[CLAUDE.md](./CLAUDE.md)** - Development guide

---

## 🎉 Summary

**What was requested:**
- CLI batch processing for multiple session files
- Shared code between UI and CLI
- Progress display
- Markdown reports with statistics
- CI/CD testing
- README updates

**What was delivered:**
- ✅ Complete CLI implementation with all requested features
- ✅ Shared core logic (`scanner_runner.py`)
- ✅ Markdown report generator
- ✅ Progress bar with color-coded status
- ✅ Manual and automated tests
- ✅ Comprehensive documentation (README, CLAUDE.md, BATCH_CLI_GUIDE.md)
- ✅ Smart filtering (only shows sessions with issues)
- ✅ Flexible scanner selection
- ✅ File and console output

**Bonus features:**
- ANSI color support for better terminal UX
- Recursive directory scanning
- Error handling and graceful failures
- Example use cases and integration patterns
- Programmatic usage examples
