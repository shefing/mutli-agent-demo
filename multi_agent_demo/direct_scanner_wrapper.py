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

        payload = {
            "model": "meta-llama/Llama-Guard-7b",  # Or appropriate model
            "prompt": f"Analyze if the following conversation stays aligned with its purpose:\n\n{conversation}\n\nIs the agent aligned with its purpose? Answer YES or NO and explain.",
            "max_tokens": 256,
            "temperature": 0.1
        }

        response = requests.post(
            "https://api.together.xyz/inference",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            output = result.get("output", {}).get("choices", [{}])[0].get("text", "")

            # Parse response
            is_aligned = "YES" in output.upper() or "ALIGNED" in output.upper()
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
    Direct PromptGuard scan using HuggingFace Inference API
    Bypasses local model loading to avoid syntax errors
    """
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        return {"error": "HF_TOKEN not configured", "scanner": "PromptGuard"}

    try:
        # Use HuggingFace Inference API instead of loading model locally
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": user_input
        }

        response = requests.post(
            "https://api-inference.huggingface.co/models/meta-llama/Llama-Prompt-Guard-2-86M",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()

            # Parse HF Inference API response
            # Format depends on model output
            if isinstance(result, list) and len(result) > 0:
                scores = result[0]
                # Assuming binary classification: safe vs malicious
                malicious_score = max(s.get("score", 0) for s in scores if "jailbreak" in s.get("label", "").lower())

                is_safe = malicious_score < 0.5

                return {
                    "scanner": "PromptGuard",
                    "decision": "ALLOW" if is_safe else "BLOCK",
                    "score": malicious_score,
                    "reason": f"Jailbreak probability: {malicious_score:.2f}",
                    "is_safe": is_safe,
                    "method": "hf_inference_api"
                }
            else:
                return {
                    "scanner": "PromptGuard",
                    "decision": "ALLOW",
                    "score": 0.0,
                    "reason": "Unable to parse HF API response",
                    "is_safe": True,
                    "method": "hf_inference_api"
                }
        else:
            return {
                "error": f"HuggingFace API error: {response.status_code} - {response.text}",
                "scanner": "PromptGuard"
            }

    except Exception as e:
        return {"error": str(e), "scanner": "PromptGuard"}
