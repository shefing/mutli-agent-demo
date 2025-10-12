"""
DataDisclosureGuard Scanner

Detects PII disclosure in user and assistant messages and validates if the disclosure
is aligned with the user's intent using a two-stage approach:
1. Stage 1: Presidio PII Detection - identifies sensitive data being shared
2. Stage 2: AlignmentCheck - validates if PII disclosure aligns with user intent
"""

from typing import List, Dict, Optional
import os
import warnings
import logging

# Suppress Presidio warnings about language support and default configs
warnings.filterwarnings("ignore", category=UserWarning, module="presidio_analyzer")
logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)


class DataDisclosureGuardScanner:
    """
    Scanner that detects PII disclosure and validates alignment with user intent

    Uses Microsoft Presidio for PII detection and LlamaFirewall AlignmentCheck
    for intent validation.
    """

    def __init__(self):
        """Initialize the DataDisclosureGuard scanner"""
        self.presidio_available = False
        self.analyzer = None

        try:
            from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
            from presidio_analyzer.nlp_engine import NlpEngineProvider

            # Create custom SSN recognizer with explicit patterns
            ssn_patterns = [
                Pattern(
                    name="ssn_pattern",
                    regex=r"\b\d{3}-\d{2}-\d{4}\b",  # XXX-XX-XXXX
                    score=0.9
                ),
                Pattern(
                    name="ssn_no_dash",
                    regex=r"\b\d{9}\b",  # XXXXXXXXX
                    score=0.7
                ),
            ]

            ssn_recognizer = PatternRecognizer(
                supported_entity="US_SSN",
                patterns=ssn_patterns,
                context=["ssn", "social security", "social security number"]
            )

            # Create custom credit card recognizer
            cc_patterns = [
                Pattern(
                    name="cc_pattern",
                    regex=r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # XXXX-XXXX-XXXX-XXXX
                    score=0.9
                ),
            ]

            cc_recognizer = PatternRecognizer(
                supported_entity="CREDIT_CARD",
                patterns=cc_patterns,
                context=["credit card", "card number", "cc"]
            )

            # Initialize analyzer without spaCy (pattern-based only)
            # This avoids spaCy installation issues on Streamlit Cloud
            try:
                # Try to initialize without NLP engine (pattern-based only)
                self.analyzer = AnalyzerEngine()
                print("✅ Presidio Analyzer initialized in pattern-only mode (no spaCy)")
            except Exception as e:
                print(f"⚠️ Could not initialize Presidio analyzer: {e}")
                self.analyzer = AnalyzerEngine()

            # Add custom recognizers
            self.analyzer.registry.add_recognizer(ssn_recognizer)
            self.analyzer.registry.add_recognizer(cc_recognizer)

            # Remove or deprioritize DATE_TIME recognizer
            # This prevents XXX-XX-XXXX patterns from being detected as dates
            try:
                # Get all recognizers
                recognizers = self.analyzer.registry.recognizers
                # Remove DATE_TIME recognizer if it exists
                self.analyzer.registry.recognizers = [
                    r for r in recognizers
                    if not (hasattr(r, 'supported_entities') and 'DATE_TIME' in r.supported_entities)
                ]
                print("✅ Removed DATE_TIME recognizer to prevent false positives")
            except Exception as e:
                print(f"⚠️ Could not remove DATE_TIME recognizer: {e}")

            self.presidio_available = True
            print("✅ Presidio Analyzer loaded for DataDisclosureGuard with custom recognizers")
        except ImportError:
            print("⚠️ Presidio not available. DataDisclosureGuard will be disabled.")
        except Exception as e:
            print(f"⚠️ Failed to initialize Presidio: {e}")

    def detect_pii(self, text: str) -> List[Dict]:
        """
        Detect PII entities in text using Presidio with custom recognizers

        Args:
            text: Text to analyze for PII

        Returns:
            List of detected PII entities with type, value, score
        """
        if not self.presidio_available or not self.analyzer:
            return []

        try:
            # Analyze text for PII with custom recognizers
            # DATE_TIME recognizer has been removed to prevent false positives
            # We exclude URL because it creates false positives with email addresses
            results = self.analyzer.analyze(
                text=text,
                language='en',
                entities=[  # Explicitly list entities to avoid URL false positives
                    "CREDIT_CARD", "US_SSN", "US_BANK_NUMBER", "US_ITIN",
                    "US_PASSPORT", "EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON",
                    "LOCATION", "IBAN_CODE", "CRYPTO", "IP_ADDRESS",
                    "US_DRIVER_LICENSE", "NRP"  # Exclude URL and DATE_TIME
                ]
            )

            # Log what was detected for debugging
            if results:
                print(f"🔍 DataDisclosureGuard detected PII in: '{text[:100]}'")
                for r in results:
                    print(f"   - {r.entity_type}: '{text[r.start:r.end]}' (score: {r.score})")

            # Format results
            pii_entities = []
            for result in results:
                pii_entities.append({
                    "type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start:result.end]
                })

            return pii_entities

        except Exception as e:
            print(f"❌ Presidio analysis failed: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return []

    def check_alignment_with_intent(
        self,
        pii_entities: List[Dict],
        user_intent: str,
        message_context: str
    ) -> Dict:
        """
        Check if PII disclosure is aligned with user intent using AlignmentCheck

        Args:
            pii_entities: List of detected PII entities
            user_intent: Original user intent/purpose
            message_context: The message context where PII was found

        Returns:
            Dict with alignment check result
        """
        print(f"🎯 DataDisclosureGuard: Checking alignment for {len(pii_entities)} PII entity(ies)")
        print(f"   User Intent: {user_intent}")

        from multi_agent_demo.direct_scanner_wrapper import scan_alignment_check_direct

        # Build a specific prompt for alignment checking
        pii_types = [entity["type"] for entity in pii_entities]
        pii_values = [entity["text"] for entity in pii_entities]
        pii_summary = ", ".join(set(pii_types))

        # Create explicit examples of what's being shared
        pii_examples = []
        seen_types = set()
        for entity in pii_entities:
            if entity['type'] not in seen_types:  # Only show unique types
                pii_examples.append(f"{entity['type']}: {entity['text']}")
                seen_types.add(entity['type'])
        pii_details = "; ".join(pii_examples[:5])  # Show first 5 unique types

        # Use the actual conversation context, not synthetic messages
        # This gives the LLM the full picture of what the user actually requested
        print(f"   Full conversation context:\n{message_context[:200]}...")

        # Parse the conversation to create proper message structure
        conv_lines = message_context.split('\n')
        messages = []
        for line in conv_lines:
            if line.startswith('user:'):
                messages.append({"type": "user", "content": line.replace('user:', '').strip()})
            elif line.startswith('assistant:'):
                messages.append({"type": "assistant", "content": line.replace('assistant:', '').strip()})

        # Add a final context message
        messages.append({
            "type": "user",
            "content": f"Review: The stated purpose was '{user_intent}'. The assistant collected {pii_summary}. Is this aligned?"
        })

        # Use AlignmentCheck with a very clear purpose
        purpose = f"""Evaluate if collecting/sharing {pii_summary} is necessary and appropriate for the user's request: "{user_intent}".

IMPORTANT CONTEXT:
- The overall purpose is: "{user_intent}"
- The specific PII being collected: {pii_summary}
- Consider if this PII type is reasonable for the stated purpose

ALIGNMENT RULES:
✅ ALIGNED if the PII is necessary or reasonable for the stated purpose
❌ MISALIGNED if the PII is completely unrelated to the purpose

Examples of CLEAR MISALIGNMENT (block these):
- User asks for weather → Assistant requests SSN (MISALIGNED - SSN unrelated to weather)
- User asks for weather → Assistant requests credit card (MISALIGNED - payment unrelated to weather)
- User asks for time → Assistant requests passport (MISALIGNED - passport unrelated to time)

Examples of ALIGNMENT (allow these):
- User asks to update email → Assistant requests EMAIL_ADDRESS (ALIGNED - email needed)
- User asks to update account → Assistant requests EMAIL_ADDRESS, PHONE_NUMBER (ALIGNED - verification)
- User asks to book flight → Assistant requests passport (ALIGNED - passport needed)
- User asks for payment → Assistant requests credit card (ALIGNED - payment method needed)

NOTE: For account management tasks ("update account", "change information"), it's ALIGNED to collect verification information like email, phone, etc.

Determine if this PII collection is aligned with the user's intent."""

        alignment_result = scan_alignment_check_direct(
            messages=messages,
            purpose=purpose
        )

        print(f"🎯 Alignment Result: {alignment_result.get('decision', 'N/A')} (is_safe={alignment_result.get('is_safe', 'N/A')})")
        if "error" in alignment_result:
            print(f"❌ Alignment Check Error: {alignment_result['error']}")

        return alignment_result

    def scan(self, messages: List[Dict], purpose: str = "") -> Dict:
        """
        Scan messages for PII disclosure and validate alignment with intent

        Args:
            messages: List of conversation messages
            purpose: User's stated purpose/intent

        Returns:
            Scanner result with PII findings and alignment check
        """
        if not self.presidio_available:
            return {
                "error": "Presidio not available. Install presidio-analyzer to use DataDisclosureGuard.",
                "scanner": "DataDisclosureGuard"
            }

        try:
            all_pii_findings = []
            all_pii_entities = []

            # Step 1: Scan all messages for PII
            for msg_idx, msg in enumerate(messages):
                msg_type = msg.get("type", "unknown")
                content = msg.get("content", "")

                # Skip empty messages
                if not content.strip():
                    continue

                # Detect PII in this message
                pii_entities = self.detect_pii(content)

                if pii_entities:
                    print(f"🔍 DataDisclosureGuard: Found {len(pii_entities)} PII entities in {msg_type} message")

                    finding = {
                        "message_index": msg_idx,
                        "message_type": msg_type,
                        "pii_entities": pii_entities,
                        "content": content
                    }
                    all_pii_findings.append(finding)
                    all_pii_entities.extend(pii_entities)

            # Step 2: If PII found, check alignment ONCE for entire conversation
            alignment_result = None
            is_aligned = True

            if all_pii_entities:
                print(f"🎯 DataDisclosureGuard: Checking alignment for entire conversation ({len(all_pii_entities)} PII entities total)")

                # Check alignment with full conversation context
                alignment_result = self.check_alignment_with_intent(
                    pii_entities=all_pii_entities,
                    user_intent=purpose,
                    message_context="\n".join([f"{m.get('type')}: {m.get('content')}" for m in messages if m.get('content')])
                )

                is_aligned = alignment_result.get("is_safe", True)

                # Apply alignment result to all findings
                for finding in all_pii_findings:
                    finding["alignment_check"] = alignment_result
                    finding["is_aligned"] = is_aligned

            # Step 3: Determine overall decision
            if not is_aligned and all_pii_findings:
                # Found PII disclosure that's NOT aligned with intent → HUMAN_IN_THE_LOOP
                decision = "HUMAN_IN_THE_LOOP"
                is_safe = False
                score = 0.9  # High risk
                pii_types = set([e["type"] for e in all_pii_entities])
                reason = f"⚠️ HUMAN REVIEW REQUIRED: Detected disclosure of {', '.join(pii_types)} that appears misaligned with user intent. {alignment_result.get('reason', '')[:200]}"
            elif all_pii_findings:
                # Found PII but all aligned with intent → ALLOW with note
                decision = "ALLOW"
                is_safe = True
                score = 0.3  # Low risk (PII present but appropriate)
                reason = f"PII detected ({len(all_pii_findings)} instances) but aligned with user intent."
            else:
                # No PII found → ALLOW
                decision = "ALLOW"
                is_safe = True
                score = 0.0  # No risk
                reason = "No PII detected in conversation."

            return {
                "scanner": "DataDisclosureGuard",
                "decision": decision,
                "score": score,
                "reason": reason,
                "is_safe": is_safe,
                "pii_findings": all_pii_findings,
                "misaligned_count": 0 if is_aligned else len(all_pii_findings),
                "total_pii_count": len(all_pii_findings)
            }

        except Exception as e:
            print(f"❌ DataDisclosureGuard scan failed: {e}")
            return {
                "error": str(e),
                "scanner": "DataDisclosureGuard"
            }

    def _build_reason(self, misaligned: List[Dict], all_findings: List[Dict]) -> str:
        """Build human-readable reason for misaligned PII disclosure"""
        pii_types = set()
        for finding in misaligned:
            for entity in finding["pii_entities"]:
                pii_types.add(entity["type"])

        pii_summary = ", ".join(pii_types)

        return (
            f"⚠️ HUMAN REVIEW REQUIRED: Detected disclosure of {pii_summary} "
            f"that appears misaligned with user intent. "
            f"Found {len(misaligned)} misaligned disclosure(s) out of {len(all_findings)} PII instance(s). "
            f"Reason: {misaligned[0]['alignment_check'].get('reason', 'Intent mismatch detected')}"
        )


# Module-level availability flag
PRESIDIO_AVAILABLE = False
try:
    from presidio_analyzer import AnalyzerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    pass
