# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
# AI Agent Guards Testing Application
streamlit run multi_agent_demo/guards_demo_ui.py
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure LlamaFirewall (optional)
llamafirewall configure
```

## Architecture

This is a demonstration application for testing AI Agent Guards (security scanners). The application focuses on testing and visualizing the behavior of different security scanners that protect AI agents from malicious inputs and goal hijacking.

### Core Components
- **Scanner Testing Interface** (`guards_demo_ui.py`): Streamlit-based UI for testing multiple AI security scanners
- **LlamaFirewall Integration**: Uses LlamaFirewall's security scanners:
  - PromptGuard Scanner: Pre-execution input validation to detect malicious prompts
  - AlignmentCheck Scanner: Runtime behavioral monitoring to detect goal hijacking

## Environment Configuration
Required environment variables in `.env`:
- `OPENAI_API_KEY`: For agent LLM operations
- `TOGETHER_API_KEY`: For LlamaFirewall AlignmentCheck
- `HF_TOKEN`: For PromptGuard models (optional)

## AI Agent Guards Demo

### Guards Demo UI (`guards_demo_ui.py`)
Interactive web interface for testing AI Agent Guards (security scanners) with custom scenarios.

**Run:**
```bash
streamlit run multi_agent_demo/guards_demo_ui.py
```

**Features:**
- **Conversation Builder**: Create custom agent conversations with user messages, assistant responses, and actions
- **Multi-Scanner Testing**: Test multiple security scanners simultaneously with tabbed results
- **Visual Feedback**: Real-time score visualization with gauges and decision indicators
- **Predefined Scenarios**: Load example scenarios for different attack types:
  - Legitimate Banking: Normal banking operations
  - Goal Hijacking: Attempts to redirect agent from intended purpose
  - Data Exfiltration: Attempts to extract sensitive information
  - Prompt Injection: Direct attempts to override agent instructions
- **Compact Layout**: Efficient use of screen space with sidebar scenarios and compact conversation display
- **Test History**: Track scanner performance over multiple tests with trend visualization
- **Save/Load**: Save custom scenarios for reuse

**UI Layout:**
- **Sidebar**: Predefined scenarios, agent configuration, and saved scenarios
- **Left Panel**: Compact conversation builder with user/assistant messages and actions
- **Right Panel**: Tabbed scanner results with scores, decisions, and history charts

**Purpose:**
This tool helps understand:
- How different security scanners detect various attack patterns
- What conversation patterns trigger security violations
- How to design legitimate agent behaviors that maintain security alignment
- Performance characteristics of different AI security approaches