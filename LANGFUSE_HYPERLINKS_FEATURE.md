# Langfuse Session Hyperlinks in CLI Reports

## Overview

CLI reports now automatically hyperlink session filenames to their Langfuse session URLs, making it easy to navigate from test results to detailed Langfuse traces.

## Feature

When generating markdown reports, session names are now clickable links that open the corresponding Langfuse session in your browser.

## Example

### Summary Table (Before)
```markdown
| Session | AlignmentCheck | Overall |
|---------|----------------|---------|
| environment_prod_98b176c9.json | SAFE (5: 5/0/0) | SAFE |
```

### Summary Table (After)
```markdown
| Session | AlignmentCheck | Overall |
|---------|----------------|---------|
| [environment_prod_98b176c9.json](https://us.cloud.langfuse.com/project/.../sessions/d01231e3...) | SAFE (5: 5/0/0) | SAFE |
```

### Detailed Results (Before)
```markdown
### Session 1: `environment_prod_98b176c9.json`
```

### Detailed Results (After)
```markdown
### Session 1: [`environment_prod_98b176c9.json`](https://us.cloud.langfuse.com/project/.../sessions/d01231e3...)
```

## How It Works

### 1. Langfuse Session Export Format
Session JSON files from Langfuse include a `langfuse_session_url` field:

```json
{
  "scenario_name": "environment_prod_98b176c9",
  "langfuse_session_url": "https://us.cloud.langfuse.com/project/cmd918irz02wcad07s78q25yg/sessions/d01231e3...",
  "agent_purpose": "...",
  "messages": [...]
}
```

### 2. CLI Processing
The CLI:
1. Loads session JSON files
2. Extracts the `langfuse_session_url` field
3. Passes it to the report generator
4. Creates markdown hyperlinks: `[filename](url)`

### 3. Report Generation
The report generator creates hyperlinks in:
- **Summary Table:** Session column shows clickable filenames
- **Detailed Results:** Session headers are clickable
- **CSV Format:** Plain filenames (no links) for Google Sheets compatibility

## Benefits

### 1. Quick Navigation
Click directly from report to Langfuse trace:
```
Report → Click session name → Opens in Langfuse → View full conversation
```

### 2. Context Switching
Easy to:
- Review test results in markdown
- Click to see full conversation in Langfuse
- Investigate issues without searching

### 3. Sharing Reports
Reports can be:
- Shared as markdown files
- Viewed in GitHub (hyperlinks work)
- Opened in markdown viewers
- Pasted into Slack/Discord (links preserved)

## Usage

### Generate Report with Links
```bash
# Single file
python multi_agent_demo/cli.py \
  -f sessions_prod/environment_prod_98b176c9.json \
  -s AlignmentCheck

# Batch with output file
python multi_agent_demo/cli.py \
  -d sessions_prod/ \
  -s AlignmentCheck \
  -o report.md
```

### View Report
```bash
# View in terminal
cat report.md

# Open in markdown viewer (macOS)
open -a "Marked 2" report.md

# View in GitHub
# Just commit and push - links will be clickable
```

## Implementation Details

### Files Modified

**CLI (`cli.py`):**
- Added `session_data_list` to store session data
- Passes session data to report generator

**Report Generator (`reports/markdown_generator.py`):**
- Added `session_data_list` parameter
- Extracts `langfuse_session_url` from each session
- Creates markdown hyperlinks for session names

### Code Changes

```python
# CLI: Store session data
session_data_list.append(session_data)

# Report: Create hyperlink
langfuse_url = session_data.get("langfuse_session_url", "")
if langfuse_url:
    session_display = f"[{session_name}]({langfuse_url})"
else:
    session_display = session_name
```

## Fallback Behavior

If `langfuse_session_url` is not present in the JSON:
- Session name is displayed without hyperlink
- Report generation continues normally
- No errors or warnings

This ensures backward compatibility with session files that don't have the URL field.

## Testing

### Test Single File
```bash
python multi_agent_demo/cli.py \
  -f sessions_prod/environment_prod_98b176c9.json \
  -s AlignmentCheck
```

Expected output:
```markdown
| [environment_prod_98b176c9.json](https://us.cloud.langfuse.com/...) | SAFE (5: 5/0/0) | SAFE |
```

### Test Batch
```bash
python multi_agent_demo/cli.py \
  -d sessions_prod/ \
  -s AlignmentCheck \
  -o report.md

# Check hyperlinks in report
grep -E '\[.*\]\(https://us.cloud.langfuse.com' report.md
```

### Test Without Langfuse URL
Create a test session without `langfuse_session_url`:
```json
{
  "scenario_name": "test_session",
  "agent_purpose": "Test",
  "messages": []
}
```

Expected: Session name shown without hyperlink (graceful fallback).

## Future Enhancements

### 1. Trace-Level Links
Currently links to session. Could also link individual messages to traces:
```markdown
- Message #3: [`Assistant response`](https://langfuse.com/trace/abc123)
```

### 2. Observation-Level Links
Link specific observations (API calls, tool uses):
```markdown
- Tool call: [`execute_workflow`](https://langfuse.com/observation/def456)
```

### 3. Comparison View
Link multiple sessions for side-by-side comparison:
```markdown
- [Compare sessions](https://langfuse.com/compare?sessions=abc,def)
```

### 4. Direct Edit Links
Link to edit/annotate in Langfuse:
```markdown
- [Annotate in Langfuse](https://langfuse.com/sessions/abc/annotate)
```

## Related Documentation

- Session export format: Langfuse export API docs
- Markdown hyperlinks: [CommonMark spec](https://commonmark.org/)
- Report generation: `BATCH_CLI_REPORT_FORMAT.md`

## Troubleshooting

### Links Don't Work
**Problem:** Clicking link does nothing

**Solution:** Check if you're viewing in a markdown-compatible viewer:
- ✅ GitHub, GitLab, Bitbucket
- ✅ Markdown editors (Typora, Marked, VSCode)
- ❌ Plain text editors (won't render links)

### Wrong URL Format
**Problem:** Link points to wrong Langfuse instance

**Solution:** Ensure JSON export includes correct `langfuse_session_url`:
```bash
# Check URL in JSON
jq '.langfuse_session_url' session.json
```

### Missing Links
**Problem:** Some sessions don't have links

**Solution:** Re-export from Langfuse with updated exporter that includes URLs:
```bash
# Ensure export includes langfuse_session_url field
python export_from_langfuse.py --include-urls
```
