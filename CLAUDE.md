# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
# AI Agent Guards Testing Application
streamlit run multi_agent_demo/guards_demo_ui.py
```

### Development Setup

⚠️ **Important**: Due to complex dependencies, follow the step-by-step installation guide:

```bash
# See detailed instructions in INSTALL.md
pip install -r requirements_minimal.txt
pip install llamafirewall
pip install nemoguardrails
```

For troubleshooting dependency conflicts, see [`INSTALL.md`](./INSTALL.md)

**Environment Setup:**
```bash
# Configure LlamaFirewall (optional)
llamafirewall configure
```

## Architecture

This is a demonstration application for testing AI Agent Guards (security scanners). The application focuses on testing and visualizing the behavior of different security scanners that protect AI agents from malicious inputs and goal hijacking.

### Module Structure (Refactored)
The application is organized into specialized modules for maintainability:

- **`guards_demo_ui.py`** (112 lines): Main application entry point
- **`firewall.py`**: Scanner orchestration and LlamaFirewall integration
- **`scanners/`**: Scanner implementation classes
  - `nemo_scanners.py`: NeMo GuardRails scanner implementations
- **`scenarios/`**: Scenario management and persistence
  - `scenario_manager.py`: Load/save scenarios, predefined scenarios
- **`ui/`**: UI component modules
  - `sidebar.py`: Scanner configuration interface
  - `conversation_builder.py`: Conversation creation/editing
  - `results_display.py`: Test results visualization

### Security Scanners
- **LlamaFirewall Integration**:
  - PromptGuard Scanner: Pre-execution input validation to detect malicious prompts
  - AlignmentCheck Scanner: Runtime behavioral monitoring to detect goal hijacking
- **NeMo GuardRails Integration** (NVIDIA's advanced content safety toolkit):
  - SelfContradiction Scanner: Detects response inconsistencies and contradictions
  - FactChecker Scanner: Verifies factual accuracy of AI responses
  - HallucinationDetector Scanner: Identifies hallucinated or ungrounded content

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
- **Multi-Scanner Testing**: Test up to 5 different security scanners simultaneously:
  - **PromptGuard**: Detects malicious user inputs and prompt injections
  - **AlignmentCheck**: Identifies goal hijacking and behavioral drift
  - **SelfContradiction**: Catches response inconsistencies and contradictions
  - **FactChecker**: Verifies factual accuracy of AI statements
  - **HallucinationDetector**: Identifies ungrounded or fabricated content
- **Dynamic Scanner Selection**: Enable/disable scanners via sidebar checkboxes
- **Visual Feedback**: Real-time score visualization with gauges, metrics, and decision indicators
- **Predefined Scenarios**: Load example scenarios for different attack types:
  - Legitimate Banking: Normal banking operations
  - Goal Hijacking: Attempts to redirect agent from intended purpose
  - Data Exfiltration: Attempts to extract sensitive information
  - Prompt Injection: Direct attempts to override agent instructions
- **Compact Layout**: Efficient use of screen space with sidebar scenarios and compact conversation display
- **Rich Results Display**: Expandable sections for each scanner with confidence scores and detailed analysis
- **Test History**: Track scanner performance over multiple tests with trend visualization
- **Save/Load**: Save custom scenarios for reuse

**UI Layout:**
- **Sidebar**: Scanner selection, predefined scenarios, agent configuration, and saved scenarios
- **Left Panel**: Compact conversation builder with user/assistant messages and actions
- **Right Panel**: Scanner results with AlignmentCheck gauge, PromptGuard alerts, and expandable NeMo GuardRails sections

**Purpose:**
This tool helps understand:
- How different security scanners detect various attack patterns and content issues
- What conversation patterns trigger security violations across multiple dimensions
- How to design legitimate agent behaviors that maintain security alignment
- Performance characteristics of different AI security approaches
- Detection capabilities for prompt injections, goal hijacking, contradictions, false information, and hallucinations
- Real-world AI safety challenges including factual accuracy and response consistency