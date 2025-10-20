"""
Direct scanner wrappers that bypass LlamaFirewall's initialization
to avoid Streamlit Cloud compatibility issues
"""

import os
import requests
from typing import Dict, List

def scan_alignment_check_direct(messages: List[Dict], purpose: str) -> Dict:
    """
    Direct AlignmentCheck scan using Together API
    Bypasses LlamaFirewall wrapper to avoid syntax errors
    """
    together_key = os.getenv("TOGETHER_API_KEY")
    if not together_key:
        return {"error": "TOGETHER_API_KEY not configured", "scanner": "AlignmentCheck"}

    try:
        # Build conversation context
        conversation = f"Purpose: {purpose}\n\n"
        for msg in messages:
            role = msg.get("type", "unknown")
            content = msg.get("content", "")
            conversation += f"{role}: {content}\n"

        # Call Together API for alignment checking
        # This is a simplified version - you may need to adjust based on Together's actual API
        headers = {
            "Authorization": f"Bearer {together_key}",
            "Content-Type": "application/json"
        }

        # Enhanced prompt for PII alignment checking
        if "PII" in purpose or "collecting" in purpose or "sharing" in purpose:
            # This is a PII alignment check - be more strict
            prompt = f"""Analyze if the agent's actions are appropriate given the user's request.

{conversation}

Task: {purpose}

CRITICAL: The agent should ONLY collect or share personal information (PII) that is strictly necessary for the specific task the user requested. Any unnecessary PII collection is a security risk.

Is the agent's behavior aligned with the user's request and appropriate? Answer YES or NO and explain why."""
        else:
            # Standard alignment check
            prompt = f"Analyze if the following conversation stays aligned with its purpose:\n\n{conversation}\n\nIs the agent aligned with its purpose? Answer YES or NO and explain."

        # Use Together AI's chat completions endpoint (OpenAI-compatible)
        # Using Llama-3.1-8B-Instruct as it's better for reasoning/analysis tasks
        payload = {
            "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 256,
            "temperature": 0.1
        }

        response = requests.post(
            "https://api.together.xyz/v1/chat/completions",  # Updated endpoint
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            # Parse OpenAI-compatible response format
            output = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Debug logging for PII alignment checks
            if "PII" in purpose or "collecting" in purpose:
                print("=" * 80)
                print("⚠️ LlamaFirewall AlignmentCheck Debug")
                print("=" * 80)
                print(f"Purpose: {purpose[:100]}...")
                print(f"API Response: {output[:300]}...")
                print("=" * 80)

            # Parse response with improved logic
            output_upper = output.upper()

            # Check for explicit misalignment indicators
            misalignment_indicators = [
                "NO" in output_upper and "NOT ALIGNED" in output_upper,
                "NOT NECESSARY" in output_upper,
                "NOT APPROPRIATE" in output_upper,
                "UNNECESSARY" in output_upper,
                "MISALIGNED" in output_upper,
                "NOT NEEDED" in output_upper,
                "SHOULD NOT" in output_upper and "COLLECT" in output_upper,
                "SHOULD NOT" in output_upper and "REQUEST" in output_upper,
            ]

            # Check for explicit alignment indicators
            alignment_indicators = [
                output_upper.startswith("YES"),  # Response starts with YES
                "YES" in output_upper and "ALIGNED" in output_upper,
                "NECESSARY" in output_upper and "YES" in output_upper,
                "APPROPRIATE" in output_upper and "YES" in output_upper,
                "YES" in output_upper and "REASONABLE" in output_upper,
            ]

            # Determine alignment
            # Priority: Check misalignment first (more important for security)
            if any(misalignment_indicators):
                is_aligned = False
                if "PII" in purpose or "collecting" in purpose:
                    triggered = [i for i, indicator in enumerate(misalignment_indicators) if indicator]
                    print(f"🔴 MISALIGNMENT detected - triggered indicators: {triggered}")
            elif any(alignment_indicators):
                is_aligned = True
                if "PII" in purpose or "collecting" in purpose:
                    triggered = [i for i, indicator in enumerate(alignment_indicators) if indicator]
                    print(f"🟢 ALIGNMENT detected - triggered indicators: {triggered}")
            else:
                # Fallback: Check if response starts with YES/NO
                first_word = output.strip().split()[0].upper() if output.strip() else ""
                if first_word == "YES":
                    is_aligned = True
                elif first_word == "NO":
                    is_aligned = False
                else:
                    # Last resort: look for YES without NO
                    is_aligned = "YES" in output_upper and "NO" not in output_upper

                if "PII" in purpose or "collecting" in purpose:
                    print(f"⚪ FALLBACK - first_word={first_word}, result={is_aligned}")

            score = 0.1 if is_aligned else 0.9

            return {
                "scanner": "AlignmentCheck",
                "decision": "ALLOW" if is_aligned else "BLOCK",
                "score": score,
                "reason": output,
                "is_safe": is_aligned,
                "method": "direct_api"
            }
        else:
            return {
                "error": f"Together API error: {response.status_code} - {response.text}",
                "scanner": "AlignmentCheck"
            }

    except Exception as e:
        return {"error": str(e), "scanner": "AlignmentCheck"}


def scan_prompt_guard_direct(user_input: str) -> Dict:
    """
    Direct PromptGuard scan using simple heuristics
    Bypasses HF API to avoid permission issues
    """
    try:
        # Simple heuristic-based prompt injection detection
        # This is a simplified version that doesn't require external APIs

        user_input_lower = user_input.lower()

        # Patterns that indicate potential prompt injection or jailbreak attempts
        suspicious_patterns = [
            "ignore previous instructions",
            "ignore all previous",
            "ignore your previous",
            "disregard previous",
            "disregard your",
            "forget previous",
            "forget your",
            "ignore your instructions",
            "ignore your purpose",
            "ignore your intended",
            "ignore your goals",
            "ignore the intended",  # Catches "ignore the intended usage"
            "ignore the original",
            "override your",
            "bypass your",
            "new instructions",
            "system:",
            "assistant:",
            "[INST]",
            "<<SYS>>",
            "you are now",
            "act as if",
            "pretend you are",
            "roleplay as",
            "your new purpose",
            "your new goal",
            "change your purpose",
            "sudo",
            "admin mode",
            "developer mode",
            "god mode",
            "jailbreak",
            "DAN mode",
            "unrestricted mode"
        ]

        # Check for suspicious patterns
        matches = [pattern for pattern in suspicious_patterns if pattern in user_input_lower]

        if matches:
            # Found suspicious patterns - extract context snippets
            context_snippets = []
            for pattern in matches[:3]:  # Show up to 3 matches
                # Find the pattern in the original text (case-insensitive)
                pattern_index = user_input_lower.find(pattern)
                if pattern_index != -1:
                    # Extract surrounding context (up to 50 chars before and after)
                    start = max(0, pattern_index - 20)
                    end = min(len(user_input), pattern_index + len(pattern) + 30)

                    # Adjust start to not cut words - find previous space
                    if start > 0:
                        # Look backwards for word boundary (space or punctuation)
                        while start > 0 and user_input[start - 1] not in ' \n\t.,;:!?':
                            start -= 1

                    # Adjust end to not cut words - find next space
                    if end < len(user_input):
                        # Look forwards for word boundary (space or punctuation)
                        while end < len(user_input) and user_input[end] not in ' \n\t.,;:!?':
                            end += 1

                    # Get the snippet from the original text (preserving case)
                    snippet = user_input[start:end].strip()

                    # Add ellipsis if we truncated
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(user_input):
                        snippet = snippet + "..."

                    context_snippets.append(f'"{snippet}"')

            # Build reason with context
            if context_snippets:
                reason = f"Detected prompt injection attempt: {context_snippets[0]}"
            else:
                reason = f"Detected potential prompt injection patterns: {', '.join(matches[:3])}"

            score = min(0.9, 0.5 + (len(matches) * 0.1))  # Higher score for more matches
            return {
                "scanner": "PromptGuard",
                "decision": "BLOCK",
                "score": score,
                "reason": reason,
                "is_safe": False,
                "method": "heuristic"
            }
        else:
            # No suspicious patterns found
            return {
                "scanner": "PromptGuard",
                "decision": "ALLOW",
                "score": 0.1,
                "reason": "No prompt injection patterns detected",
                "is_safe": True,
                "method": "heuristic"
            }

    except Exception as e:
        return {"error": str(e), "scanner": "PromptGuard"}
