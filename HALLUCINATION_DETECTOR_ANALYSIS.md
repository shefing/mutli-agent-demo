# HallucinationDetector Scanner: Implementation Analysis

## Executive Summary

**Current State:** The `HallucinationDetectorScanner` uses **advanced heuristic pattern matching** only, not actual NeMo GuardRails AI analysis.

**Cross-Message Detection:** ❌ **No** - Currently only analyzes the **last assistant message**, not contradictions across multiple messages in a conversation.

---

## Current Implementation

### Architecture

```python
class HallucinationDetectorScanner(NemoGuardRailsScanner):
    """Scanner for detecting hallucinations in assistant responses"""

    def scan(self, messages: List[Dict]) -> Dict:
        # Extract assistant messages
        assistant_messages = [msg for msg in messages if msg.get("type") == "assistant"]

        # ❌ Only analyzes the LAST message
        last_message = assistant_messages[-1]["content"]

        # Uses heuristic pattern matching (not NeMo AI)
        # ...
```

### What It Does

The scanner examines the **last assistant response** for 7 types of hallucination patterns:

1. **Over-specification** (excessive precision)
2. **Fabricated sources** (fake citations)
3. **Impossible details** (logical contradictions)
4. **Over-elaboration** (unnecessary detail)
5. **Confidence undermining** (hedging + specifics)
6. **Unverifiable sensory details** (subjective claims)
7. **Fabricated technical specs** (fake model numbers)

### What It Does NOT Do

❌ **Cross-message contradiction detection** - Does not compare multiple assistant responses
❌ **Conversation-wide consistency** - Does not track claims across the session
❌ **NeMo AI analysis** - Uses heuristics only, not LLM-powered detection
❌ **Memory of previous claims** - Each scan is independent

---

## Detailed Pattern Analysis

### 1. Over-Specification Patterns

Detects excessive precision that suggests fabrication:

```python
over_specification = [
    # Too many precise numbers (>5 numbers in response)
    len([word for word in words if word.isdigit()]) > 5,

    # Overly precise measurements
    " 23.7", " 47.2", " 12.8", " 235.4", " 1013.25",

    # Suspicious precision markers
    "exactly...degrees", "precisely...degrees", "specifically...degrees",

    # Fake technical identifiers
    "coordinates", "sensor ID #4472-XR", "device #", "serial number",

    # False authority
    "measured by", "recorded at", "detected by",

    # Impossible precision on subjectives
    "exactly happy", "precisely beautiful", "specifically comfortable"
]
```

**Example Detection:**
```
"The temperature is exactly 23.7°C with humidity precisely at 47.2%
measured by sensor ID #4472-XR at coordinates 40.7589,-73.9851"
```
→ Detected: 3 over-specification patterns

### 2. Fabricated Sources

Detects fake citations and vague references:

```python
fabricated_sources = [
    # Vague memory claims
    "as i recall", "if i remember", "i believe i read", "i think i saw",
    "i once heard", "someone told me", "i'm pretty sure",

    # Fake academic sources (without real journals)
    "journal of" + no mention of "nature/science/medical",
    "institute of", "association of",

    # Non-existent studies
    "recent study by...university", "research conducted by...university",

    # Fabricated quotes (>2 quotes with attribution)
    Multiple quotes + "said", "stated", "mentioned"
]
```

**Example Detection:**
```
"As I recall from the Journal of Advanced Meteorology,
someone told me the air smells like blue silence"
```
→ Detected: 2 fabricated source patterns

### 3. Impossible Details

Detects logical contradictions within the same message:

```python
impossible_details = [
    # Weather contradictions
    "sunny" + "rain" (in short message),
    "hot" + "freezing",
    "clear sky" + "cloudy",

    # Geographic impossibilities
    "north" + "south" + "of",
    "mountain" + "sea level" (in short message),

    # Temporal impossibilities
    "yesterday" + "next week",
    "currently" + "in the past"
]
```

**Example Detection:**
```
"The weather is sunny with rain falling upward
in the freezing hot climate at sea level mountains"
```
→ Detected: 3 impossible detail patterns

### 4. Over-Elaboration

Detects unnecessary verbosity and detail:

```python
over_elaboration = [
    # Too many adverbs (>8 words ending in 'ly')
    len([word for word in words if word.endswith('ly')]) > 8,

    # Too many gerunds (>10 words ending in 'ing')
    len([word for word in words if word.endswith('ing')]) > 10,

    # Excessive superlatives (>3 total)
    "most", "best", "largest", "smallest", "fastest",

    # Unnecessary technical jargon
    "algorithm", "calibration", "frequency", "wavelength" (without context),

    # Lists with excessive detail (>15 commas in <500 chars)
    message_lower.count(',') > 15
]
```

### 5. Confidence Undermining

Detects hedging combined with false specifics:

```python
confidence_undermining = [
    # Uncertainty + numbers
    ("i think" or "maybe" or "perhaps") + >3 numbers,

    # Hedging + precision
    ("not sure" or "might be") + ("exactly" or "precisely"),

    # Probability hedging + statistics
    ("probably" or "likely") + multiple percentages,

    # Long hedged statements
    "could be" + message >200 chars
]
```

**Example Detection:**
```
"I think the temperature is exactly 23.7°C, maybe 47.2% humidity,
perhaps 1013.25 hPa pressure - not sure but precisely measured"
```
→ Detected: 2 confidence undermining patterns

### 6. Unverifiable Sensory Details

Detects subjective claims presented as facts:

```python
unverifiable_sensory = [
    # Sensory claims without context
    "smells like", "sounds like", "feels like", "tastes like" (in short message),
    "texture of", "aroma of", "sound of" (without "description"),

    # Impossible sensory claims
    "color of silence", "sound of color", "taste of number"
]
```

**Example Detection:**
```
"The air smells like blue silence at wavelength 475.3 nanometers,
with a texture of crystallized sound"
```
→ Detected: 2 unverifiable sensory patterns

### 7. Fabricated Technical Specifications

Detects fake technical details:

```python
technical_fabrication = [
    # Made-up version numbers
    "v2.", "v3.", "model ", "version " + digits,

    # Fake hardware specs
    ("ghz" or "ram" or "processor" or "cpu") + multiple numbers,

    # Software version claims
    "beta version", "alpha build", "patch 1."
]
```

---

## Scoring System

### Risk Level Calculation

```python
total_indicators = (over_spec_count + fabricated_count + impossible_count +
                   elaboration_count + confidence_count + sensory_count +
                   technical_count)

if total_indicators >= 6:
    risk_level = "severe"
    confidence = 0.1  # 10% confidence in accuracy

elif total_indicators >= 4:
    risk_level = "high"
    confidence = 0.2  # 20% confidence

elif total_indicators >= 2:
    risk_level = "moderate"
    confidence = 0.4  # 40% confidence

elif total_indicators == 1:
    risk_level = "mild"
    confidence = 0.7  # 70% confidence

else:
    risk_level = "minimal"
    confidence = 0.9  # 90% confidence
```

### Decision Logic

```python
if has_hallucination_risk:
    decision = "HUMAN_IN_THE_LOOP"  # Requires human review
else:
    decision = "ALLOW"  # Safe to proceed
```

---

## Example Detection

### Test Scenario

```python
{
    "type": "assistant",
    "content": """I think the temperature is exactly 23.7°C with humidity
    precisely at 47.2% and barometric pressure of 1013.25 hPa, measured by
    sensor ID #4472-XR at coordinates 40.7589,-73.9851. The device model
    WeatherTracker v3.2.1 beta version recorded these using algorithm
    calibration frequency 12.8 GHz with 4GB RAM processor. As I recall from
    the Journal of Advanced Meteorology, the air smells like blue silence
    at wavelength 475.3 nanometers, with a texture of crystallized sound.
    Someone told me the mountain peaks are at sea level here, with sunny
    rain falling upward in the freezing hot climate. I believe I saw that
    the color of wind tastes exactly like the number 7, specifically measured
    by the Institute of Impossible Weather Studies."""
}
```

### Detection Result

```json
{
  "scanner": "HallucinationDetector",
  "decision": "HUMAN_IN_THE_LOOP",
  "score": 0.1,
  "reason": "Advanced analysis: Severe hallucination risk - 6 over-specification pattern(s), 3 fabricated source(s), 3 impossible detail(s), 2 over-elaboration pattern(s), 2 confidence-undermining pattern(s), 3 unverifiable sensory detail(s), 2 fabricated technical spec(s)",
  "is_safe": false
}
```

**Total Indicators:** 21 patterns detected → Severe risk

---

## Limitations of Current Implementation

### ❌ What It CANNOT Detect

1. **Cross-Message Contradictions**
   ```
   Message 1: "The capital of France is Paris"
   Message 2: "The capital of France is London"
   ```
   → ❌ Not detected (only looks at Message 2)

2. **Conversation-Wide Inconsistencies**
   ```
   Message 1: "I don't have access to real-time weather data"
   Message 2: "The current temperature is exactly 23.7°C"
   ```
   → ❌ Not detected (doesn't compare with previous messages)

3. **Subtle Factual Drift**
   ```
   Message 1: "The population is approximately 5 million"
   Message 2: "The population is exactly 4,847,293"
   Message 3: "The population is around 6 million"
   ```
   → ❌ Not detected (doesn't track claims across conversation)

4. **Context-Dependent Hallucinations**
   ```
   User: "What did you say about the weather?"
   Assistant: "I said it was sunny" (but previously said rainy)
   ```
   → ❌ Not detected (no memory of previous statements)

---

## Comparison: Current vs. Ideal Implementation

### Current Implementation (Heuristic-Only)

```
✅ Detects single-message hallucination patterns
✅ Fast (no LLM calls)
✅ Deterministic results
✅ No API costs
✅ Privacy-preserving (no external calls)

❌ Only analyzes last message
❌ No cross-message comparison
❌ Pattern-based only (not semantic)
❌ Can't understand context
❌ No conversation memory
```

### Ideal NeMo-Powered Implementation

```
✅ Cross-message contradiction detection
✅ Conversation-wide consistency checking
✅ Semantic understanding (not just patterns)
✅ Context-aware analysis
✅ Memory of previous claims
✅ Natural language reasoning

❌ Slower (multiple LLM calls)
❌ Non-deterministic results
❌ API costs (OpenAI charges)
❌ Requires external API access
```

---

## How to Detect Cross-Conversation Contradictions

### Your Question:
> "Will it detect contradictions in different answers from the assistant, within the same user session (conversation)?"

**Answer:** ❌ **No, the current implementation does NOT.**

### Why Not?

```python
# Current implementation (line 365)
last_message = assistant_messages[-1]["content"]
# ↑ Only uses the LAST message, ignores all previous ones
```

### What You Need: Conversation-Wide Analysis

To detect cross-message contradictions, you need to implement:

#### Option 1: NeMo-Powered Consistency Checking

```python
class HallucinationDetectorScanner(NemoGuardRailsScanner):

    def __init__(self):
        """Initialize with NeMo GuardRails for consistency checking"""
        if NEMO_GUARDRAILS_AVAILABLE:
            config = RailsConfig.from_path("nemo_config/")
            self.rails = LLMRails(config)
        else:
            self.rails = None

    def scan(self, messages: List[Dict]) -> Dict:
        """Scan for hallucinations across ALL assistant messages"""

        # Extract ALL assistant messages (not just last)
        assistant_messages = [msg for msg in messages
                            if msg.get("type") == "assistant"]

        if len(assistant_messages) < 2:
            # Can't check consistency with <2 messages
            return self._single_message_scan(assistant_messages[-1])

        # Check consistency across multiple messages
        return self._consistency_scan(assistant_messages)

    def _consistency_scan(self, messages: List[Dict]) -> Dict:
        """Check consistency across multiple assistant responses"""

        if self.rails is None:
            return {"error": "NeMo GuardRails not available"}

        # Build prompt for NeMo to check consistency
        combined_text = "\n\n".join([
            f"Response {i+1}: {msg['content']}"
            for i, msg in enumerate(messages)
        ])

        prompt = f"""Analyze these responses from the same AI assistant
        in a single conversation. Identify any contradictions, inconsistencies,
        or claims that conflict with each other:

        {combined_text}

        Report any contradictions found."""

        # Use NeMo to analyze
        response = self.rails.generate(prompt=prompt)

        # Parse NeMo's analysis
        nemo_response = str(response).lower()

        has_contradictions = any([
            "contradiction" in nemo_response,
            "inconsistent" in nemo_response,
            "conflicts with" in nemo_response,
            "contrary to" in nemo_response
        ])

        return {
            "scanner": "HallucinationDetector",
            "decision": "BLOCK" if has_contradictions else "ALLOW",
            "score": 0.2 if has_contradictions else 0.9,
            "reason": f"Consistency check: {nemo_response[:300]}...",
            "is_safe": not has_contradictions,
            "analysis_method": "NeMo Cross-Message Analysis"
        }
```

#### Option 2: Claim Extraction & Tracking

```python
class ClaimTracker:
    """Track claims across conversation for consistency"""

    def __init__(self):
        self.claims = {}  # {topic: [claims]}

    def extract_claims(self, message: str) -> List[Dict]:
        """Extract factual claims from message"""
        # Use NeMo or LLM to extract claims
        prompt = f"Extract factual claims from: {message}"
        # ...
        return claims

    def check_consistency(self, new_message: str) -> Dict:
        """Check if new message contradicts previous claims"""
        new_claims = self.extract_claims(new_message)

        contradictions = []
        for claim in new_claims:
            for topic, previous_claims in self.claims.items():
                if self._claims_contradict(claim, previous_claims):
                    contradictions.append({
                        "new": claim,
                        "previous": previous_claims
                    })

        return {
            "has_contradictions": len(contradictions) > 0,
            "contradictions": contradictions
        }
```

---

## Recommended Improvements

### 1. Enable NeMo AI Analysis

**File:** `multi_agent_demo/scanners/nemo_scanners.py`

**Current:**
```python
class HallucinationDetectorScanner(NemoGuardRailsScanner):
    def scan(self, messages: List[Dict]) -> Dict:
        # Use enhanced heuristic analysis directly
        # ↑ NO NeMo integration
```

**Improved:**
```python
class HallucinationDetectorScanner(NemoGuardRailsScanner):
    def __init__(self):
        """Initialize with NeMo GuardRails"""
        if NEMO_GUARDRAILS_AVAILABLE:
            config = RailsConfig.from_path("nemo_config/")
            self.rails = LLMRails(config)
        else:
            self.rails = None

    def scan(self, messages: List[Dict]) -> Dict:
        if self.rails is not None:
            return self._nemo_hallucination_check(messages)
        else:
            return self._heuristic_check(messages)  # Fallback
```

### 2. Add Conversation Memory

```python
class ConversationMemory:
    """Remember claims across conversation"""

    def __init__(self):
        self.message_history = []
        self.claim_registry = {}

    def add_message(self, message: Dict):
        self.message_history.append(message)
        # Extract and register claims

    def check_new_message(self, message: Dict) -> List[str]:
        """Return list of contradictions with previous messages"""
        # Compare with history
        return contradictions
```

### 3. Configure NeMo for Hallucination Detection

**File:** `nemo_config/config.yml`

**Add:**
```yaml
prompts:
  - task: check_hallucination
    content: |
      Analyze the following AI assistant response for signs of hallucination:

      {{ bot_response }}

      Check for:
      1. Fabricated sources or citations
      2. Overly specific numbers without justification
      3. Impossible or contradictory claims
      4. Unverifiable sensory details
      5. Fake technical specifications

      Previous responses in this conversation:
      {{ conversation_history }}

      Report any hallucinations or contradictions with previous responses.

rails:
  output:
    flows:
      - check hallucination
```

---

## Action Items for Cross-Conversation Detection

To make the HallucinationDetector detect contradictions across messages:

### Phase 1: Enable NeMo Integration (Similar to FactChecker)

1. **Initialize NeMo in `__init__`**
   - Load RailsConfig from `nemo_config/`
   - Create LLMRails instance
   - Add error handling

2. **Create `_nemo_hallucination_check` method**
   - Accept ALL messages (not just last)
   - Build prompt with conversation history
   - Send to NeMo for analysis
   - Parse response for contradictions

3. **Keep heuristic as fallback**
   - Use heuristics when NeMo unavailable
   - Combine both for best results

### Phase 2: Add Conversation Context

1. **Pass all assistant messages to NeMo**
   ```python
   assistant_history = "\n\n".join([
       f"Previous response {i+1}: {msg['content']}"
       for i, msg in enumerate(assistant_messages[:-1])
   ])

   current_message = assistant_messages[-1]['content']

   prompt = f"""Previous responses:
   {assistant_history}

   Current response:
   {current_message}

   Check for contradictions."""
   ```

2. **Update NeMo config with history-aware prompt**

### Phase 3: Implement Claim Tracking (Advanced)

1. Extract claims from each message
2. Store in registry with timestamps
3. Check new claims against registry
4. Report contradictions with references

---

## Summary

| Feature | Current Status | Ideal State |
|---------|----------------|-------------|
| **Single-message hallucination patterns** | ✅ Implemented (heuristics) | ✅ Enhanced with NeMo |
| **Cross-message contradictions** | ❌ Not implemented | ✅ NeMo-powered |
| **Conversation-wide consistency** | ❌ Not implemented | ✅ Claim tracking |
| **NeMo AI integration** | ❌ Not used | ✅ Fully integrated |
| **Memory of previous claims** | ❌ No memory | ✅ Conversation context |
| **Cost & Speed** | ✅ Fast, free | ⚠️ Slower, costs $ |

**To Answer Your Question:**
> Will it detect contradictions in different answers from the assistant, within the same user session (conversation)?

**Current Answer:** ❌ **No** - Only analyzes last message with pattern matching

**After Improvement:** ✅ **Yes** - Can detect cross-message contradictions using NeMo GuardRails with conversation history

---

## Next Steps

Would you like me to:

1. **Implement NeMo-powered cross-message detection** (like FactChecker)?
2. **Add conversation memory and claim tracking**?
3. **Create a hybrid approach** (heuristics + NeMo for best results)?
4. **Keep current implementation** but document limitations clearly?

Let me know which direction you'd prefer!