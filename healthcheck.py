#!/usr/bin/env python3
"""Quick healthcheck to verify environment"""
import sys
print("=" * 80)
print("HEALTHCHECK START")
print("=" * 80)
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")

print("\n--- Testing imports ---")
try:
    import streamlit
    print(f"✅ Streamlit: {streamlit.__version__}")
except Exception as e:
    print(f"❌ Streamlit: {e}")

try:
    import nemoguardrails
    print(f"✅ NeMo GuardRails: available")
except Exception as e:
    print(f"❌ NeMo GuardRails: {e}")

try:
    import presidio_analyzer
    print(f"✅ Presidio: available")
except Exception as e:
    print(f"❌ Presidio: {e}")

try:
    import llamafirewall
    print(f"✅ LlamaFirewall: available")
except Exception as e:
    print(f"❌ LlamaFirewall: {e}")

print("\n--- Checking spaCy model ---")
try:
    import spacy
    nlp = spacy.load("en_core_web_lg")
    print(f"✅ spaCy model loaded: en_core_web_lg")
except Exception as e:
    print(f"❌ spaCy model: {e}")

print("\n--- Environment variables ---")
import os
print(f"OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
print(f"TOGETHER_API_KEY: {'✅ Set' if os.getenv('TOGETHER_API_KEY') else '❌ Not set'}")
print(f"HF_TOKEN: {'✅ Set' if os.getenv('HF_TOKEN') else '❌ Not set'}")

print("\n" + "=" * 80)
print("HEALTHCHECK COMPLETE")
print("=" * 80)
