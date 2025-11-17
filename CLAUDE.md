# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
# AI Agent Guards Multi-Page Application (NEW - recommended)
streamlit run multi_agent_demo/app.py

# Legacy single-page application (Real-time testing only)
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

- **`app.py`**: Multi-page application entry point with navigation
- **`guards_demo_ui.py`**: Legacy single-page entry point (Real-time only)
- **`pages/`**: Page modules for multi-page application
  - `realtime_page.py`: Real-time conversation testing page
  - `deviations_page.py`: OTEL-based deviations analysis page
- **`firewall.py`**: Scanner orchestration and LlamaFirewall integration
- **`scanners/`**: Scanner implementation classes
  - `nemo_scanners.py`: NeMo GuardRails scanner implementations
- **`deviations/`**: Deviation and bias detection modules
  - `otel_parser.py`: OpenTelemetry data parser
  - `deviation_detector.py`: Temporal anomaly detection
  - `bias_detector.py`: Cross-parameter bias detection
- **`scenarios/`**: Scenario management and persistence
  - `scenario_manager.py`: Load/save scenarios, predefined scenarios
- **`ui/`**: UI component modules
  - `common.py`: Shared components (agent configuration, headers)
  - `sidebar.py`: Scanner configuration interface (Real-time page)
  - `conversation_builder.py`: Conversation creation/editing
  - `results_display.py`: Test results visualization (Real-time)
  - `deviation_results.py`: Deviation/bias results visualization

### Security Scanners (3 Core Scanners)
- **LlamaFirewall Integration** (2 scanners):
  - **PromptGuard Scanner**: Pre-execution input validation to detect malicious prompts and prompt injections
  - **AlignmentCheck Scanner**: Runtime behavioral monitoring to detect goal hijacking and behavioral drift
- **NeMo GuardRails Integration** (1 scanner - NVIDIA's AI-powered content safety):
  - **FactChecker Scanner**: AI-powered fact verification using GPT-4o-mini to detect false claims and fabricated information

## Environment Configuration
Required environment variables in `.env`:
- `OPENAI_API_KEY`: For agent LLM operations
- `TOGETHER_API_KEY`: For LlamaFirewall AlignmentCheck
- `HF_TOKEN`: For PromptGuard models (optional)

## AI Agent Guards Demo

The application now has **two main modes** accessible via multi-page navigation:

### 1. Real-time Testing Page
Interactive web interface for testing AI Agent Guards (security scanners) with custom scenarios.

**Features:**
- **Conversation Builder**: Create custom agent conversations with user messages, assistant responses, and actions
- **Multi-Scanner Testing**: Test 3 core security scanners:
  - **PromptGuard**: Detects malicious user inputs and prompt injections
  - **AlignmentCheck**: Identifies goal hijacking and behavioral drift
  - **FactChecker**: AI-powered fact verification (uses NeMo GuardRails + GPT-4o-mini)
- **Dynamic Scanner Selection**: Enable/disable scanners via sidebar checkboxes
- **Visual Feedback**: Real-time score visualization with gauges, metrics, and decision indicators
- **Predefined Scenarios**: Load example scenarios for different attack types:
  - Legitimate Banking: Normal banking operations
  - Goal Hijacking: Attempts to redirect agent from intended purpose
  - Data Exfiltration: Attempts to extract sensitive information
  - Prompt Injection: Direct attempts to override agent instructions
  - Fact-Checking Test: Tests detection of false claims and fabricated statistics
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
- How different security scanners detect various attack patterns
- What conversation patterns trigger security violations
- How to design legitimate agent behaviors that maintain security alignment
- Performance characteristics of different AI security approaches
- Detection capabilities for prompt injections, goal hijacking, and false information
- Real-world AI safety challenges including factual accuracy verification

### 2. Deviations Analysis Page (NEW)
Analyze OpenTelemetry traces to detect behavioral deviations and bias patterns over time.

**Features:**
- **OTEL Upload**: Upload OpenTelemetry JSON traces for analysis
- **Sample Data**: Built-in sample datasets demonstrating deviation and bias patterns
- **Automatic Metric Identification**: Intelligently identifies business-relevant metrics from telemetry
- **Temporal Deviation Detection**: Detects trends and changes over time
  - Monotonic trends (increasing/decreasing patterns)
  - Period-to-period changes
  - Sudden spikes or drops
- **Bias Detection**: Identifies correlations indicating bias
  - Protected attribute detection (age, gender, etc.)
  - Disparity ratio calculation
  - Statistical significance (Cohen's d effect size)
  - Intersectional bias detection
- **Rich Visualizations**:
  - Severity scores and distributions
  - Temporal trend charts
  - Group comparison charts
  - Statistical evidence and recommendations
- **Agent Context**: Uses agent purpose to assess alignment concerns

**Example Use Cases:**
1. **Banking Commission Refunds**: Detect if average refund amounts are drifting upward over weeks, indicating agent becoming more generous
2. **Hiring CV Scoring**: Identify age-based bias where candidates under 40 receive significantly higher scores
3. **Customer Service**: Monitor response times, resolution rates, or satisfaction scores for temporal drift
4. **Financial Approvals**: Detect bias in approval rates across demographic groups

**Analysis Types:**
- **Deviations**: Temporal anomalies and behavioral drift
  - Temporal drift: Consistent increasing/decreasing trends
  - Period changes: Significant changes between time periods
  - Outliers: Unusual spikes or variability
- **Bias**: Cross-parameter correlations
  - Protected attribute bias (age, gender, etc.)
  - Disparity ratios with statistical significance
  - Fairness concerns and legal implications
  - Intersectional bias (combinations of parameters)

**UI Layout:**
- **Sidebar**: Page navigation (Real-time ↔ Deviations)
- **Agent Configuration**: Shared across both pages
- **Left Panel**: OTEL upload and analysis configuration
- **Right Panel**: Results with severity metrics, expandable findings, and visualizations

**Purpose:**
This tool enables:
- Post-hoc analysis of agent behavior from production telemetry
- Early detection of behavioral drift before it becomes problematic
- Identification of fairness issues and potential discrimination
- Compliance monitoring for regulatory requirements
- Understanding long-term trends in agent decision-making