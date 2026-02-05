# Batch CLI Report Format Guide

## Overview

The batch CLI generates markdown reports with **Google Sheets-compatible tables** for easy data analysis and tracking.

**Command:**
```bash
python -m multi_agent_demo.cli -d /path/to/sessions -o report.md
```

---

## Report Sections

### 1. Overall Statistics

Summary of all sessions scanned:
- Total sessions scanned
- Safe sessions (no issues)
- Sessions with issues
- Accumulated counts (blocks, warnings, safe)

### 2. Results by Scanner

Breakdown of each scanner's performance:
- Blocks: Number of messages blocked
- Warnings: Number of messages with warnings
- Safe: Number of messages passed

### 3. Sessions Summary Table ⭐ (NEW)

**Google Sheets compatible table** showing all sessions with per-scanner results.

**Format:** Each cell shows `DECISION (total: safe/warning/block)`

**Example:**
```markdown
| Session | AlignmentCheck | PromptGuard | FactsChecker | Overall |
|---------|---------------|-------------|--------------|---------|
| session1.json | SAFE (3: 3/0/0) | SAFE (2: 2/0/0) | WARNING (5: 3/2/0) | WARNING |
| session2.json | BLOCK (3: 1/0/2) | SAFE (2: 2/0/0) | SAFE (5: 5/0/0) | BLOCK |
| session3.json | SAFE (3: 3/0/0) | SAFE (2: 2/0/0) | SAFE (5: 5/0/0) | SAFE |
```

**Column Definitions:**
- **Session**: Session filename
- **[Scanner Name]**: Decision and counts for each scanner
- **Overall**: Worst decision across all scanners (BLOCK > WARNING > SAFE)

**How to use:**
1. Copy the markdown table
2. Paste into Google Sheets or Excel
3. Markdown will be converted to table format automatically

### 4. Copy-Paste Format (Tab-Separated) ⭐ (NEW)

**Plain text format** optimized for pasting directly into Google Sheets.

**Example:**
```
Session	AlignmentCheck	PromptGuard	FactsChecker	Overall
session1.json	SAFE (3/0/0)	SAFE (2/0/0)	WARNING (3/2/0)	WARNING
session2.json	BLOCK (1/0/2)	SAFE (2/0/0)	SAFE (5/0/0)	BLOCK
session3.json	SAFE (3/0/0)	SAFE (2/0/0)	SAFE (5/0/0)	SAFE
```

**How to use:**
1. Click inside the code block
2. Select all text (Cmd+A / Ctrl+A)
3. Copy (Cmd+C / Ctrl+C)
4. Open Google Sheets
5. Click on cell A1
6. Paste (Cmd+V / Ctrl+V)
7. Data automatically separates into columns!

**Format:** `DECISION (safe/warning/block)`
- Shorter format: just the counts
- Tab-separated for perfect column alignment

### 5. Detailed Results per Session

Full details for sessions with issues:
- Scanner-by-scanner breakdown
- Reason for each block/warning
- Counts per scanner

---

## Google Sheets Usage

### Method 1: Markdown Table (Recommended)

**Best for:** Viewing in markdown editors, GitHub, documentation

1. Copy the "Sessions Summary Table" section
2. Paste into Google Sheets
3. Sheets will detect the table structure

**Pros:**
- ✅ Readable format with column names
- ✅ Clear decision labels
- ✅ Shows detailed counts

### Method 2: TSV Copy-Paste (Fastest)

**Best for:** Quick data import, bulk analysis, charts

1. Find "Copy-Paste Format (Tab-Separated)" section
2. Copy the text from the code block
3. Paste into Google Sheets cell A1
4. Data splits into columns automatically

**Pros:**
- ✅ Fastest method
- ✅ Perfect column alignment
- ✅ No formatting needed
- ✅ Easy to create charts/pivot tables

---

## Understanding the Data

### Decision Types

| Decision | Meaning | Color |
|----------|---------|-------|
| **SAFE** | No issues detected | 🟢 Green |
| **WARNING** | Minor issues, review recommended | 🟡 Yellow |
| **BLOCK** | Critical issues, action required | 🔴 Red |
| **ERROR** | Scanner encountered an error | ⚠️ Orange |
| **-** | Scanner not run or not available | ⚪ Gray |

### Count Format

**In markdown table:** `DECISION (total: safe/warning/block)`
- **total**: Total messages analyzed
- **safe**: Messages with no issues
- **warning**: Messages with warnings
- **block**: Messages blocked

**Example:** `WARNING (5: 3/2/0)` means:
- Total: 5 messages analyzed
- Safe: 3 messages
- Warnings: 2 messages
- Blocks: 0 messages
- Overall: WARNING (because has warnings)

**In TSV:** `DECISION (safe/warning/block)`
- Same counts, shorter format
- Easier to parse programmatically

### Overall Decision Logic

The "Overall" column uses the **worst decision** across all scanners:

```
BLOCK > WARNING > SAFE
```

**Examples:**
- AlignmentCheck: SAFE, PromptGuard: WARNING → Overall: **WARNING**
- AlignmentCheck: BLOCK, PromptGuard: SAFE → Overall: **BLOCK**
- AlignmentCheck: SAFE, PromptGuard: SAFE → Overall: **SAFE**

---

## Google Sheets Analysis Examples

### 1. Count Sessions by Overall Status

```
=COUNTIF(E:E, "SAFE")
=COUNTIF(E:E, "WARNING")
=COUNTIF(E:E, "BLOCK")
```

### 2. Create Pie Chart of Decisions

1. Select the "Overall" column
2. Insert → Chart → Pie Chart
3. Customize colors: SAFE=Green, WARNING=Yellow, BLOCK=Red

### 3. Extract Counts from Cell

If cell B2 contains `SAFE (3/0/0)`, extract counts:

```
# Extract safe count (first number)
=VALUE(MID(B2, FIND("(", B2)+1, FIND("/", B2) - FIND("(", B2) - 1))

# Extract warning count (second number)
=VALUE(MID(B2, FIND("/", B2)+1, FIND("/", B2, FIND("/", B2)+1) - FIND("/", B2) - 1))

# Extract block count (third number)
=VALUE(MID(B2, FIND("/", B2, FIND("/", B2)+1)+1, FIND(")", B2) - FIND("/", B2, FIND("/", B2)+1) - 1))
```

### 4. Filter Sessions with Issues

```
=FILTER(A:E, E:E<>"SAFE")
```

### 5. Pivot Table for Scanner Comparison

1. Select all data (A1:E100)
2. Data → Pivot Table
3. Rows: Overall Decision
4. Columns: Scanner Name
5. Values: Count of Sessions

---

## Advanced Usage

### Automated Tracking

Run CLI regularly and append results to a master spreadsheet:

```bash
# Generate report
python -m multi_agent_demo.cli -d ./sessions -o report.md

# Extract TSV section and append to Google Sheets via API
# (requires Google Sheets API setup)
```

### Trend Analysis

Track scanner performance over time:

| Date | Total Sessions | Safe % | Warning % | Block % |
|------|----------------|--------|-----------|---------|
| 2026-02-01 | 100 | 85% | 10% | 5% |
| 2026-02-02 | 105 | 82% | 12% | 6% |
| 2026-02-03 | 110 | 88% | 8% | 4% |

### Scanner Comparison

Compare different scanners' detection rates:

| Scanner | Blocks | Warnings | False Positive Rate |
|---------|--------|----------|---------------------|
| AlignmentCheck | 12 | 0 | 2% |
| PromptGuard | 8 | 15 | 5% |
| FactsChecker | 5 | 20 | 1% |

---

## Tips & Tricks

### Formatting in Google Sheets

1. **Conditional Formatting:**
   - Highlight cells containing "BLOCK" in red
   - Highlight cells containing "WARNING" in yellow
   - Highlight cells containing "SAFE" in green

2. **Data Validation:**
   - Create dropdown for filtering by decision type
   - Lock header rows to prevent editing

3. **Formulas:**
   - Use `COUNTIF` to count decisions
   - Use `FILTER` to show only sessions with issues
   - Use `QUERY` for complex analysis

### Keyboard Shortcuts

- **Copy all text in code block:** Click inside → Cmd/Ctrl+A → Cmd/Ctrl+C
- **Paste and keep formatting:** Cmd/Ctrl+Shift+V
- **Auto-resize columns:** Select columns → Double-click column divider

### Collaboration

Share the Google Sheet with team members:
1. File → Share
2. Set permissions (view/edit)
3. Add team members' emails
4. Use comments to discuss specific sessions

---

## Example Workflow

**1. Run batch scan:**
```bash
python -m multi_agent_demo.cli \
  -d /Users/user/sessions_prod \
  -s AlignmentCheck PromptGuard FactsChecker \
  -o weekly_report.md
```

**2. Open the report:**
```bash
cat weekly_report.md
```

**3. Copy TSV section to Google Sheets:**
- Find "Copy-Paste Format (Tab-Separated)"
- Copy the text block
- Paste into Google Sheets

**4. Analyze:**
- Apply conditional formatting
- Create charts
- Filter for sessions with issues

**5. Share:**
- Share sheet with team
- Add comments for specific sessions
- Track progress over time

---

## Troubleshooting

### Paste not splitting into columns

**Solution:** Ensure you're copying from the TSV code block, not the markdown table.

### Columns not aligned

**Solution:** Use "Copy-Paste Format (Tab-Separated)" section, not the markdown table.

### Counts showing as text

**Solution:** Google Sheets may interpret `(3/0/0)` as text. Use formulas to extract numbers (see Advanced Usage section).

### Missing data in cells

**Possible causes:**
- Scanner not enabled (shows "-")
- Scanner error (shows "ERROR")
- Check detailed results section for errors

---

## Related Documentation

- `BATCH_CLI_GUIDE.md` - Complete CLI usage guide
- `README.md` - Overall project documentation
- `SCANNER_VALIDATION.md` - Scanner code validation

---

## Questions?

For issues or feature requests, see:
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Documentation: `README.md` in project root
