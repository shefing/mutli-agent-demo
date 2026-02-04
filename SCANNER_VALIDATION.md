# Scanner Code Path Validation - CLI vs UI

## Validation Date
2026-02-04

## Architecture

### CLI Flow
```
cli.py
  └─> core/scanner_runner.py::run_scanners_on_session()
       ├─> alignment_check_new.py::scan_alignment_check_per_message()
       ├─> alignment_check_new.py::scan_prompt_guard_per_message()
       ├─> scanners/nemo_scanners.py::FactCheckerScanner().scan()
       └─> scanners/data_disclosure_scanner.py::DataDisclosureGuardScanner().scan()
```

### UI Flow
```
ui/conversation_builder.py
  └─> firewall.py::run_scanner_tests()
       ├─> alignment_check_new.py::scan_alignment_check_per_message()
       ├─> alignment_check_new.py::scan_prompt_guard_per_message()
       ├─> scanners/nemo_scanners.py::FactCheckerScanner().scan()
       └─> scanners/data_disclosure_scanner.py::DataDisclosureGuardScanner().scan()
```

## Scanner-by-Scanner Validation

### 1. AlignmentCheck ✅ VERIFIED IDENTICAL

**Shared Code:** `alignment_check_new.py::scan_alignment_check_per_message()`

**CLI Call (scanner_runner.py:72-76):**
```python
from multi_agent_demo.alignment_check_new import scan_alignment_check_per_message
results["alignment_check"] = scan_alignment_check_per_message(
    messages=messages,
    purpose=purpose
)
```

**UI Call (firewall.py:244-247):**
```python
alignment_result = scan_alignment_check_per_message(
    st.session_state.current_conversation["messages"],
    st.session_state.current_conversation["purpose"]
)
```

**Status:** ✅ Both use identical function with same parameters

**Recent Fixes:**
- Updated prompt to better distinguish agent analysis vs agent failure
- Increased max_tokens from 256 to 512
- **Switched from Llama-3.1-8B (Together) to GPT-4o-mini (OpenAI)** for better reasoning
- Changed API key from `TOGETHER_API_KEY` to `OPENAI_API_KEY`

---

### 2. PromptGuard ✅ VERIFIED IDENTICAL

**Shared Code:** `alignment_check_new.py::scan_prompt_guard_per_message()`

**CLI Call (scanner_runner.py:83-86):**
```python
from multi_agent_demo.alignment_check_new import scan_prompt_guard_per_message
results["prompt_guard"] = scan_prompt_guard_per_message(
    messages=messages
)
```

**UI Call (firewall.py:256-258):**
```python
promptguard_result = scan_prompt_guard_per_message(
    st.session_state.current_conversation["messages"]
)
```

**Status:** ✅ Both use identical function with same parameters

---

### 3. FactsChecker ✅ VERIFIED IDENTICAL (FIXED)

**Shared Code:** `scanners/nemo_scanners.py::FactCheckerScanner`

**Method Signature:**
```python
def scan(self, messages: List[Dict], context: str = "") -> Dict:
```

**CLI Call (scanner_runner.py:94-96):**
```python
scanner = FactCheckerScanner()
# Use explicit keyword arg 'context' to match method signature
result = scanner.scan(messages, context=purpose)
```

**UI Call (firewall.py:268):**
```python
nemo_results["FactsChecker"] = nemo_scanners["FactsChecker"].scan(messages, context=purpose)
```

**Status:** ✅ Both use explicit `context=purpose` keyword argument

**Recent Fix:** Updated CLI to use explicit keyword argument to match UI

---

### 4. DataDisclosureGuard ✅ VERIFIED IDENTICAL

**Shared Code:** `scanners/data_disclosure_scanner.py::DataDisclosureGuardScanner`

**Method Signature:**
```python
def scan(self, messages: List[Dict], purpose: str = "") -> Dict:
```

**CLI Call (scanner_runner.py:108-109):**
```python
scanner = DataDisclosureGuardScanner()
result = scanner.scan(messages, purpose)
```

**UI Call (firewall.py:271):**
```python
nemo_results["DataDisclosureGuard"] = nemo_scanners["DataDisclosureGuard"].scan(messages, purpose)
```

**Status:** ✅ Both use identical calls

---

## Summary

### All Scanners Status: ✅ VERIFIED IDENTICAL

| Scanner | Shared Code | CLI/UI Identical | Notes |
|---------|-------------|------------------|-------|
| AlignmentCheck | `alignment_check_new.py` | ✅ Yes | Recently updated prompt |
| PromptGuard | `alignment_check_new.py` | ✅ Yes | - |
| FactsChecker | `nemo_scanners.py` | ✅ Yes | Fixed CLI to use explicit keyword arg |
| DataDisclosureGuard | `data_disclosure_scanner.py` | ✅ Yes | - |

### Changes Made
1. **AlignmentCheck prompt fix** - Better distinction between agent analysis vs failure
2. **AlignmentCheck max_tokens** - Increased from 256 to 512 to prevent truncation
3. **FactsChecker CLI fix** - Use explicit `context=purpose` keyword argument
4. **UI fallback fix** - Changed from `scan_alignment_check_direct()` to `scan_alignment_check_per_message()`

### No Remaining Discrepancies
All 4 scanners now use identical code paths in both CLI and UI.

### Testing Confirmation
- CLI tested on `/tmp/test_single/environment_prod_4ceb5892.json` - shows SAFE with 3 safe messages
- UI should show identical results after restart (may need cache clear)

### Maintenance Note
When modifying scanner behavior, ensure changes are made to the shared scanner implementations:
- `alignment_check_new.py` for AlignmentCheck and PromptGuard
- `scanners/nemo_scanners.py` for FactsChecker
- `scanners/data_disclosure_scanner.py` for DataDisclosureGuard

Both CLI (`core/scanner_runner.py`) and UI (`firewall.py`) will automatically use the updated code.
