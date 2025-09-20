# Installation Guide for AI Agent Guards Testing Application

Due to complex dependencies between LlamaFirewall and NeMo GuardRails, follow these steps for successful installation:

## Step-by-Step Installation

### 1. Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Basic Dependencies First
```bash
pip install --upgrade pip
pip install -r requirements_minimal.txt
```

### 3. Install Scanner Dependencies (Choose Your Approach)

#### Option A: Full Installation (All Scanners)
```bash
# Install LlamaFirewall first
pip install llamafirewall

# Install NeMo GuardRails
pip install nemoguardrails
```

#### Option B: LlamaFirewall Only (PromptGuard + AlignmentCheck)
```bash
pip install llamafirewall
```

#### Option C: Manual Installation with Specific Versions
```bash
# If you encounter dependency conflicts, try specific versions:
pip install llamafirewall==1.0.3
pip install nemoguardrails==0.16.0
```

### 4. Verify Installation
```bash
# Test basic imports
python -c "import streamlit; print('✅ Streamlit OK')"
python -c "import llamafirewall; print('✅ LlamaFirewall OK')"
python -c "import nemoguardrails; print('✅ NeMo GuardRails OK')" || echo "⚠️ NeMo GuardRails not available"
```

### 5. Run the Application
```bash
streamlit run multi_agent_demo/guards_demo_ui.py
```

## Troubleshooting

### Dependency Resolution Issues
If you encounter "resolution-too-deep" errors:

1. **Clean install**:
   ```bash
   pip cache purge
   deactivate
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install with --no-deps** (advanced):
   ```bash
   pip install --no-deps llamafirewall
   pip install --no-deps nemoguardrails
   # Then install missing dependencies manually
   ```

3. **Use conda instead** (if available):
   ```bash
   conda create -n ai-guards python=3.11
   conda activate ai-guards
   pip install streamlit plotly pandas python-dotenv
   pip install llamafirewall nemoguardrails
   ```

### Scanner Availability
- **All scanners work**: PromptGuard, AlignmentCheck, SelfContradiction, FactChecker, HallucinationDetector
- **LlamaFirewall only**: PromptGuard, AlignmentCheck (NeMo GuardRails scanners disabled)
- **Minimal install**: Basic UI works, scanners show as unavailable

## Environment Variables
Ensure your `.env` file contains:
```bash
OPENAI_API_KEY=your_openai_key
HF_TOKEN=your_huggingface_token
TOGETHER_API_KEY=your_together_key
```

The application will gracefully handle missing dependencies and show appropriate warnings in the UI.