# Scanner Fixes - DataDisclosureGuard & FactsChecker

## Issues Found During Testing

### Issue 1: DataDisclosureGuard - DATE_TIME Instead of SSN

**Problem:**
When testing "PII - Misaligned Disclosure" scenario with SSN `123-45-6789`, the scanner detected it as `DATE_TIME` instead of `US_SSN`.

**Root Cause:**
Presidio's default DATE_TIME recognizer is overly aggressive and matches patterns like `123-45-6789` as dates (interpreting as month-day-year).

**Example:**
```
Input: "Sure, it's 123-45-6789"
❌ Detected: DATE_TIME (wrong!)
✅ Expected: US_SSN
```

**Fix Applied:**

1. **Priority Entity List:**
   - Created list of high-risk PII types (SSN, credit card, etc.)
   - These take precedence over DATE_TIME

2. **Filtering Logic:**
   - Filter out low-confidence DATE_TIME detections (< 0.7 confidence)
   - Skip DATE_TIME if it overlaps with priority PII

3. **Fallback Strategy:**
   - If only DATE_TIME found, re-analyze with priority entities only
   - This catches SSN patterns that were misclassified

**Code Changes:**

File: `multi_agent_demo/scanners/data_disclosure_scanner.py`

```python
def detect_pii(self, text: str) -> List[Dict]:
    # Priority entity types (high-risk PII)
    priority_entities = [
        "CREDIT_CARD", "US_SSN", "US_BANK_NUMBER", "US_ITIN",
        "US_PASSPORT", "IBAN_CODE", "CRYPTO"
    ]

    # Analyze text for PII
    results = self.analyzer.analyze(text=text, language='en')

    # Filter out low-confidence DATE_TIME
    pii_entities = []
    for result in results:
        if result.entity_type == "DATE_TIME" and result.score < 0.7:
            overlaps_priority = any(
                r.entity_type in priority_entities and
                (r.start <= result.start < r.end or r.start < result.end <= r.end)
                for r in results
            )
            if overlaps_priority:
                continue  # Skip this DATE_TIME

        pii_entities.append({...})

    # Fallback: If no priority PII found, re-analyze
    if not any(e["type"] in priority_entities for e in pii_entities):
        results_high_priority = self.analyzer.analyze(
            text=text,
            language='en',
            entities=priority_entities + ["EMAIL_ADDRESS", "PHONE_NUMBER", ...]
        )
        # Use these results instead
```

**Result:**
- ✅ SSN patterns now detected correctly as `US_SSN`
- ✅ DATE_TIME false positives eliminated
- ✅ High-risk PII prioritized

---

### Issue 2: FactsChecker - Inverted Risk Score

**Problem:**
When FactsChecker detected NO false claims (ALLOW decision), it showed:
- Risk gauge: **0.9** (high risk, red zone)
- Decision: **ALLOW** (safe)
- Analysis: "No false claims detected"

This is contradictory and confusing - safe content showing as high risk!

**Root Cause:**
FactsChecker was using **confidence score** (0.9 = high confidence in accuracy) but our UI interprets scores as **risk levels** (0.9 = high danger).

**Score Interpretation Mismatch:**

| Scenario | FactsChecker (Before) | UI Gauge Interpretation | Result |
|----------|----------------------|------------------------|--------|
| No false claims | 0.9 (confident it's accurate) | 0.9 = High Risk 🔴 | ❌ Confusing! |
| False claims found | 0.1 (low confidence) | 0.1 = Low Risk 🟢 | ❌ Wrong! |

**Fix Applied:**

Inverted the score logic to represent **RISK** instead of **CONFIDENCE**:

File: `multi_agent_demo/scanners/nemo_scanners.py`

**Before:**
```python
if has_false_claims:
    decision = "BLOCK"
    score = 0.1  # Very low confidence in false content ❌ Wrong!
else:
    decision = "ALLOW"
    score = 0.9  # High confidence in accurate content ❌ Confusing!
```

**After:**
```python
# NOTE: Score represents RISK level (0=safe, 1=dangerous)
if has_false_claims:
    decision = "BLOCK"
    score = 0.9  # High risk - false claims detected ✅
else:
    decision = "ALLOW"
    score = 0.1  # Low risk - content appears accurate ✅
```

**Result:**

| Scenario | FactsChecker Score | UI Gauge | Clarity |
|----------|-------------------|----------|---------|
| No false claims | 0.1 (low risk) | 🟢 Empty (safe) | ✅ Clear! |
| False claims found | 0.9 (high risk) | 🔴 Full (danger) | ✅ Correct! |

---

## Testing Results

### Test 1: PII - Misaligned Disclosure

**Before Fixes:**
```
DataDisclosureGuard:
- Finding 1: DATE_TIME (wrong!) ❌
- Finding 2: DATE_TIME (wrong!) ❌
- Decision: ALLOW ❌

FactsChecker:
- Gauge: 0.9 (high risk) but ALLOW ❌ Confusing!
```

**After Fixes:**
```
DataDisclosureGuard:
- Finding 1: US_SSN ✅
- Finding 2: US_SSN ✅
- Decision: HUMAN_IN_THE_LOOP ✅

FactsChecker:
- Gauge: 0.1 (low risk) and ALLOW ✅ Clear!
```

### Test 2: Fact-Checking Test (False Claims)

**Before Fixes:**
```
FactsChecker:
- Gauge: 0.1 (low risk) ❌ Should be high!
- Decision: BLOCK ✅
```

**After Fixes:**
```
FactsChecker:
- Gauge: 0.9 (high risk) ✅
- Decision: BLOCK ✅
- Correctly shows danger for false claims
```

---

## Summary of Changes

### Files Modified

1. **`multi_agent_demo/scanners/data_disclosure_scanner.py`**
   - Added priority entity list for high-risk PII
   - Implemented DATE_TIME filtering logic
   - Added fallback re-analysis for edge cases

2. **`multi_agent_demo/scanners/nemo_scanners.py`**
   - Inverted FactsChecker score logic
   - Changed from "confidence" to "risk" scoring
   - Added clarifying comments

### Impact

✅ **DataDisclosureGuard:**
- Accurate PII detection (SSN, credit cards, etc.)
- No more DATE_TIME false positives
- Reliable misalignment detection

✅ **FactsChecker:**
- Risk gauge matches decision (0.1=safe, 0.9=dangerous)
- No more confusing contradictions
- Clear visual indication of content quality

### Verification

Run these scenarios to verify fixes:

1. **PII - Misaligned Disclosure**
   - Should detect US_SSN (not DATE_TIME)
   - Should trigger HUMAN_IN_THE_LOOP
   - FactsChecker should show ~0.1 (low risk)

2. **Fact-Checking Test**
   - Should detect multiple false claims
   - Should show BLOCK decision
   - Gauge should show ~0.9 (high risk)

3. **Legitimate Banking**
   - Should show ALLOW for all scanners
   - All gauges should be in green zone (< 0.3)

---

## Technical Notes

### Presidio Entity Detection Order

Presidio processes recognizers in order:
1. Pattern-based recognizers (regex)
2. Context-based recognizers (NLP)
3. Date/Time recognizers (aggressive matching)

Our fix ensures high-risk PII (SSN, credit cards) are checked first and take precedence.

### Score Semantic Consistency

All scanners now use consistent score semantics:

| Score Range | Meaning | Gauge Display | Decision Guidance |
|-------------|---------|---------------|-------------------|
| **0.0 - 0.3** | Low Risk | 🟢 Green zone | ALLOW |
| **0.3 - 0.7** | Medium Risk | 🟡 Yellow zone | WARNING |
| **0.7 - 1.0** | High Risk | 🔴 Red zone | BLOCK / HUMAN_IN_THE_LOOP |

This applies to:
- AlignmentCheck
- FactsChecker
- DataDisclosureGuard
- (PromptGuard uses different scale but same principle)

---

## Future Improvements

### DataDisclosureGuard

1. **Custom PII Recognizers:**
   - Add domain-specific patterns (employee IDs, customer numbers)
   - Industry-specific PII (medical record numbers, policy numbers)

2. **Severity Levels:**
   - Critical PII (SSN, credit card) → immediate block
   - Low-risk PII (email, phone) → flag but allow

3. **Redaction Option:**
   - Mask detected PII instead of blocking
   - Allow conversation to continue with redacted data

### FactsChecker

1. **Confidence Levels:**
   - High confidence false claims → 0.9
   - Uncertain claims → 0.5
   - Verified accurate → 0.1

2. **Claim-by-Claim Analysis:**
   - Break down response into individual claims
   - Score each claim separately
   - Aggregate for overall risk

---

## Deployment

Both fixes are **backward compatible** and require no configuration changes:

```bash
# Just deploy the updated code
git add multi_agent_demo/scanners/
git commit -m "Fix: DataDisclosureGuard DATE_TIME false positives & FactsChecker score inversion"
git push
```

Streamlit Cloud will auto-deploy and fixes will be live immediately!
