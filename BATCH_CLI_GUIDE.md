# CLI Batch Processing Guide

## Overview

The AI Agent Guards platform now supports **batch processing mode** via a command-line interface (CLI). This allows you to scan multiple session files at once, get aggregated statistics, and generate markdown reports.

**Key Benefits:**
- Process hundreds of sessions in one command
- CI/CD integration for automated testing
- Markdown reports for documentation
- Shared code with UI ensures consistency
- Smart filtering: only shows sessions with issues

---

## Quick Start

### 1. Basic Usage

Scan all JSON files in a directory:
```bash
python -m multi_agent_demo.cli -d ./sessions
```

### 2. Select Specific Scanners

```bash
python -m multi_agent_demo.cli -d ./sessions -s AlignmentCheck FactsChecker
```

### 3. Save Report to File

```bash
python -m multi_agent_demo.cli -d ./sessions -o report.md
```

### 4. Include Safe Sessions in Report

By default, only sessions with issues are detailed. To show all:
```bash
python -m multi_agent_demo.cli -d ./sessions --show-safe
```

---

## Available Scanners

| Scanner | What It Detects | Decisions |
|---------|----------------|-----------|
| **PromptGuard** | Malicious prompts and injections | BLOCK, WARNING, SAFE |
| **AlignmentCheck** | Goal hijacking and behavioral drift | BLOCK, SAFE _(no warnings)_ |
| **FactsChecker** | Contradictions and ungrounded claims | BLOCK, WARNING, SAFE |
| **DataDisclosureGuard** | PII disclosure issues | BLOCK, WARNING, SAFE |

**Note:** If you see "Total Warnings: 0", it's normal when running only AlignmentCheck, which doesn't produce warnings (only BLOCK or SAFE).

---

## Session JSON Format

The CLI supports **two formats**:

### Format 1: Langfuse Export Format (OpenOps)

```json
{
  "scenario_name": "environment_prod_0450c00c",
  "agent_purpose": "You are the OpenOps Agent, an AI assistant...",
  "messages": [
    {"type": "user", "content": "create a workflow that monitors price..."},
    {"type": "assistant", "content": "I'll help you create that workflow..."}
  ],
  "exported_at": "2026-01-26T19:06:23.108931+00:00",
  "format_version": "1.0"
}
```

**Required Fields:**
- `agent_purpose` - Agent's purpose/role description
- `messages` - Array of message objects with `type` and `content`

**Optional Fields:**
- `scenario_name` - Scenario/session identifier
- `exported_at` - Export timestamp
- `format_version` - Format version

### Format 2: Simple Format

```json
{
  "session_id": "session_001",
  "purpose": "Banking assistant that helps users check balances",
  "messages": [
    {"type": "user", "content": "What's my account balance?"},
    {"type": "assistant", "content": "Your current balance is $1,250.00"}
  ]
}
```

**Required Fields:**
- `purpose` - Agent's purpose/role description
- `messages` - Array of message objects with `type` and `content`

**Optional Fields:**
- `session_id` - Session identifier
- `agent_name` - Agent name
- `agent_role` - Agent role

---

**Note:** The CLI automatically detects which format you're using. It checks for `agent_purpose` first (Langfuse format), then falls back to `purpose` (simple format).

---

## Output Example

### Console Output

```
================================================================================
🛡️  AI AGENT GUARDS - BATCH SCANNER
================================================================================

📂 Scanning directory: ./sessions
✅ Found 51 session file(s)

🔍 Enabled scanners: PromptGuard, AlignmentCheck, FactsChecker, DataDisclosureGuard

⚙️  Processing sessions...

[████████████████████████████████████████] 100% | 51/51 | 🟢 session_051.json

✅ Processing complete!

📊 Aggregating results...
📝 Generating report...

================================================================================
📊 SUMMARY
================================================================================

Total Sessions: 51
Safe Sessions: 35 ✅
Sessions with Issues: 16 ⚠️

Total Blocks: 6 🚫
Total Warnings: 43 ⚠️
Total Safe: 198 ✅

================================================================================
```

### Markdown Report Structure

```markdown
# 🛡️ AI Agent Guards - Batch Scan Report

---

## 📊 Overall Statistics

- **Total Sessions Scanned:** 51
- **Safe Sessions:** 35 ✅
- **Sessions with Issues:** 16 ⚠️

**Accumulated Counts:**
- 🚫 **Blocks:** 6
- ⚠️ **Warnings:** 43
- ✅ **Safe:** 198

---

## 🔍 Results by Scanner

### AlignmentCheck

| Metric | Count |
|--------|-------|
| 🚫 Blocks | 3 |
| ⚠️ Warnings | 0 |
| ✅ Safe | 48 |

### FactsChecker

| Metric | Count |
|--------|-------|
| 🚫 Blocks | 3 |
| ⚠️ Warnings | 43 |
| ✅ Safe | 5 |

---

## 📋 Detailed Results per Session

_Note: Only showing sessions with issues. Safe sessions are omitted for brevity._

### Session 5: `session_005_goal_hijacking.json`

**Overall Decision:** 🔴 BLOCK

**Scanner Results:**

- **AlignmentCheck:** 🔴 BLOCK
  - Total: 4 | Safe: 2 | Warnings: 0 | Blocks: 2
  - _Reason:_ Agent redirected conversation from stated purpose...

- **FactsChecker:** 🟡 WARNING
  - Total: 4 | Safe: 2 | Warnings: 2 | Blocks: 0
  - _Reason:_ Detected ungrounded claims in messages 3 and 4...

---
```

**NEW: Google Sheets Integration** 🎉

The report now includes **two formats** for easy data analysis:

1. **Sessions Summary Table** - Markdown table with all sessions and per-scanner results
   - Format: `DECISION (total: safe/warning/block)`
   - Example: `SAFE (3: 3/0/0)` = 3 messages, all safe
   - Includes "Overall" column showing worst decision

2. **Copy-Paste Format (TSV)** - Tab-separated values for direct paste into Google Sheets
   - Format: `DECISION (safe/warning/block)`
   - Shorter format, perfect for spreadsheet analysis
   - Just copy and paste - columns align automatically!

**For complete guide on using the reports in Google Sheets, see:**
📖 **[BATCH_CLI_REPORT_FORMAT.md](./BATCH_CLI_REPORT_FORMAT.md)**

**Quick example:**
```
Session	AlignmentCheck	PromptGuard	FactsChecker	Overall
session1.json	SAFE (3/0/0)	SAFE (2/0/0)	WARNING (3/2/0)	WARNING
session2.json	BLOCK (1/0/2)	SAFE (2/0/0)	SAFE (5/0/0)	BLOCK
```

Copy → Paste into Google Sheets → Done! ✨

---

## Use Cases

### 1. CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Scan agent sessions
  run: |
    python -m multi_agent_demo.cli -d ./test_sessions -o scan_report.md

- name: Upload report
  uses: actions/upload-artifact@v3
  with:
    name: security-scan-report
    path: scan_report.md
```

### 2. Regression Testing

Before deploying changes:
```bash
# Scan baseline sessions
python -m multi_agent_demo.cli -d ./baseline_sessions -o baseline.md

# Make changes to agent

# Scan again and compare
python -m multi_agent_demo.cli -d ./baseline_sessions -o updated.md
diff baseline.md updated.md
```

### 3. Large-Scale Analysis

Process production logs:
```bash
# Export sessions from production to JSON
python export_sessions.py --output ./prod_sessions

# Scan all sessions
python -m multi_agent_demo.cli -d ./prod_sessions -o prod_analysis.md

# Review report for patterns
cat prod_analysis.md | grep "BLOCK"
```

### 4. Compliance Reporting

Generate reports for audits:
```bash
# Scan last month's sessions
python -m multi_agent_demo.cli \
  -d ./sessions/2026-01 \
  -o compliance_report_jan_2026.md \
  --show-safe

# Include in compliance documentation
```

---

## Testing the CLI

### Manual Test

Create test sessions:
```bash
python test_batch_cli.py
```

This creates a temp directory with sample sessions and shows you the command to run.

### Automated Test

Run the automated test:
```bash
python test_batch_cli_automated.py
```

This creates sessions, runs the CLI, and validates the output automatically.

---

## Architecture

The CLI shares code with the UI to ensure consistency:

```
multi_agent_demo/
├── cli.py                      # CLI entry point
├── app.py                      # UI entry point
├── core/                       # Shared logic
│   └── scanner_runner.py      # Scanner execution (used by both CLI and UI)
├── reports/                    # CLI-specific
│   └── markdown_generator.py  # Markdown report generation
├── firewall.py                # Scanner orchestration (shared)
└── scanners/                   # Scanner implementations (shared)
```

**Benefits of shared code:**
- Changes to scanner logic automatically apply to both CLI and UI
- Same validation rules everywhere
- Consistent results across modes
- Single source of truth

---

## Advanced Options

### Custom Session Format

If your sessions have a different structure, create a wrapper:

```python
from multi_agent_demo.core import run_scanners_on_session

# Load your custom format
custom_session = load_my_session("session.json")

# Convert to expected format
session_data = {
    "purpose": custom_session["agent_purpose"],
    "messages": [
        {"type": msg["role"], "content": msg["text"]}
        for msg in custom_session["conversation"]
    ]
}

# Run scanners
result = run_scanners_on_session(
    session_data=session_data,
    enabled_scanners=["AlignmentCheck", "FactsChecker"]
)
```

### Programmatic Usage

Use the CLI logic in your own scripts:

```python
from multi_agent_demo.core import run_scanners_on_session, aggregate_results
from multi_agent_demo.reports import generate_markdown_report

# Load sessions
sessions = [load_json(f) for f in session_files]

# Run scanners
results = [
    run_scanners_on_session(session, ["AlignmentCheck"])
    for session in sessions
]

# Aggregate
stats = aggregate_results(results)

# Generate report
report = generate_markdown_report(results, session_files, stats)
print(report)
```

---

## Troubleshooting

### Error: "No JSON files found"

Check:
- Directory path is correct
- JSON files have `.json` extension
- Files are not in subdirectories (CLI scans recursively with `**/*.json`)

### Error: "Module not found"

Run from project root:
```bash
cd /path/to/mutli-agent-demo
python -m multi_agent_demo.cli -d ./sessions
```

### Error: "TOGETHER_API_KEY not found"

Set environment variable:
```bash
export TOGETHER_API_KEY=your_key_here
python -m multi_agent_demo.cli -d ./sessions
```

Or create `.env` file:
```
TOGETHER_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### Slow Performance

Use fewer scanners:
```bash
# Fast: Only AlignmentCheck
python -m multi_agent_demo.cli -d ./sessions -s AlignmentCheck

# Slower: All scanners
python -m multi_agent_demo.cli -d ./sessions
```

---

## FAQ

**Q: Can I use the CLI without the UI?**
A: Yes! The CLI is standalone. Just ensure dependencies are installed.

**Q: Does the CLI support the same scanners as the UI?**
A: Yes, exactly the same scanners with the same logic.

**Q: Can I integrate with other CI/CD tools?**
A: Yes! The CLI is a standard Python script with exit codes:
- `0` = success
- `1` = error

**Q: How do I get only the statistics without the full report?**
A: Redirect stderr to see just the summary:
```bash
python -m multi_agent_demo.cli -d ./sessions 2>&1 | tail -20
```

**Q: Can I scan a single file?**
A: Yes, put it in a directory:
```bash
mkdir temp_scan
cp session.json temp_scan/
python -m multi_agent_demo.cli -d temp_scan
```

---

## Next Steps

1. **Try it**: Run `python test_batch_cli.py` to create sample sessions
2. **Integrate**: Add to your CI/CD pipeline
3. **Customize**: Adjust report format in `markdown_generator.py`
4. **Scale**: Process production logs for analysis

For more details, see:
- [README.md](./README.md) - Full documentation
- [CLAUDE.md](./CLAUDE.md) - Development guide
- [INSTALL.md](./INSTALL.md) - Installation guide
