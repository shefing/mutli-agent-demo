# Root Cause Analysis: AlignmentCheck False Positives

## TL;DR - The Smoking Gun

**Problem:** GPT-4o-mini is producing false positives (Issue #3: collaborative behavior)

**Root Cause:** Native LlamaFirewall was NEVER running because `TOGETHER_API_KEY` is commented out in `.env`

**Evidence:**
```bash
$ cat .env
OPENAI_API_KEY=sk-***
# TOGETHER_API_KEY=***   ← COMMENTED OUT!
```

**What's Actually Happening:**
```
initialize_firewall()
  ↓
Check: TOGETHER_API_KEY exists? → NO!
  ↓
firewall.py:57: st.error("⚠️ AlignmentCheck requires TOGETHER_API_KEY")
  ↓
Return None (firewall initialization failed)
  ↓
test_alignment_check() → Exception: firewall is None
  ↓
Fallback: scan_alignment_check_per_message() → Uses GPT-4o-mini
  ↓
GPT-4o-mini produces Issue #3 false positives
```

## The Complete Timeline

### Phase 1: Original Implementation (Llama-3.1-8B)
- **Code:** `direct_scanner_wrapper.py`
- **Model:** Llama-3.1-8B via Together API
- **Key:** TOGETHER_API_KEY
- **Issues:** #1 (parsing bug), #2 (semantic confusion)

### Phase 2: Model Switch (GPT-4o-mini)
- **Code:** `alignment_check_new.py`
- **Model:** GPT-4o-mini via OpenAI API
- **Key:** OPENAI_API_KEY
- **Changed:** .env file - commented out TOGETHER_API_KEY, added OPENAI_API_KEY
- **Fixes:** Issues #1 and #2
- **New Issue:** #3 (collaborative behavior false positives)

### Phase 3: Current State (Confusion)
- **Native LlamaFirewall:** NEVER running (missing TOGETHER_API_KEY)
- **Actual Implementation:** GPT-4o-mini (fallback)
- **User Experience:** False positives from GPT-4o-mini
- **User Belief:** Native LlamaFirewall might be better
- **Reality:** Native LlamaFirewall hasn't been tested because it can't initialize

## Verification

Let's check what happens when the app runs:

**File: `firewall.py:54-58`**
```python
if enabled_scanners.get("AlignmentCheck", False):
    together_key = os.getenv("TOGETHER_API_KEY")
    if not together_key:
        st.error("⚠️ AlignmentCheck requires TOGETHER_API_KEY...")
        return None  # ← Firewall initialization FAILS
```

**File: `firewall.py:182-205`**
```python
def test_alignment_check(firewall, trace, messages, purpose):
    try:
        result = firewall.scan_replay(trace)  # ← Never reaches here (firewall is None)
        return {...}
    except Exception as e:  # ← Catches "NoneType has no attribute scan_replay"
        print(f"⚠️ LlamaFirewall AlignmentCheck failed: {e}")
        return scan_alignment_check_per_message(messages, purpose)  # ← ALWAYS goes here
```

**Result:** GPT-4o-mini is ALWAYS used because native LlamaFirewall never initializes.

## The Real Question

**User asked:** "What would it take to revert to native LlamaFirewall?"

**Answer:** You're not using native LlamaFirewall right now! You're using GPT-4o-mini because TOGETHER_API_KEY is commented out.

**The actual choices are:**

### Option A: Enable Native LlamaFirewall (RECOMMENDED - EASIEST)
**What:** Uncomment TOGETHER_API_KEY in `.env`

**Impact:** Native LlamaFirewall will work, GPT-4o-mini fallback won't be needed

**Unknown:** We don't know if native LlamaFirewall has Issue #3 (collaborative behavior false positives)

**Effort:** 5 seconds to uncomment + 10 minutes testing

**Steps:**
1. Edit `.env`:
   ```bash
   OPENAI_API_KEY=sk-***
   TOGETHER_API_KEY=<your-key>   # ← UNCOMMENT THIS
   ```
2. Restart Streamlit app
3. Run test with `environment_prod_1dfdc5c0.json` (Issue #3 test case)
4. Check if Assistant #1 and #8 are still falsely blocked

**Expected Outcome:**
- Native LlamaFirewall will run
- If it has Issue #3: Keep both keys, keep GPT-4o-mini fallback
- If it doesn't have Issue #3: Remove OPENAI_API_KEY, remove GPT-4o-mini code

---

### Option B: Revert to Custom Llama-3.1-8B
**What:** Switch `alignment_check_new.py` back to Together API + Llama model

**Impact:** Same as Phase 1 (fixes Issue #3, brings back Issue #2)

**Effort:** 1-2 hours (code changes + testing)

---

### Option C: Keep GPT-4o-mini, Improve Prompt
**What:** Continue prompt engineering

**Impact:** Ongoing iterative fixes

**Effort:** Ongoing (2-3 hours per issue)

## Recommendation

**IMMEDIATE ACTION (5 minutes):**

1. **Uncomment TOGETHER_API_KEY in `.env`:**
   ```bash
   # Before:
   # TOGETHER_API_KEY=***

   # After:
   TOGETHER_API_KEY=***
   ```

2. **Restart Streamlit app**

3. **Test with Issue #3 scenario:**
   ```bash
   python multi_agent_demo/cli.py --session sessions_prod/environment_prod_1dfdc5c0.json
   ```

4. **Check results:**
   - If Assistant #1 and #8 are now SAFE → Native LlamaFirewall WORKS! Issue #3 is fixed!
   - If still BLOCK → Native LlamaFirewall has same issue as GPT-4o-mini

**THEN DECIDE:**

**If native works (Issue #3 fixed):**
- Remove `alignment_check_new.py` (GPT-4o-mini implementation)
- Remove OPENAI_API_KEY dependency from README
- Keep only TOGETHER_API_KEY
- Done! ✅

**If native has same issue:**
- You have 3 options:
  1. Revert to custom Llama-3.1-8B (accept Issue #2, fix Issue #3)
  2. Keep GPT-4o-mini (accept Issue #3, fix Issue #2)
  3. Implement hybrid with cascading fallback

## Why This Matters

**Current confusion:**
- User thinks they switched from Llama to GPT-4o-mini
- User thinks native LlamaFirewall might be better than GPT-4o-mini
- User doesn't realize native LlamaFirewall has never been tested

**Reality:**
- Native LlamaFirewall initialization has been failing silently
- All testing has been with GPT-4o-mini fallback
- We don't know if native LlamaFirewall has Issue #3

**Solution:**
- Enable native LlamaFirewall (uncomment one line)
- Test it properly
- Then decide based on actual results

## Testing Checklist

After uncommenting TOGETHER_API_KEY, test these scenarios:

### Issue #1: Parsing Bug (should be fixed in all implementations)
```bash
python test_alignment_check_fixes.py
# Look for: test_parsing_edge_cases() PASS
```

### Issue #2: Semantic Confusion (Llama fails, GPT-4o-mini fixed)
```bash
python multi_agent_demo/cli.py --session sessions_prod/environment_prod_4ceb5892.json
# Expected: SAFE (agent analyzing external failure)
```

### Issue #3: Collaborative Behavior (GPT-4o-mini fails, native unknown)
```bash
python multi_agent_demo/cli.py --session sessions_prod/environment_prod_1dfdc5c0.json
# Expected: SAFE for Assistant #1 and #8 (asking for approval)
```

## Files to Update After Testing

**If native works well:**

1. **Remove GPT-4o-mini implementation:**
   - Delete or rename `alignment_check_new.py` → `alignment_check_new.py.backup`

2. **Update firewall.py fallback:**
   ```python
   # Line 198: Change from
   return scan_alignment_check_per_message(messages, purpose)

   # To:
   return {"error": "Native LlamaFirewall failed", "scanner": "AlignmentCheck"}
   ```

3. **Update README.md:**
   - Remove: "⚠️ AlignmentCheck now uses GPT-4o-mini instead of Llama-3.1-8B"
   - Remove: OPENAI_API_KEY requirement
   - Keep: TOGETHER_API_KEY requirement

4. **Update ALIGNMENT_CHECK_MODEL_SWITCH.md:**
   - Add: "Reverted to native LlamaFirewall after discovering it was never tested"
   - Document: Why native works better

**If native has issues:**
- Keep current hybrid approach
- Document known limitations
- Consider cascading fallback (Option 4 from analysis doc)

---

## Summary

**You asked:** "What would it take to revert to native LlamaFirewall?"

**Answer:** Uncomment one line in `.env` - you've never actually used native LlamaFirewall yet!

**Next Step:** Test native LlamaFirewall properly, then decide based on results.

**Time Required:** 5 minutes to enable + 15 minutes to test = 20 minutes total
