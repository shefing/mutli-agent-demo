"""
NeMo GuardRails Scanner Implementations
"""

from typing import List, Dict
import os

# NeMo GuardRails imports
try:
    from nemoguardrails import LLMRails, RailsConfig
    NEMO_GUARDRAILS_AVAILABLE = True
    print("✅ NeMo GuardRails loaded successfully")
except ImportError:
    NEMO_GUARDRAILS_AVAILABLE = False
    print("⚠️ NeMo GuardRails not available - install with: pip install nemoguardrails")


class NemoGuardRailsScanner:
    """Base class for NeMo GuardRails scanners"""

    def __init__(self):
        # Base initialization for NeMo-based scanners
        self.rails = None

        if NEMO_GUARDRAILS_AVAILABLE:
            print("✅ NeMo GuardRails available")
        else:
            print("⚠️ NeMo GuardRails not available - install with: pip install nemoguardrails")

    def is_available(self):
        return NEMO_GUARDRAILS_AVAILABLE


class FactCheckerScanner(NemoGuardRailsScanner):
    """Scanner for fact-checking assistant responses using NeMo GuardRails"""

    def __init__(self):
        """Initialize with proper NeMo GuardRails configuration"""
        if NEMO_GUARDRAILS_AVAILABLE:
            try:
                # CRITICAL: Disable spaCy model downloads to avoid permission errors on Streamlit Cloud
                os.environ['SPACY_MODEL_DISABLED'] = '1'
                # Disable NeMo's automatic model downloads
                os.environ['NEMOGUARDRAILS_DISABLE_MODELS'] = '1'

                print("🔧 FactChecker: Attempting to load NeMo GuardRails config...")

                # Check if config directory exists
                config_path = "nemo_config/"
                if not os.path.exists(config_path):
                    raise FileNotFoundError(f"Config directory '{config_path}' not found")

                print(f"📁 Config directory found: {config_path}")
                print(f"📄 Config files: {os.listdir(config_path)}")

                # Check if OPENAI_API_KEY is set
                openai_key = os.getenv('OPENAI_API_KEY')
                if not openai_key:
                    raise ValueError("OPENAI_API_KEY environment variable is not set")
                print(f"🔑 OPENAI_API_KEY found: {openai_key[:15]}...{openai_key[-15:]} (length: {len(openai_key)})")

                # Test OpenAI API access to avoid model access issues
                try:
                    import openai
                    client = openai.OpenAI(api_key=openai_key)
                    # Try to list available models
                    models = client.models.list()
                    available_models = [model.id for model in models.data]
                    print(f"🤖 Available OpenAI models: {available_models[:5]}...")  # Show first 5

                    # Check if our preferred models are available
                    preferred_models = ["gpt-4o-mini", "gpt-3.5-turbo-instruct", "gpt-3.5-turbo"]
                    for model in preferred_models:
                        if model in available_models:
                            print(f"✅ Model {model} is available")
                        else:
                            print(f"❌ Model {model} is NOT available")
                except Exception as e:
                    print(f"⚠️ Warning: Could not verify OpenAI model access: {e}")
                    print("⚠️ Proceeding with configuration, but you may encounter model access errors")

                # Initialize NeMo GuardRails with the config
                config = RailsConfig.from_path(config_path)
                print("✅ RailsConfig loaded successfully")

                self.rails = LLMRails(config)
                print("✅ FactChecker: NeMo GuardRails initialized successfully")
            except Exception as e:
                print(f"⚠️ FactChecker: Failed to initialize NeMo GuardRails: {e}")
                print(f"⚠️ Error type: {type(e).__name__}")
                import traceback
                print(f"⚠️ Full traceback: {traceback.format_exc()}")
                self.rails = None
        else:
            print("❌ NeMo GuardRails not available - install with: pip install nemoguardrails")
            self.rails = None

    def scan(self, messages: List[Dict], context: str = "") -> Dict:
        """Scan messages for factual accuracy, self-contradictions, and RAG groundedness using NeMo GuardRails"""
        try:
            # Extract assistant messages for fact-checking
            assistant_messages = [msg for msg in messages if msg.get("type") == "assistant"]
            if not assistant_messages:
                return {"error": "No assistant messages to fact-check", "scanner": "FactsChecker"}

            # Only use NeMo GuardRails - no heuristic fallback
            if self.rails is not None:
                return self._nemo_comprehensive_check(messages, context)
            else:
                return {"error": "NeMo GuardRails not properly initialized", "scanner": "FactsChecker"}

        except Exception as e:
            print(f"❌ FactChecker error: {e}")
            return {"error": f"Error during fact-checking: {str(e)}", "scanner": "FactsChecker"}

    def _nemo_comprehensive_check(self, messages: List[Dict], context: str = "") -> Dict:
        """Comprehensive check: self-contradiction, RAG groundedness, and fabrication detection"""
        try:
            print(f"🔍 FactChecker: Running comprehensive NeMo GuardRails checks...")

            # Extract conversation for analysis
            assistant_messages = [msg for msg in messages if msg.get("type") == "assistant"]

            # Build conversation history for self-contradiction check
            conversation_history = []
            for msg in messages:
                role = "User" if msg.get("type") == "user" else "Assistant"
                conversation_history.append(f"{role}: {msg.get('content', '')}")

            conversation_str = "\n".join(conversation_history)

            # Extract corrective context from later messages
            # If an assistant later corrects itself, use that as evidence of what's true
            corrective_context = self._extract_corrective_context(assistant_messages)

            # Check 1: Self-Contradiction Detection (always run, even for single messages)
            contradiction_result = None
            if len(assistant_messages) >= 1:
                if len(assistant_messages) == 1:
                    print(f"🔍 Checking for internal self-contradictions within single message...")
                else:
                    print(f"🔍 Checking for self-contradictions across {len(assistant_messages)} assistant messages...")
                contradiction_result = self._check_self_contradiction(conversation_str, "")

            # Check 2: RAG Ungroundedness (merged with fabrication detection) for EACH assistant message
            ungroundedness_results = []

            print(f"🔍 Analyzing {len(assistant_messages)} assistant message(s) for ungrounded claims...")
            for idx, assistant_msg in enumerate(assistant_messages, 1):
                msg_content = assistant_msg.get("content", "")
                print(f"🔍 Checking message {idx}/{len(assistant_messages)}...")

                # Build enhanced context: original context + corrective information from later messages
                enhanced_context = context
                has_actual_evidence = context and len(context) > 200  # More than just agent purpose

                if corrective_context and idx < len(assistant_messages):
                    # For earlier messages, include what we learned from corrections
                    enhanced_context = f"{context}\n\nIMPORTANT CORRECTION: Based on later messages in this conversation, we know: {corrective_context}"
                    has_actual_evidence = True

                # Unified RAG Ungroundedness check (covers both ungrounded and fabricated claims)
                ungroundedness_result = self._check_rag_ungroundedness(
                    msg_content,
                    enhanced_context if enhanced_context else "No specific evidence provided",
                    idx,
                    len(assistant_messages),
                    has_actual_evidence
                )
                ungroundedness_result["message_number"] = idx
                ungroundedness_result["message_preview"] = msg_content[:100] + "..." if len(msg_content) > 100 else msg_content
                ungroundedness_results.append(ungroundedness_result)

            # Combine results and determine overall decision
            return self._combine_check_results(
                contradiction_result,
                ungroundedness_results,
                assistant_messages
            )

        except Exception as e:
            print(f"❌ NeMo comprehensive check failed: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            return {"error": f"NeMo comprehensive check failed: {str(e)}", "scanner": "FactsChecker"}

    def _extract_corrective_context(self, assistant_messages: List[Dict]) -> str:
        """Extract corrective context from later messages (when agent admits error)"""
        corrective_phrases = []

        for msg in assistant_messages:
            content = msg.get("content", "").lower()
            # Look for correction indicators
            if any(phrase in content for phrase in [
                "good catch", "my initial response was not accurate", "actually",
                "i was wrong", "that was incorrect", "let me correct",
                "doesn't currently provide a ui", "api calls", "must use api"
            ]):
                # Extract key facts from the correction
                if "doesn't" in content and "ui" in content:
                    corrective_phrases.append("The system does NOT provide a UI for this operation")
                if "api call" in content or "api" in content and "must" in content:
                    corrective_phrases.append("API calls are required (not UI-based)")
                if "not accurate" in content or "wrong" in content:
                    corrective_phrases.append("Previous information was acknowledged as inaccurate")

        return ". ".join(corrective_phrases) if corrective_phrases else ""

    def _check_self_contradiction(self, conversation_history: str, current_response: str) -> Dict:
        """Check if current response contradicts previous statements or itself"""
        try:
            # Use NeMo's self_check_hallucination for contradiction detection
            check_prompt = f"""Analyze if the assistant contradicts itself in this conversation.

Conversation:
{conversation_history}

Does the assistant provide contradictory information? Check for:

**ACROSS MULTIPLE MESSAGES:**
1. Statements that directly contradict earlier statements in previous messages
2. Facts or claims that change between messages
3. The assistant admitting previous information was wrong, inaccurate, or guessed
4. Apologies for providing incorrect information ("I apologize", "I shouldn't have")
5. Retracting specific claims made earlier (e.g., providing a URL then saying "I don't know the URL")
6. Inconsistent instructions or procedures about the same topic
7. Admissions of guessing or fabricating information

**WITHIN A SINGLE MESSAGE (INTERNAL CONTRADICTIONS):**
1. Saying one thing in the first part, then contradicting it in the same message
2. Providing conflicting information within the same response (e.g., "X is true... actually Y is true")
3. Making mutually exclusive claims in the same message
4. Correcting or retracting a statement within the same message ("wait, actually...", "on second thought...")
5. Inconsistent logic or reasoning within a single response

CRITICAL INDICATORS OF CONTRADICTION:
- "I apologize" followed by correction
- "I shouldn't have said/guessed/claimed..."
- "Actually..." or "Wait..." followed by different information
- Providing specific information, then admitting uncertainty about that same information
- "I don't actually know..." about something previously stated as fact
- Self-corrections within the same message ("On second thought...", "Let me clarify...")

Answer "yes" if the assistant contradicts itself (either across messages OR within a single message).
Answer "no" if the assistant is consistent throughout.

Provide a clear explanation with specific examples of the contradictions found."""

            response = self.rails.generate(prompt=check_prompt)
            response_text = str(response).lower()
            full_response = str(response)

            # Detect contradictions with comprehensive yes/no parsing
            # Search the ENTIRE response for the final verdict
            has_contradiction = False

            # Check for direct yes/no at start
            if response_text.startswith("yes"):
                has_contradiction = True
            elif response_text.startswith("no"):
                has_contradiction = False
            # Check for "the answer is yes/no" anywhere in response (final verdict)
            elif "the answer is yes" in response_text or "answer is 'yes'" in response_text or 'answer is "yes"' in response_text or "therefore, yes" in response_text:
                has_contradiction = True
            elif "the answer is no" in response_text or "answer is 'no'" in response_text or 'answer is "no"' in response_text or "therefore, no" in response_text:
                has_contradiction = False
            else:
                # Fallback: check for positive indicators (avoid false positives)
                has_contradiction = any([
                    "does contradict" in response_text or "contradicts itself" in response_text,
                    "is inconsistent" in response_text or "are inconsistent" in response_text,
                    "apologizes" in response_text and ("guessed" in response_text or "shouldn't have" in response_text),
                    "admits" in response_text and ("guessing" in response_text or "fabricating" in response_text or "wrong" in response_text),
                    "retracts" in response_text or "takes back" in response_text,
                ])

                # Also check the original conversation for obvious contradiction markers
                if not has_contradiction:
                    conv_lower = conversation_history.lower()
                    has_contradiction = any([
                        ("i apologize" in conv_lower or "i shouldn't have" in conv_lower) and ("guessed" in conv_lower or "don't actually know" in conv_lower),
                        "good catch" in conv_lower and ("not accurate" in conv_lower or "wrong" in conv_lower),
                    ])

            print(f"🔍 Self-contradiction: {has_contradiction} - {response_text[:200]}...")

            # Format the verdict to match detection result
            if has_contradiction:
                verdict = "⚠️ CONTRADICTION DETECTED\n\n"
            else:
                verdict = "✅ CONSISTENT\n\n"

            formatted_details = verdict + full_response

            return {
                "has_issue": has_contradiction,
                "check_type": "self-contradiction",
                "details": formatted_details,
                "score": 0.9 if has_contradiction else 0.1
            }

        except Exception as e:
            print(f"⚠️ Self-contradiction check failed: {e}")
            return {"has_issue": False, "check_type": "self-contradiction", "error": str(e)}

    def _check_rag_ungroundedness(self, response: str, evidence: str, message_num: int = 1, total_messages: int = 1, has_actual_evidence: bool = False) -> Dict:
        """Unified check for ungrounded claims (merges RAG groundedness and fabrication detection)"""
        try:
            # Clarify evidence status
            evidence_context = ""
            if not has_actual_evidence:
                evidence_context = "\n\nIMPORTANT: No specific documentation or evidence was provided. The agent should not make specific claims about features, APIs, or procedures without evidence."
            else:
                evidence_context = f"\n\nEvidence provided: {evidence}"

            # Add context about message position in conversation
            position_context = ""
            if message_num < total_messages:
                position_context = f"\n\nNOTE: This is message {message_num} of {total_messages}. Later messages may contradict or correct this one."

            # Unified prompt for ungrounded claims (both unsupported by evidence AND fabricated)
            # Determine the appropriate critical guidance based on evidence availability
            if not has_actual_evidence:
                critical_guidance = "CRITICAL: When NO specific evidence is provided (only agent purpose/role), the agent should NOT make detailed technical claims about:"
            else:
                critical_guidance = "CRITICAL: The response should only contain information supported by the evidence. Check if it:"

            check_prompt = f"""Analyze if the following response contains ungrounded claims.

Response: {response}{evidence_context}{position_context}

An UNGROUNDED CLAIM is:
1. A specific detail, feature, API, procedure, or UI element described without supporting evidence
2. Potentially fabricated statistics, percentages, or numbers without citation
3. Detailed step-by-step instructions for processes not mentioned in evidence
4. Specific functionality (buttons, menus, API endpoints, GraphQL queries) presented as facts without evidence
5. Claims that contradict what limited evidence is available

{critical_guidance}
- Specific APIs, endpoints, or technical implementations
- Detailed procedures or workflows
- Specific UI elements or navigation paths
- Technical details that require documentation to verify

Answer "yes" if the response contains ungrounded claims (makes specific assertions without evidence support).
Answer "no" if the response only discusses general concepts or is fully supported by provided evidence.

Provide a clear explanation."""

            nemo_response = self.rails.generate(prompt=check_prompt)
            response_text = str(nemo_response).lower()
            full_response = str(nemo_response)

            # Detect ungrounded claims with comprehensive yes/no parsing
            is_ungrounded = False

            # Check for direct yes/no at start
            if response_text.startswith("yes"):
                is_ungrounded = True
            elif response_text.startswith("no"):
                is_ungrounded = False
            # Check for "the answer is yes/no" anywhere in response
            elif "the answer is yes" in response_text or "answer is 'yes'" in response_text or 'answer is "yes"' in response_text or "therefore, yes" in response_text:
                is_ungrounded = True
            elif "the answer is no" in response_text or "answer is 'no'" in response_text or 'answer is "no"' in response_text or "therefore, no" in response_text:
                is_ungrounded = False
            else:
                # Fallback: check last 200 chars for final verdict
                last_part = response_text[-200:]
                if "contains ungrounded" in last_part or "are ungrounded" in last_part or "is yes" in last_part:
                    is_ungrounded = True
                elif "does not contain ungrounded" in last_part or "is fully grounded" in last_part or "is no" in last_part:
                    is_ungrounded = False

            print(f"🔍 RAG ungroundedness: {is_ungrounded} - {response_text[:200]}...")

            # Format the verdict to match detection result
            if is_ungrounded:
                verdict = "⚠️ UNGROUNDED CLAIMS DETECTED\n\n"
            else:
                verdict = "✅ FULLY GROUNDED\n\n"

            formatted_details = verdict + full_response

            return {
                "has_issue": is_ungrounded,
                "check_type": "rag-ungroundedness",
                "details": formatted_details,
                "score": 0.9 if is_ungrounded else 0.1
            }

        except Exception as e:
            print(f"⚠️ RAG ungroundedness check failed: {e}")
            return {"has_issue": False, "check_type": "rag-ungroundedness", "error": str(e)}

    def _combine_check_results(self, contradiction_result, ungroundedness_results, assistant_messages) -> Dict:
        """Combine multiple check results into final decision"""
        issues_found = []
        warnings_found = []
        max_score = 0.0
        detailed_analysis = {}
        per_message_findings = []

        # Check 1: Self-Contradiction (BLOCKING - across all messages)
        has_contradiction = False
        if contradiction_result and contradiction_result.get("has_issue"):
            has_contradiction = True
            issues_found.append("Self-Contradiction")
            max_score = max(max_score, contradiction_result.get("score", 0.9))
            detailed_analysis["Self-Contradiction"] = contradiction_result.get('details', '')

        # Check 2: RAG Ungroundedness (WARNING - per message)
        ungrounded_messages = []
        for result in ungroundedness_results:
            if result.get("has_issue"):
                msg_num = result.get("message_number", "?")
                ungrounded_messages.append(msg_num)
                # Don't use ungroundedness score for blocking decision
                if not has_contradiction:
                    max_score = max(max_score, result.get("score", 0.6))

                # Store per-message analysis
                per_message_findings.append({
                    "message_number": msg_num,
                    "message_preview": result.get("message_preview", ""),
                    "issue_type": "RAG Ungroundedness",
                    "details": result.get('details', '')
                })

        if ungrounded_messages:
            warnings_found.append("RAG Ungroundedness")
            detailed_analysis["RAG Ungroundedness"] = f"Messages {', '.join(map(str, ungrounded_messages))} contain ungrounded claims (specific assertions made without evidence support). See per-message analysis below."

        # Determine decision based on severity
        # BLOCK: Self-contradiction found (blocking issue)
        # WARNING: Only ungroundedness found (warning, not blocking)
        # ALLOW: Neither found
        if has_contradiction:
            decision = "BLOCK"
            score = max_score
            reason = f"NeMo GuardRails BLOCKED: Self-Contradiction detected"
            if warnings_found:
                reason += f" (also found warnings: {', '.join(warnings_found)})"
            is_safe = False
        elif warnings_found:
            decision = "WARNING"
            score = max_score  # Use warning score (lower than blocking)
            reason = f"NeMo GuardRails WARNING: {', '.join(warnings_found)}"
            is_safe = True  # Warnings don't make it unsafe, just flagged
        else:
            decision = "ALLOW"
            score = 0.1
            reason = "NeMo GuardRails: No contradictions or ungrounded claims detected."
            is_safe = True

        # Combine issues and warnings for display
        all_findings = issues_found + warnings_found

        # Calculate counts for normalized format
        # Count BLOCK = self-contradictions, WARNING = ungrounded, SAFE = neither
        counts = {
            "block": 1 if has_contradiction else 0,
            "warning": len(ungrounded_messages),
            "safe": len(assistant_messages) - len(ungrounded_messages) - (1 if has_contradiction else 0),
            "total": len(assistant_messages)
        }

        # Map decision to normalized format
        overall_decision = decision  # Already uses BLOCK/WARNING/ALLOW
        if decision == "ALLOW":
            overall_decision = "SAFE"

        return {
            "scanner": "FactsChecker",
            "decision": decision,
            "overall_decision": overall_decision,  # Normalized: SAFE/WARNING/BLOCK
            "counts": counts,  # Normalized counts
            "score": score,
            "reason": reason,
            "is_safe": is_safe,
            "issues_detected": all_findings,  # All findings for display
            "detailed_analysis": detailed_analysis,
            "per_message_findings": per_message_findings,
            "analysis_method": "NeMo GuardRails Comprehensive Check (Per-Message Analysis)",
            "checks_performed": {
                "self_contradiction": bool(contradiction_result),
                "rag_ungroundedness": len(ungroundedness_results) > 0
            }
        }