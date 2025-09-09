# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
# Main CLI interface with interactive and automated testing modes
python multi_agent_demo/main.py

# Web-based demo with Streamlit dashboard
streamlit run multi_agent_demo/streamlit_demo.py

# Standalone LlamaFirewall demonstration
python multi_agent_demo/demo_standalone_agent.py
```

### Testing
```bash
# Run alignment check scenarios
python multi_agent_demo/test_alignment_check.py

# Test simple attack detection
python multi_agent_demo/test_simple_attack.py
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install UI dependencies (for Streamlit demo)
pip install -r multi_agent_demo/requirements_ui.txt

# Configure LlamaFirewall
llamafirewall configure
```

## Architecture

### Core Components
The system implements a multi-agent architecture with specialized domain agents protected by LlamaFirewall security:

- **Agent System** (`src/agents/`): BaseAgent abstract class with specialized implementations (BankingAgent, TravelAgent, EmailAgent) orchestrated by MultiAgentManager for request routing and session management
  
- **Tool Layer** (`src/tools/`): Domain-specific LangChain tools for each agent with built-in safety checks and validation

- **Security Layer** (`src/security/`): SecurityManager integrates LlamaFirewall with dual-layer protection:
  - PromptGuard Scanner: Pre-execution input validation
  - AlignmentCheck Scanner: Runtime behavioral monitoring

### Request Flow
User Input → MultiAgentManager → SecurityManager (PromptGuard) → Selected Agent → Tool Execution → SecurityManager (AlignmentCheck) → Response

### Key Design Patterns
- All agents inherit from BaseAgent with LangGraph state management
- Tools use Pydantic for validation and include safety thresholds
- Security traces persist conversation history for alignment analysis
- Dynamic agent selection based on capability scoring

## Environment Configuration
Required environment variables in `.env`:
- `OPENAI_API_KEY`: For agent LLM operations
- `TOGETHER_API_KEY`: For LlamaFirewall AlignmentCheck
- `HF_TOKEN`: For PromptGuard models (optional)

## Testing Approach
- Scenario-based testing with ScenarioRunner for legitimate vs malicious inputs
- Attack scenarios test goal hijacking, data exfiltration, and malicious forwarding
- Interactive testing via CLI (main.py) or web UI (streamlit_demo.py)
- Test results generate detailed metrics (accuracy, false positives/negatives)