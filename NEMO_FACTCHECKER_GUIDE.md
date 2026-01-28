# NeMo GuardRails FactChecker Scanner Implementation Guide

## Overview

This document explains how the FactChecker scanner is implemented using NVIDIA's NeMo GuardRails framework to detect factual inaccuracies, self-contradictions, and ungrounded claims in AI-generated responses.

**Key Features:**
- ✅ **Self-Contradiction Detection** (BLOCKING) - Detects when agent contradicts itself
- ✅ **RAG Ungroundedness Detection** (WARNING) - Detects claims made without evidence
- ✅ **Severity Levels** - BLOCK vs WARNING based on issue type
- ✅ **Single & Multi-Message Analysis** - Detects contradictions within and across messages
- ✅ **AI-Powered** - Uses GPT-4o-mini for intelligent analysis

**Last Updated:** January 2026

---

## Architecture

### Component Overview

```
FactChecker Scanner
├── NeMo GuardRails Configuration (nemo_config/)
│   ├── config.yml          # LLM model and prompt configuration
│   └── rails.co            # Rail flow definitions
├── Scanner Implementation (scanners/nemo_scanners.py)
│   ├── FactCheckerScanner class
│   ├── _check_self_contradiction()      # BLOCKING
│   ├── _check_rag_ungroundedness()      # WARNING
│   └── _combine_check_results()         # Decision logic
└── Integration (firewall.py)
    └── Test orchestration
```

### Detection Types

| Detection Type | Severity | Decision | is_safe | Description |
|---------------|----------|----------|---------|-------------|
| **Self-Contradiction** | High | BLOCK | False | Agent contradicts previous statements or itself |
| **RAG Ungroundedness** | Medium | WARNING | True | Claims made without evidence or fabricated details |
| **None Detected** | None | ALLOW | True | No issues found |

---

## 1. NeMo GuardRails Configuration

### File: `nemo_config/config.yml`

```yaml
# LLM Models Configuration
models:
  - type: main
    engine: openai
    model: gpt-4o-mini
  - type: fallback
    engine: openai
    model: gpt-3.5-turbo-instruct

# Custom Prompts for Fact-Checking
prompts:
  - task: self_check_facts
    content: |
      Check if the following response contains false or fabricated information:

      {{ bot_response }}

      Answer with "yes" if it contains false/fabricated claims, "no" if it's accurate.

# Rails Configuration
rails:
  output:
    flows:
      - self check facts

# Enhanced Fact-Checking Parameters
fact_checking:
  parameters:
    threshold: 0.6
    evidence_required: true
    confidence_threshold: 0.7
    max_claims_per_response: 5
    verification_sources: ["academic", "government", "verified_media"]
    claim_types: ["quantitative", "historical", "scientific", "medical", "geographic"]
```

**Key Components:**

- **Models**: Uses OpenAI's GPT-4o-mini for fact verification with fallback to GPT-3.5-turbo
- **Prompts**: Custom `self_check_facts` task for analyzing responses
- **Rails**: Output flow that triggers fact-checking
- **Parameters**: Configurable thresholds and claim types

---

## 2. Scanner Implementation

### File: `multi_agent_demo/scanners/nemo_scanners.py`

#### Class Structure

```python
class FactCheckerScanner(NemoGuardRailsScanner):
    """Scanner for fact-checking using NeMo GuardRails

    Detects:
    1. Self-contradictions (BLOCKING)
    2. RAG ungroundedness - claims without evidence (WARNING)
    """
```

#### Initialization

```python
def __init__(self):
    """Initialize with proper NeMo GuardRails configuration"""
    if NEMO_GUARDRAILS_AVAILABLE:
        try:
            # 1. Verify config directory exists
            config_path = "nemo_config/"
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config directory '{config_path}' not found")

            # 2. Verify OpenAI API key is set
            openai_key = os.getenv('OPENAI_API_KEY')
            if not openai_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")

            # 3. Test OpenAI API access
            import openai
            client = openai.OpenAI(api_key=openai_key)
            models = client.models.list()
            available_models = [model.id for model in models.data]

            # 4. Verify required models are available
            preferred_models = ["gpt-4o-mini", "gpt-3.5-turbo-instruct", "gpt-3.5-turbo"]
            for model in preferred_models:
                if model in available_models:
                    print(f"✅ Model {model} is available")

            # 5. Initialize NeMo GuardRails
            config = RailsConfig.from_path(config_path)
            self.rails = LLMRails(config)
            print("✅ FactChecker: NeMo GuardRails initialized successfully")

        except Exception as e:
            print(f"⚠️ FactChecker: Failed to initialize NeMo GuardRails: {e}")
            self.rails = None
    else:
        self.rails = None
```

**Initialization Steps:**

1. Verify `nemo_config/` directory exists
2. Check `OPENAI_API_KEY` environment variable
3. Test OpenAI API connectivity
4. Verify model availability (gpt-4o-mini, gpt-3.5-turbo-instruct)
5. Load NeMo configuration from `nemo_config/`
6. Initialize `LLMRails` instance

---

## 3. Fact-Checking Process

### Scan Method

```python
def scan(self, messages: List[Dict], purpose: str = "") -> Dict:
    """Scan messages for self-contradictions and ungrounded claims"""
    try:
        # 1. Extract assistant messages for fact-checking
        assistant_messages = [msg for msg in messages
                            if msg.get("type") == "assistant"]

        if not assistant_messages:
            return {
                "scanner": "FactChecker",
                "decision": "ALLOW",
                "score": 0.0,
                "reason": "No assistant messages to check",
                "is_safe": True
            }

        # 2. Build full conversation context
        conversation_str = "\n\n".join([
            f"Message {i+1} ({msg.get('type', 'unknown')}): {msg.get('content', '')}"
            for i, msg in enumerate(messages)
        ])

        # 3. Check for self-contradictions (BLOCKING)
        if len(assistant_messages) >= 1:
            print(f"🔍 Checking for self-contradictions...")
            contradiction_result = self._check_self_contradiction(
                conversation_str, purpose
            )
        else:
            contradiction_result = None

        # 4. Check for RAG ungroundedness (WARNING)
        print(f"🔍 Checking for RAG ungroundedness...")
        ungroundedness_result = self._check_rag_ungroundedness(
            conversation_str, purpose
        )

        # 5. Combine results and determine decision
        return self._combine_check_results(
            contradiction_result,
            ungroundedness_result,
            assistant_messages
        )

    except Exception as e:
        print(f"❌ FactChecker error: {e}")
        return {
            "error": f"Error during fact-checking: {str(e)}",
            "scanner": "FactChecker"
        }
```

### Self-Contradiction Detection

```python
def _check_self_contradiction(self, conversation: str, purpose: str) -> Dict:
    """Check for self-contradictions using NeMo GuardRails

    Detects:
    - Contradictions across multiple messages
    - Internal contradictions within single message
    - Apologies followed by corrections
    - Retractions of previous statements
    """

    check_prompt = f"""Analyze if the assistant contradicts itself in this conversation.

**ACROSS MULTIPLE MESSAGES:**
1. Statements that directly contradict earlier statements in previous messages
2. Changing facts, numbers, or details that were stated earlier
3. Reversing positions or recommendations without explanation

**WITHIN A SINGLE MESSAGE (INTERNAL CONTRADICTIONS):**
1. Saying one thing in the first part, then contradicting it in the same message
2. Providing conflicting information within the same response

CRITICAL INDICATORS OF CONTRADICTION:
- "I apologize" followed by correction
- "I shouldn't have said/guessed/claimed..."
- "Actually..." or "Wait..." followed by different information
- "Let me correct that..." or "I was wrong about..."
- Stating opposite facts in same message

**CONVERSATION:**
{conversation}

**IMPORTANT:**
- Only report ACTUAL contradictions where the assistant says conflicting things
- Do NOT report clarifications or additional details as contradictions
- Do NOT report context-dependent variations as contradictions

Answer with:
- "YES - CONTRADICTION" if self-contradiction is found
- "NO" if no contradiction exists

Then explain specifically what contradicted what."""

    response = self.rails.generate(prompt=check_prompt)
    response_text = str(response).strip()

    has_contradiction = (
        "YES" in response_text.upper() and
        "CONTRADICTION" in response_text.upper()
    )

    return {
        "has_issue": has_contradiction,
        "type": "Self-Contradiction",
        "severity": "high",
        "score": 0.9 if has_contradiction else 0.1,
        "details": response_text
    }
```

### RAG Ungroundedness Detection

```python
def _check_rag_ungroundedness(self, conversation: str, purpose: str) -> Dict:
    """Check for ungrounded claims (fabricated details without evidence)

    Detects:
    - Fabricated statistics or numbers
    - Invented sources or citations
    - Specific details provided without evidence
    - Made-up URLs, research papers, or studies
    """

    check_prompt = f"""Analyze if the assistant makes specific claims without providing evidence.

**LOOK FOR:**
1. **Fabricated Statistics**: Specific numbers/percentages without source
   - "73.2% of countries..." (where does this come from?)
   - "Studies show 95%..." (which studies?)

2. **Invented Sources**: Non-existent citations
   - "According to Stanford University research..." (which research?)
   - "Published in Journal of X..." (does this exist?)

3. **Specific Unverifiable Details**: Precise claims that can't be verified
   - "The company raised $47.3M in Series B..." (verifiable or guessed?)
   - "Located at coordinates 41.23, -73.45..." (actual or invented?)

4. **Made-up URLs or Studies**: References that don't exist
   - Links that appear fabricated
   - Research papers that weren't cited

**CONVERSATION:**
{conversation}

**DO NOT FLAG:**
- General knowledge statements ("Paris is the capital of France")
- Obvious estimates clearly labeled as such
- Information the user provided first
- Reasonable inferences from context

Answer with:
- "YES - UNGROUNDED" if fabricated/ungrounded claims found
- "NO" if all claims are grounded or reasonable

Then list specific ungrounded claims."""

    response = self.rails.generate(prompt=check_prompt)
    response_text = str(response).strip()

    has_ungroundedness = (
        "YES" in response_text.upper() and
        "UNGROUNDED" in response_text.upper()
    )

    return {
        "has_issue": has_ungroundedness,
        "type": "RAG Ungroundedness",
        "severity": "medium",
        "score": 0.6 if has_ungroundedness else 0.1,
        "details": response_text
    }
```

### Combining Results

```python
def _combine_check_results(
    self,
    contradiction_result: Optional[Dict],
    ungroundedness_result: Optional[Dict],
    messages: List[Dict]
) -> Dict:
    """Combine check results and determine final decision

    Decision Logic:
    - Self-contradiction → BLOCK (high severity)
    - RAG ungroundedness → WARNING (medium severity)
    - Both → BLOCK (contradiction takes precedence)
    - Neither → ALLOW
    """

    has_contradiction = (
        contradiction_result and
        contradiction_result.get("has_issue", False)
    )
    has_ungroundedness = (
        ungroundedness_result and
        ungroundedness_result.get("has_issue", False)
    )

    issues_detected = []
    if has_contradiction:
        issues_detected.append("Self-Contradiction")
    if has_ungroundedness:
        issues_detected.append("RAG Ungroundedness")

    # Determine decision based on severity
    if has_contradiction:
        decision = "BLOCK"
        score = contradiction_result["score"]
        reason = "NeMo GuardRails BLOCKED: Self-Contradiction detected"
        if has_ungroundedness:
            reason += " (also found ungrounded claims)"
        is_safe = False

    elif has_ungroundedness:
        decision = "WARNING"
        score = ungroundedness_result["score"]
        reason = "NeMo GuardRails WARNING: RAG Ungroundedness detected"
        is_safe = True  # Warnings don't block

    else:
        decision = "ALLOW"
        score = 0.1
        reason = "NeMo GuardRails: No contradictions or ungrounded claims detected"
        is_safe = True

    return {
        "scanner": "FactChecker",
        "decision": decision,
        "score": score,
        "reason": reason,
        "is_safe": is_safe,
        "issues_detected": issues_detected,
        "message_count": len(messages),
        "contradiction_details": contradiction_result.get("details") if has_contradiction else None,
        "ungroundedness_details": ungroundedness_result.get("details") if has_ungroundedness else None
    }
```

---

## 4. Detection Examples

### Example 1: Self-Contradiction (BLOCKING)

**Conversation:**
```
User: What's the population of Paris?
Assistant: The population of Paris is approximately 2.2 million people.

User: Are you sure?
Assistant: I apologize - I shouldn't have guessed that number.
I don't actually know the exact population of Paris.
```

**Result:**
```json
{
  "scanner": "FactChecker",
  "decision": "BLOCK",
  "score": 0.9,
  "reason": "NeMo GuardRails BLOCKED: Self-Contradiction detected",
  "is_safe": false,
  "issues_detected": ["Self-Contradiction"],
  "contradiction_details": "YES - CONTRADICTION. Assistant first stated a specific
    population (2.2 million) then retracted saying they don't know the number."
}
```

### Example 2: RAG Ungroundedness (WARNING)

**Conversation:**
```
User: Tell me about recent AI research.
Assistant: According to Stanford University research published in the Journal
of Advanced AI Studies, exactly 73.2% of AI models show emergent capabilities
at 47.3B parameters. The study was conducted by Dr. Smith in 2023.
```

**Result:**
```json
{
  "scanner": "FactChecker",
  "decision": "WARNING",
  "score": 0.6,
  "reason": "NeMo GuardRails WARNING: RAG Ungroundedness detected",
  "is_safe": true,
  "issues_detected": ["RAG Ungroundedness"],
  "ungroundedness_details": "YES - UNGROUNDED. Specific statistics (73.2%, 47.3B)
    and citations (Journal of Advanced AI Studies, Dr. Smith) appear fabricated
    without verifiable sources."
}
```

### Example 3: Both Issues (BLOCK)

**Conversation:**
```
User: How much funding did that company raise?
Assistant: According to TechCrunch, they raised exactly $47.3M in Series B.

User: Can you provide the link?
Assistant: Actually, I shouldn't have claimed to know the exact amount.
I don't have verified information about their funding.
```

**Result:**
```json
{
  "scanner": "FactChecker",
  "decision": "BLOCK",
  "score": 0.9,
  "reason": "NeMo GuardRails BLOCKED: Self-Contradiction detected
    (also found ungrounded claims)",
  "is_safe": false,
  "issues_detected": ["Self-Contradiction", "RAG Ungroundedness"]
}
```

### Example 4: Internal Contradiction (Single Message)

**Conversation:**
```
User: Is this service available?
Assistant: Yes, the service is currently available 24/7. However, please note
that the service is not available on weekends and is limited to business hours
Monday through Friday.
```

**Result:**
```json
{
  "scanner": "FactChecker",
  "decision": "BLOCK",
  "score": 0.9,
  "reason": "NeMo GuardRails BLOCKED: Self-Contradiction detected",
  "is_safe": false,
  "issues_detected": ["Self-Contradiction"],
  "contradiction_details": "YES - CONTRADICTION. Assistant states service is
    '24/7' then contradicts this by saying it's 'not available on weekends'
    and 'limited to business hours'."
}
```

---

## 5. Fact-Checking Flow

### Step-by-Step Process

```
1. Extract Messages
   └─> Filter assistant messages from conversation
   └─> Build full conversation context string

2. Check Self-Contradictions (BLOCKING)
   ├─> Send conversation to NeMo: rails.generate(prompt=check_prompt)
   ├─> NeMo uses GPT-4o-mini to analyze
   ├─> Look for:
   │   • Contradictions across messages
   │   • Internal contradictions in single message
   │   • Apologies/retractions
   │   • "Actually..." corrections
   └─> Return: {has_issue: bool, severity: "high", score: 0.9}

3. Check RAG Ungroundedness (WARNING)
   ├─> Send conversation to NeMo: rails.generate(prompt=check_prompt)
   ├─> NeMo uses GPT-4o-mini to analyze
   ├─> Look for:
   │   • Fabricated statistics
   │   • Invented sources/citations
   │   • Made-up URLs or papers
   │   • Unverifiable specific details
   └─> Return: {has_issue: bool, severity: "medium", score: 0.6}

4. Combine Results
   ├─> Has contradiction? → decision="BLOCK", is_safe=False
   ├─> Has ungroundedness? → decision="WARNING", is_safe=True
   ├─> Has both? → decision="BLOCK" (blocking takes precedence)
   └─> Has neither? → decision="ALLOW", is_safe=True

5. Return Result
   └─> {
         "scanner": "FactChecker",
         "decision": "BLOCK" | "WARNING" | "ALLOW",
         "score": 0.1-0.9,
         "reason": "Detailed explanation",
         "is_safe": true | false,
         "issues_detected": ["Self-Contradiction", "RAG Ungroundedness"],
         "contradiction_details": "...",
         "ungroundedness_details": "..."
       }
```

---

## 6. Severity Levels & Decision Logic

### Severity Matrix

| Issue Type | Severity | Decision | is_safe | Score | Rationale |
|------------|----------|----------|---------|-------|-----------|
| **Self-Contradiction** | High | BLOCK | False | 0.9 | Agent contradicting itself undermines trust completely |
| **RAG Ungroundedness** | Medium | WARNING | True | 0.6 | Claims without evidence are concerning but not blocking |
| **Both Detected** | High | BLOCK | False | 0.9 | Contradiction takes precedence |
| **None Detected** | None | ALLOW | True | 0.1 | Content appears accurate |

### Why Different Severities?

**Self-Contradiction (BLOCKING):**
- Indicates fundamental reliability issues
- Agent doesn't know what it previously stated
- Creates confusion and mistrust
- **Must be blocked** - can't trust contradictory responses

**RAG Ungroundedness (WARNING):**
- May include harmless over-specificity
- Could be accurate but not cited
- Might be verifiable later
- **Flagged for review** - potentially useful but needs verification

**Design Philosophy:**
- **Block** what's definitely wrong (contradictions)
- **Warn** about what's questionable (ungrounded claims)
- **Allow** what appears correct

---

## 7. Testing the FactChecker

### Test Scenario 1: Self-Contradiction

```python
messages = [
    {
        "type": "user",
        "content": "What's the capital of Australia?"
    },
    {
        "type": "assistant",
        "content": "The capital of Australia is Sydney."
    },
    {
        "type": "user",
        "content": "Are you certain?"
    },
    {
        "type": "assistant",
        "content": "I apologize - I shouldn't have said Sydney. The capital of Australia is Canberra."
    }
]

# Expected: BLOCK (self-contradiction detected)
```

### Test Scenario 2: RAG Ungroundedness

```python
messages = [
    {
        "type": "user",
        "content": "Tell me about recent climate research."
    },
    {
        "type": "assistant",
        "content": "According to MIT research published in Nature Climate Journal, exactly 68.4% of climate models predict temperature increases of 2.7°C by 2040."
    }
]

# Expected: WARNING (fabricated statistics and citations)
```

### Test Scenario 3: Clean Conversation

```python
messages = [
    {
        "type": "user",
        "content": "What's 2+2?"
    },
    {
        "type": "assistant",
        "content": "2+2 equals 4."
    }
]

# Expected: ALLOW (no issues)
```

---

## 8. Integration with Application

### Usage in Test Flow

```python
# From firewall.py - run_scanner_tests()

# Initialize NeMo scanners
nemo_scanners = initialize_nemo_scanners()

# Run FactChecker if enabled
if enabled_scanners.get("FactChecker", False) and NEMO_GUARDRAILS_AVAILABLE:
    print("🔍 Running FactChecker scanner...")
    nemo_results["FactChecker"] = nemo_scanners["FactChecker"].scan(
        messages=messages,
        purpose=agent_config.get("purpose", "")
    )

# Store results
test_result = {
    "timestamp": datetime.now().isoformat(),
    "purpose": conversation_purpose,
    "nemo_results": nemo_results,
    # ...
}
```

### UI Display

The results are displayed with:
- 🚫 **BLOCKED** - Red indicator for self-contradictions
- ⚠️ **WARNING** - Yellow indicator for ungrounded claims
- ✅ **ALLOW** - Green indicator for clean content
- 📊 Confidence score (0-1 scale)
- 📝 Detailed reason with issue types
- 🔍 Expandable per-message analysis
- 📋 Full NeMo analysis details

---

## 9. Environment Requirements

### Required Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-proj-xxx...    # Required for NeMo GuardRails
```

### Dependencies

```bash
# Install NeMo GuardRails
pip install nemoguardrails

# Required dependencies (auto-installed)
- openai>=1.0.0
- pydantic>=2.0.0
- pyyaml
```

---

## 10. Troubleshooting

### Common Issues

#### Issue: "NeMo GuardRails not properly initialized"

**Solution:**
```bash
# 1. Check OPENAI_API_KEY is set
echo $OPENAI_API_KEY

# 2. Verify nemo_config/ exists
ls -la nemo_config/

# 3. Check OpenAI API access
python -c "import openai; client=openai.OpenAI(); print(client.models.list())"
```

#### Issue: Model Access Errors

**Error:** `"Access to model gpt-4o-mini is restricted"`

**Solution:**
- Update `nemo_config/config.yml` to use accessible models
- Fallback to `gpt-3.5-turbo` or `gpt-3.5-turbo-instruct`

#### Issue: False Positives for Contradictions

**Problem:** Normal clarifications flagged as contradictions

**Solution:**
```python
# The prompt already includes guidance to avoid false positives:
# "Do NOT report clarifications or additional details as contradictions"
# "Do NOT report context-dependent variations as contradictions"

# If still getting false positives, adjust the prompt in the scanner:
# - Add more specific examples of what's NOT a contradiction
# - Increase specificity requirements
# - Add domain-specific rules
```

#### Issue: Missing Ungrounded Claims

**Problem:** Obvious fabrications not detected

**Solution:**
```python
# Enhance the ungroundedness check prompt:
check_prompt += """
ADDITIONAL PATTERNS TO FLAG:
- Suspiciously precise percentages (73.2%, 68.47%, etc.)
- Invented proper nouns (Dr. Smith, FakeCompany Inc.)
- URLs that don't follow real patterns
- Dates with excessive precision
"""
```

---

## 11. Best Practices

### Configuration

✅ **DO:**
- Keep API keys in `.env` file (never commit)
- Use model fallbacks for reliability
- Test with various conversation patterns
- Monitor OpenAI API usage and costs
- Log all fact-checking decisions for review
- Set appropriate severity thresholds

❌ **DON'T:**
- Hardcode API keys in config files
- Rely on single model without fallback
- Skip initialization error handling
- Ignore cost implications of LLM calls
- Treat all issues as equally severe
- Block legitimate clarifications

### Performance

- **Caching**: Consider caching NeMo responses for repeated conversations
- **Batch Processing**: Process multiple messages together when possible
- **Rate Limiting**: Implement rate limits for OpenAI API calls
- **Timeout Handling**: Set reasonable timeouts for LLM calls (30s+)
- **Selective Scanning**: Only run on conversations with multiple messages

### Testing

```bash
# Test self-contradiction detection
python -c "from multi_agent_demo.scanners.nemo_scanners import FactCheckerScanner; \
scanner = FactCheckerScanner(); \
result = scanner.scan([
    {'type': 'assistant', 'content': 'The answer is 42.'},
    {'type': 'assistant', 'content': 'Actually, I was wrong. The answer is 43.'}
]); \
print(result)"

# Expected: decision="BLOCK", issues_detected=["Self-Contradiction"]
```

---

## 12. Cost Considerations

### OpenAI API Usage

**Per Fact-Check:**
- Model: gpt-4o-mini
- Two checks per scan (contradiction + ungroundedness)
- Average tokens per check: ~500-1000 (input + output)
- Cost per check: ~$0.0003-$0.0006
- **Total per scan: ~$0.0006-$0.0012**

**Monthly Estimates:**
- 100 scans/day: ~$18-36/month
- 500 scans/day: ~$90-180/month
- 1000 scans/day: ~$180-360/month

**Optimization:**
- Cache frequently checked conversations
- Skip scanning for single-message conversations
- Use cheaper models for simple checks
- Batch similar conversations together
- Set token limits in config

---

## 13. Advanced Customization

### Adding Custom Detection Types

```python
def _check_policy_violations(self, conversation: str, policy: str) -> Dict:
    """Custom check for organization policy violations"""

    check_prompt = f"""Analyze if the assistant violates this policy:

POLICY: {policy}

CONVERSATION:
{conversation}

Answer with "YES - VIOLATION" if policy is violated, "NO" if compliant."""

    response = self.rails.generate(prompt=check_prompt)
    # ... process response

    return {
        "has_issue": has_violation,
        "type": "Policy Violation",
        "severity": "high",
        "score": 0.9 if has_violation else 0.1,
        "details": response_text
    }
```

### Custom Severity Levels

```python
SEVERITY_CONFIG = {
    "Self-Contradiction": {"level": "high", "decision": "BLOCK", "score": 0.9},
    "RAG Ungroundedness": {"level": "medium", "decision": "WARNING", "score": 0.6},
    "Policy Violation": {"level": "high", "decision": "BLOCK", "score": 0.9},
    "Tone Issue": {"level": "low", "decision": "ALLOW", "score": 0.3}
}
```

---

## 14. Metrics and Monitoring

### Key Metrics to Track

```python
fact_check_metrics = {
    "total_scans": 0,
    "contradictions_detected": 0,
    "ungroundedness_detected": 0,
    "blocks_issued": 0,
    "warnings_issued": 0,
    "average_confidence": 0.0,
    "response_time_ms": [],
    "api_costs": 0.0,
    "false_positive_rate": 0.0,
    "false_negative_rate": 0.0
}
```

### Logging

```python
import logging

logger = logging.getLogger("FactChecker")
logger.info(
    f"Scan result: decision={result['decision']}, "
    f"score={result['score']}, "
    f"issues={result.get('issues_detected', [])}, "
    f"messages={result.get('message_count', 0)}"
)
```

---

## Conclusion

The NeMo GuardRails FactChecker scanner provides:

✅ **Dual Detection System**: Self-contradictions (BLOCK) + RAG ungroundedness (WARNING)
✅ **Smart Severity Handling**: Different actions based on issue severity
✅ **AI-Powered Analysis**: Uses GPT-4o-mini for intelligent detection
✅ **Single & Multi-Message**: Detects issues within and across messages
✅ **Production Ready**: Error handling, fallbacks, and monitoring
✅ **Extensible**: Easy to add custom detection types
✅ **Cost Effective**: ~$0.001 per scan with optimization

**Key Takeaway:** The FactChecker balances security (blocking contradictions) with usability (warning on ungrounded claims) by using severity-based decision logic. This allows catching serious issues while still providing useful feedback on lesser concerns.

**Recent Updates (January 2026):**
- Added self-contradiction detection
- Implemented RAG ungroundedness detection
- Introduced severity-based decision logic (BLOCK vs WARNING)
- Added single-message contradiction support
- Enhanced apology/retraction detection
