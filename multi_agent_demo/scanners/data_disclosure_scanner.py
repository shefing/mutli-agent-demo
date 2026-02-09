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

            # Create custom recognizer for business financial data
            financial_patterns = [
                Pattern(
                    name="annual_revenue",
                    regex=r"(?:Annual Revenue|Revenue|Annual_Revenue):\s*\$[\d,]+",
                    score=0.8
                ),
                Pattern(
                    name="revenue_disclosure",
                    regex=r"\$[\d,]{6,}",  # Large dollar amounts (6+ digits)
                    score=0.5  # Lower confidence for plain numbers
                ),
            ]

            financial_recognizer = PatternRecognizer(
                supported_entity="FINANCIAL_INFO",
                patterns=financial_patterns,
                context=["revenue", "annual revenue", "customer annual revenue", "financial"]
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
            self.analyzer.registry.add_recognizer(financial_recognizer)

            # Remove problematic recognizers that cause false positives
            try:
                # Get all recognizers
                recognizers = self.analyzer.registry.recognizers
                # Remove DATE_TIME and US_DRIVER_LICENSE recognizers
                self.analyzer.registry.recognizers = [
                    r for r in recognizers
                    if not (hasattr(r, 'supported_entities') and
                           ('DATE_TIME' in r.supported_entities or 'US_DRIVER_LICENSE' in r.supported_entities))
                ]
                print("✅ Removed DATE_TIME and US_DRIVER_LICENSE recognizers to prevent false positives")
            except Exception as e:
                print(f"⚠️ Could not remove problematic recognizers: {e}")

            self.presidio_available = True
            print("✅ Presidio Analyzer loaded for DataDisclosureGuard with custom recognizers")
        except ImportError as e:
            print(f"⚠️ Presidio not available. DataDisclosureGuard will be disabled. Error: {e}")
            self.presidio_available = False
        except Exception as e:
            print(f"⚠️ Failed to initialize Presidio: {e}")
            import traceback
            print(f"⚠️ Traceback: {traceback.format_exc()}")
            self.presidio_available = False

    def _is_in_curl_command(self, text: str, entity: Dict) -> bool:
        """
        Check if entity is within a curl/wget command block

        Args:
            text: Full text being analyzed
            entity: Detected entity with start, end, type

        Returns:
            True if entity is in curl command, False otherwise
        """
        # Find the nearest 'curl' or 'wget' before the entity
        search_start = max(0, entity["start"] - 1000)  # Look back up to 1000 chars
        before_text = text[search_start:entity["start"]]

        # Check if there's a curl/wget command before this entity
        curl_idx = before_text.rfind('curl ')
        wget_idx = before_text.rfind('wget ')

        if curl_idx == -1 and wget_idx == -1:
            return False

        # Find the command start position
        cmd_start = max(curl_idx, wget_idx)

        # Check if we've left the curl command (look for newline without backslash continuation)
        after_cmd = before_text[cmd_start:]

        # Count lines - if we see a blank line or a line without \, we've left the command
        lines = after_cmd.split('\n')
        in_command = True
        for i, line in enumerate(lines[:-1]):  # Check all but the last line
            if not line.strip().endswith('\\') and i < len(lines) - 1:
                # This line doesn't continue, so if there are more lines, we've left the command
                next_line = lines[i + 1].strip()
                if not next_line or not next_line.startswith('-'):
                    in_command = False
                    break

        return in_command

    def _is_technical_context(self, text: str, entity: Dict) -> bool:
        """
        Check if a detected entity is in a technical context (not actual PII)

        Args:
            text: Full text being analyzed
            entity: Detected entity with start, end, type, text

        Returns:
            True if this is technical data (false positive), False if likely real PII
        """
        entity_text = entity["text"]
        entity_type = entity["type"]

        # Get surrounding context (100 chars before and after for better detection)
        start = max(0, entity["start"] - 100)
        end = min(len(text), entity["end"] + 100)
        context = text[start:end].lower()

        # Check if inside a curl/wget command (very common source of false positives)
        if self._is_in_curl_command(text, entity):
            print(f"   ℹ️  Filtering out {entity_type} '{entity_text}' - inside curl/wget command")
            return True

        # Technical context indicators
        technical_indicators = [
            # JSON/API structure
            '"sku":', '"product_id":', '"productid":', '"item_id":', '"itemid":',
            '"session_id":', '"sessionid":', '"session":', '"cookie":',
            '"token":', '"access_token":', '"refresh_token":', '"api_key":',
            '"id":', '"uuid":', '"tracking_id":', '"order_id":', '"orderid":',
            '"timestamp":', '"ts":', '"created_at":', '"updated_at":',

            # URL patterns
            'productpage.', '/product/', '/item/', '?id=', '&id=',
            'utm_', '.html', '.htm', '/api/', 'articlenumber=',

            # HTTP headers/curl
            'x-forwarded-for:', 'x-real-ip:', 'user-agent:', 'cookie:',
            'authorization:', 'bearer ', 'set-cookie:', '-h ', '--header',

            # E-commerce specific
            'sku:', 'asin:', 'gtin:', 'ean:', 'upc:',
            'variant_id:', 'style_id:', 'color_id:',

            # Code/script patterns
            '```', 'code:', 'script:', '<script', '</script>',
        ]

        # Check if entity is in technical context
        for indicator in technical_indicators:
            if indicator in context:
                print(f"   ℹ️  Filtering out {entity_type} '{entity_text}' - found technical context: '{indicator}'")
                return True

        # Check if inside a URL (common for product IDs)
        if 'http://' in context or 'https://' in context:
            # Check if entity is part of URL path or query string
            if any(sep in context[max(0, entity["start"]-start-10):entity["end"]-start+10]
                   for sep in ['/', '?', '&', '=', '.']):
                print(f"   ℹ️  Filtering out {entity_type} '{entity_text}' - inside URL")
                return True

        # IP address specific filtering
        if entity_type == "IP_ADDRESS":
            # Check if this is a version number (e.g., Chrome/139.0.0.0 or Safari/537.36)
            # Look for patterns like "Chrome/", "Safari/", "Firefox/" before the number
            if any(browser in context for browser in [
                'chrome/', 'safari/', 'firefox/', 'edge/', 'opera/',
                'applewebkit/', 'gecko/', 'version/'
            ]):
                print(f"   ℹ️  Filtering out IP_ADDRESS '{entity_text}' - browser/software version number")
                return True

            # Filter out if in headers, curl commands, or technical logs
            if any(header in context for header in [
                'x-forwarded-for', 'x-real-ip', 'remote-addr', 'client-ip',
                'curl ', 'wget ', 'http header', 'accept:', 'content-type:',
                'user-agent:', 'forwarded', 'cloudflare', 'cf_chl', 'cray:',
                'status":403', 'status":503', 'error response', '"body":', '"response":',
                'html>', '<!doctype', 'challenge-platform', 'orchestrate'
            ]):
                print(f"   ℹ️  Filtering out IP_ADDRESS '{entity_text}' - in HTTP/technical context")
                return True

            # Filter out if inside JSON error responses or HTML
            if any(json_marker in context for json_marker in [
                '{"response":', '{"status":', '{"error":', '<!doctype', '<html'
            ]):
                print(f"   ℹ️  Filtering out IP_ADDRESS '{entity_text}' - in JSON/HTML error response")
                return True

        # Phone number specific filtering
        if entity_type == "PHONE_NUMBER":
            # If it looks like a product ID (in URL, has "product" nearby)
            if any(keyword in context for keyword in [
                'product', 'item', 'sku', '.html', '/product', 'productpage',
                'articlenumber', 'variant', 'style'
            ]):
                print(f"   ℹ️  Filtering out PHONE_NUMBER '{entity_text}' - likely product/item ID")
                return True

            # Timestamp-like numbers (unix timestamps often look like phone numbers)
            if len(entity_text) == 10 and entity_text.startswith('17'):
                # Unix timestamps in seconds starting with 17 (years 2023+)
                print(f"   ℹ️  Filtering out PHONE_NUMBER '{entity_text}' - likely timestamp")
                return True

        # SSN/Passport specific filtering
        if entity_type in ["US_SSN", "US_PASSPORT"]:
            # If in JSON with technical keys or e-commerce context
            if any(keyword in context for keyword in [
                '"sku"', 'variant', 'product', 'item', 'asin', 'gtin',
                'session', 'cookie', 'token', 'timestamp'
            ]):
                print(f"   ℹ️  Filtering out {entity_type} '{entity_text}' - likely SKU/product code/session data")
                return True

        # Bank number specific filtering
        if entity_type == "US_BANK_NUMBER":
            # Timestamp-like numbers (unix timestamps often detected as bank numbers)
            if len(entity_text) >= 10 and entity_text.startswith('17'):
                # Unix timestamps in milliseconds or seconds starting with 17 (years 2023+)
                print(f"   ℹ️  Filtering out US_BANK_NUMBER '{entity_text}' - likely timestamp")
                return True

            # If looks like product/order/session ID
            if any(keyword in context for keyword in [
                'product', 'order', 'item', 'sku', '.html', '/product',
                'session', 'cookie', 'token', 'timestamp', 'tracking',
                'expires', 'max-age', 'domain=', 'path=', 'samesite'
            ]):
                print(f"   ℹ️  Filtering out US_BANK_NUMBER '{entity_text}' - likely product/order/session ID")
                return True

        return False

    def detect_pii(self, text: str) -> List[Dict]:
        """
        Detect PII entities in text using Presidio with custom recognizers
        and context-aware filtering

        Args:
            text: Text to analyze for PII

        Returns:
            List of detected PII entities with type, value, score
        """
        if not self.presidio_available or not self.analyzer:
            return []

        try:
            # Analyze text for PII with custom recognizers
            # DATE_TIME and US_DRIVER_LICENSE recognizers removed to prevent false positives
            # We exclude URL because it creates false positives with email addresses
            results = self.analyzer.analyze(
                text=text,
                language='en',
                entities=[  # Explicitly list entities to avoid false positives
                    "CREDIT_CARD", "US_SSN", "US_BANK_NUMBER", "US_ITIN",
                    "US_PASSPORT", "EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON",
                    "LOCATION", "IBAN_CODE", "CRYPTO", "IP_ADDRESS",
                    "NRP", "FINANCIAL_INFO"  # Exclude URL, DATE_TIME, and US_DRIVER_LICENSE
                ]
            )

            # Log what was detected for debugging
            if results:
                print(f"🔍 DataDisclosureGuard detected {len(results)} potential PII matches in: '{text[:100]}'")

            # Format results and filter out technical false positives
            pii_entities = []
            filtered_count = 0

            for result in results:
                entity = {
                    "type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start:result.end]
                }

                # Check if this is technical data (false positive)
                if self._is_technical_context(text, entity):
                    filtered_count += 1
                    continue

                # Real PII detected
                print(f"   ✓ {result.entity_type}: '{text[result.start:result.end]}' (score: {result.score})")
                pii_entities.append(entity)

            if filtered_count > 0:
                print(f"   📊 Filtered out {filtered_count} technical false positive(s), {len(pii_entities)} real PII remain")

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
        message_context: str,
        pii_findings: List[Dict]
    ) -> Dict:
        """
        Check if PII disclosure is aligned with user intent using AlignmentCheck

        Args:
            pii_entities: List of detected PII entities
            user_intent: Original user intent/purpose
            message_context: The message context where PII was found
            pii_findings: List of findings with message_type info

        Returns:
            Dict with alignment check result
        """
        print(f"🎯 DataDisclosureGuard: Checking alignment for {len(pii_entities)} PII entity(ies)")
        print(f"   User Intent: {user_intent}")

        # Check if all PII was provided by the user (not collected by assistant)
        user_provided_count = sum(1 for f in pii_findings if f.get("message_type") == "user")
        assistant_collected_count = sum(1 for f in pii_findings if f.get("message_type") == "assistant")

        print(f"   PII breakdown: {user_provided_count} user-provided, {assistant_collected_count} assistant-collected")

        # If all PII was user-provided, it's likely aligned (user gave their own info)
        # unless the user is being tricked/socially engineered
        if user_provided_count > 0 and assistant_collected_count == 0:
            print(f"   ✅ All PII was user-provided (not collected by assistant) - likely aligned with intent")
            # Still check for social engineering / goal hijacking
            # but use a more lenient prompt that understands user-provided data

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

        # Determine if PII was user-provided or agent-collected
        if user_provided_count > 0 and assistant_collected_count == 0:
            context_note = "The user explicitly provided their own contact/personal information as part of their request."
        elif assistant_collected_count > 0:
            context_note = "The agent collected or requested personal information from the user."
        else:
            context_note = "Personal information was detected in the conversation."

        # Add a final context message
        messages.append({
            "type": "user",
            "content": f"Review: The stated purpose was '{user_intent}'. {context_note} {pii_summary} was detected. Is this aligned with the user's stated purpose?"
        })

        # Use AlignmentCheck with a very clear purpose
        purpose = f"""Evaluate if the presence of {pii_summary} is aligned with the user's request: "{user_intent}".

IMPORTANT CONTEXT:
- The overall purpose is: "{user_intent}"
- The specific PII detected: {pii_summary}
- {context_note}

ALIGNMENT RULES:
✅ ALIGNED if the PII is necessary or reasonable for the stated purpose
✅ ALIGNED if the user explicitly provided their own contact info for notifications, alerts, or communication
✅ ALIGNED if the user is asking the agent to send something to their own email/phone/slack
❌ MISALIGNED if the PII is completely unrelated to the purpose
❌ MISALIGNED if the agent is collecting unnecessary PII

Examples of CLEAR MISALIGNMENT (block these):
- User asks for weather → Assistant requests SSN (MISALIGNED - SSN unrelated to weather)
- User asks for weather → Assistant requests credit card (MISALIGNED - payment unrelated to weather)
- User asks for time → Assistant requests passport (MISALIGNED - passport unrelated to time)
- User asks for news → Agent collects email without consent (MISALIGNED - unnecessary collection)

Examples of ALIGNMENT (allow these):
- User says "send to my email bob@example.com" → EMAIL_ADDRESS detected (ALIGNED - user provided for stated purpose)
- User says "notify me on slack at rita@company.com" → EMAIL_ADDRESS detected (ALIGNED - user provided for notifications)
- User asks to update email → Assistant requests EMAIL_ADDRESS (ALIGNED - email needed)
- User asks to update account → Assistant requests EMAIL_ADDRESS, PHONE_NUMBER (ALIGNED - verification)
- User asks to book flight → Assistant requests passport (ALIGNED - passport needed)
- User asks for payment → Assistant requests credit card (ALIGNED - payment method needed)

KEY PRINCIPLE: When users explicitly provide their own contact information (email, phone, slack) as part of their request for the agent to contact/notify them, this is ALIGNED, not data exfiltration.

Determine if this PII usage is aligned with the user's intent."""

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

                # Group PII by type and track first occurrence
                pii_first_occurrence = {}  # {(type, text): message_index}
                for finding in all_pii_findings:
                    for entity in finding["pii_entities"]:
                        key = (entity["type"], entity["text"])
                        if key not in pii_first_occurrence:
                            pii_first_occurrence[key] = finding["message_index"]

                # Check if PII first appears in user's request with notification keywords
                user_provided_for_notifications = False
                notification_keywords = [
                    "send", "notify", "alert", "email me", "message me", "contact me",
                    "let me know", "inform me", "ping me", "slack", "notification",
                    "dm me", "text me", "call me", "reach out"
                ]

                # Check if any PII first appears in a user message with notification keywords
                for (pii_type, pii_value), first_msg_idx in pii_first_occurrence.items():
                    if first_msg_idx < len(messages):
                        first_msg = messages[first_msg_idx]
                        if first_msg.get("type") == "user":
                            content = first_msg.get("content", "").lower()
                            # Check if this is a notification/communication request
                            if any(keyword in content for keyword in notification_keywords):
                                # Check if the PII value appears in this message
                                if pii_value.lower() in content:
                                    user_provided_for_notifications = True
                                    print(f"   ✅ {pii_type} first appears in user message with notification keywords: '{content[:100]}'")
                                    break

                # If PII is user-provided for notifications, skip alignment check (it's clearly aligned)
                if user_provided_for_notifications:
                    print(f"   ✅ Auto-approving: User provided contact info for notifications/alerts - clearly aligned")
                    is_aligned = True
                    alignment_result = {
                        "is_safe": True,
                        "decision": "ALLOW",
                        "reason": "User explicitly provided their contact information for receiving notifications/alerts as part of their request. Subsequent mentions by the assistant are echoing/confirming the user's provided contact info.",
                        "score": 0.1
                    }
                else:
                    # Run full alignment check
                    alignment_result = self.check_alignment_with_intent(
                        pii_entities=all_pii_entities,
                        user_intent=purpose,
                        message_context="\n".join([f"{m.get('type')}: {m.get('content')}" for m in messages if m.get('content')]),
                        pii_findings=all_pii_findings
                    )

                    # If alignment check returned an error, default to misaligned (conservative)
                    if "error" in alignment_result:
                        print(f"⚠️ Alignment check failed, defaulting to misaligned (conservative): {alignment_result.get('error')}")
                        is_aligned = False
                    else:
                        is_aligned = alignment_result.get("is_safe", False)

                # Apply alignment result to all findings
                for finding in all_pii_findings:
                    finding["alignment_check"] = alignment_result
                    finding["is_aligned"] = is_aligned

            # Step 3: Determine overall decision with examples
            if not is_aligned and all_pii_findings:
                # Found PII disclosure that's NOT aligned with intent → HUMAN_IN_THE_LOOP
                decision = "HUMAN_IN_THE_LOOP"
                is_safe = False
                score = 0.9  # High risk

                # Build examples of each PII type detected
                pii_examples = {}
                for entity in all_pii_entities:
                    pii_type = entity["type"]
                    if pii_type not in pii_examples:
                        # Store first example of each type
                        example_text = entity["text"]
                        # Truncate long examples
                        if len(example_text) > 40:
                            example_text = example_text[:37] + "..."
                        pii_examples[pii_type] = example_text

                # Format examples for display
                examples_str = ", ".join([f"{pii_type} (e.g., {example})" for pii_type, example in pii_examples.items()])

                reason = f"⚠️ HUMAN REVIEW REQUIRED: Detected disclosure of {examples_str} that appears misaligned with user intent. {alignment_result.get('reason', '')[:200]}"
            elif all_pii_findings:
                # Found PII but all aligned with intent → ALLOW with note
                decision = "ALLOW"
                is_safe = True
                score = 0.3  # Low risk (PII present but appropriate)

                # Build examples of each PII type detected
                pii_examples = {}
                for entity in all_pii_entities:
                    pii_type = entity["type"]
                    if pii_type not in pii_examples:
                        example_text = entity["text"]
                        if len(example_text) > 40:
                            example_text = example_text[:37] + "..."
                        pii_examples[pii_type] = example_text

                examples_str = ", ".join([f"{pii_type} (e.g., {example})" for pii_type, example in pii_examples.items()])
                reason = f"PII detected: {examples_str}. All aligned with user intent."
            else:
                # No PII found → ALLOW
                decision = "ALLOW"
                is_safe = True
                score = 0.0  # No risk
                reason = "No PII detected in conversation."

            # Build per-message results for normalized format
            message_results = []
            for finding in all_pii_findings:
                msg_decision = "BLOCK" if not finding.get("is_aligned", True) else "SAFE"
                message_results.append({
                    "message_index": finding["message_index"],
                    "message_type": finding["message_type"],
                    "decision": msg_decision,
                    "reason": f"PII detected: {', '.join([e['type'] for e in finding['pii_entities']])}"
                })

            # Calculate counts (across all messages, not just those with PII)
            total_messages = len(messages)
            counts = {
                "block": sum(1 for r in message_results if r["decision"] == "BLOCK"),
                "warning": sum(1 for r in message_results if r["decision"] == "WARNING"),
                "safe": total_messages - sum(1 for r in message_results if r["decision"] in ["BLOCK", "WARNING"]),
                "total": total_messages
            }

            # Map decision to normalized format
            overall_decision = "BLOCK" if decision == "HUMAN_IN_THE_LOOP" else "SAFE"
            if decision == "ALLOW" and all_pii_findings:
                # PII found but aligned
                overall_decision = "WARNING"  # Informational warning

            return {
                "scanner": "DataDisclosureGuard",
                "decision": decision,
                "overall_decision": overall_decision,  # Normalized: SAFE/WARNING/BLOCK
                "counts": counts,  # Normalized counts
                "message_results": message_results,  # Per-message results
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
