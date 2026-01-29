---
title: Aitruism
emoji: 🛡️
colorFrom: gray
colorTo: indigo
sdk: docker
pinned: false
license: gpl-3.0
short_description: AI Agent Guards Testing - Security scanners for LLM agents
app_port: 8501
---

# AI Agent Guards Behavioral Monitoring Platform

A comprehensive demonstration application for testing AI Agent security scanners and behavioral monitoring. Features real-time security testing with multiple scanners and post-hoc behavioral analysis using OpenTelemetry traces.

**Live Demo**: Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

## Table of Contents
- [Overview](#overview)
- [Documentation Index](#documentation-index)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [LLM Dependencies](#llm-dependencies)
- [External Resources](#external-resources)
- [Configuration](#configuration)
- [Usage](#usage)
- [Modules & Functions](#modules--functions)
- [Sample Data](#sample-data)
- [Development](#development)
- [Deployment](#deployment)

---

## Overview

This application provides two complementary approaches to AI agent security and monitoring:

### 1. Real-Time Security Testing
Interactive web interface for testing AI agent security scanners against custom conversation scenarios. Test how different security scanners detect malicious inputs, goal hijacking, data exfiltration, and factual inaccuracies.

### 2. Post-Hoc Behavioral Analysis
Analyze OpenTelemetry traces to detect temporal deviations and bias patterns in agent behavior over time. Identify behavioral drift, fairness issues, and compliance concerns from production telemetry data.

---

## Documentation Index

This project includes comprehensive documentation organized by topic:

### Getting Started
- **[INSTALL.md](./INSTALL.md)** - Detailed installation guide with troubleshooting
- **[QUICKSTART_DEVIATIONS.md](./QUICKSTART_DEVIATIONS.md)** - 5-minute quick start for deviations analysis
- **[CLAUDE.md](./CLAUDE.md)** - Project overview and development commands

### Feature Documentation
- **[DEVIATIONS_FEATURE.md](./DEVIATIONS_FEATURE.md)** - Comprehensive deviations analysis guide
  - Temporal deviation detection algorithms
  - Bias detection and fairness analysis
  - OTEL data format requirements
  - Legal & compliance considerations
  - Statistical interpretation
- **[NEMO_FACTCHECKER_GUIDE.md](./NEMO_FACTCHECKER_GUIDE.md)** - FactChecker scanner implementation
  - NeMo GuardRails configuration
  - Fact-checking process and algorithms
  - Detection patterns and scoring
  - Testing and troubleshooting

### Deployment & CI/CD
- **[HF_SPACES_DEPLOYMENT.md](./HF_SPACES_DEPLOYMENT.md)** - Deploy to Hugging Face Spaces (5 minutes)
- **[STREAMLIT_CLOUD_FIX.md](./STREAMLIT_CLOUD_FIX.md)** - Streamlit Cloud deployment fixes
- **[GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)** - GitHub Actions CI/CD with Slack notifications

### Technical Documentation
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - Technical architecture overview
- **[REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md)** - Code refactoring history
- **Implementation Guides**: ALIGNMENT_CHECK_IMPROVEMENT.md, DIRECT_API_FALLBACK.md, and more

### Sample Data
- **OTEL-hr-agent-trace.json** - Age bias in HR screening
- **OTEL-bank-commission-agent-trace.json** - Temporal drift in refunds
- **OTEL-loan-applications-transactional.json** - Geographic bias in loans
- **Predefined scenarios** - Goal hijacking, data exfiltration, prompt injection tests

---

## Features

### Real-Time Testing Page
- **Multi-Scanner Testing**: Test 3 core security scanners with per-message validation
  - **PromptGuard**: Validates every user message for malicious prompts and injections (SAFE/WARNING/BLOCK)
  - **AlignmentCheck**: Validates every assistant message for goal hijacking and behavioral drift (SAFE/BLOCK)
  - **FactChecker**: Validates every assistant message for factual accuracy using GPT-4o-mini (SAFE/WARNING/BLOCK)
- **Count-Based Results**: Each scanner returns counts of safe, warning, and block decisions per message
- **Overall Decision**: Aggregated decision across all scanners (BLOCK > WARNING > SAFE)
- **Conversation Builder**: Create custom agent conversations with user messages, assistant responses, and actions
- **Predefined Scenarios**: Load example attack scenarios (Goal Hijacking, Data Exfiltration, Prompt Injection, etc.)
- **Visual Feedback**: Clear decision indicators with per-message counts and expandable details
- **Test History**: Track scanner performance over multiple tests
- **Save/Load**: Persist custom scenarios for reuse

### Deviations Analysis Page
- **OTEL Upload**: Upload OpenTelemetry JSON traces for analysis
- **Sample Data**: Built-in sample datasets demonstrating deviation and bias patterns
- **Automatic Metric Identification**: Intelligently identifies business-relevant metrics from telemetry
- **Temporal Deviation Detection**: Detect trends, period-to-period changes, and sudden spikes
- **Bias Detection**: Identify correlations with protected attributes (age, gender, location)
  - Disparity ratio calculation
  - Statistical significance testing (Cohen's d effect size)
  - Intersectional bias detection
- **Rich Visualizations**: Severity scores, temporal trend charts, group comparison charts
- **Agent Context**: Uses agent purpose to assess alignment concerns

---

## Architecture

### Core Components

```
multi_agent_demo/
├── app.py                          # Multi-page Streamlit application entry point
├── guards_demo_ui.py              # Legacy single-page real-time testing UI
├── firewall.py                    # Scanner orchestration & LlamaFirewall integration
├── direct_scanner_wrapper.py     # Direct API wrappers bypassing LlamaFirewall
├── page_modules/                  # Page implementations
│   ├── realtime_page.py          # Real-time testing page
│   └── deviations_page.py        # OTEL-based deviations analysis page
├── scanners/                      # Scanner implementations
│   ├── nemo_scanners.py          # NeMo GuardRails fact-checking scanner
│   └── data_disclosure_scanner.py # Presidio PII detection scanner
├── deviations/                    # Behavioral analysis modules
│   ├── otel_parser.py            # OpenTelemetry trace parser
│   ├── deviation_detector.py     # Temporal anomaly detection
│   └── bias_detector.py          # Cross-parameter bias detection
├── scenarios/                     # Scenario management
│   └── scenario_manager.py       # Load/save scenarios, predefined templates
└── ui/                            # UI components
    ├── common.py                  # Shared components (agent config, headers)
    ├── sidebar.py                 # Scanner configuration interface
    ├── conversation_builder.py   # Conversation creation/editing
    ├── results_display.py        # Test results visualization
    └── deviation_results.py      # Deviation/bias results visualization
```

### Security Scanners (3 Core + 1 Optional)

1. **PromptGuard Scanner** (LlamaFirewall)
   - **Validates**: Every user message
   - **Detects**: Malicious prompts and prompt injections
   - **Decisions**: BLOCK (clear injection), WARNING (suspicious patterns), SAFE (clean input)
   - **Model**: HuggingFace models via LlamaFirewall
   - **Fallback**: Heuristic pattern matching (31 suspicious patterns)

2. **AlignmentCheck Scanner** (LlamaFirewall + Together AI)
   - **Validates**: Every assistant message
   - **Detects**: Goal hijacking, off-topic redirects, behavioral drift
   - **Decisions**: BLOCK (misaligned), SAFE (aligned with both intended use AND user request)
   - **Model**: `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo`
   - **Validation Dimensions**: (A) Stays within stated purpose/role, (B) Addresses user's actual request
   - **Fallback**: Direct Together API when LlamaFirewall fails

3. **FactChecker Scanner** (NeMo GuardRails + OpenAI)
   - **Validates**: Every assistant message
   - **Detects**: Self-contradictions, ungrounded claims, fabricated details
   - **Decisions**: BLOCK (contradictions), WARNING (ungrounded claims), SAFE (factually sound)
   - **Model**: `gpt-4o-mini`
   - **Uses**: NeMo GuardRails framework for structured fact-checking

4. **DataDisclosureGuard Scanner** (Presidio) - *Optional*
   - **Validates**: Every message (user + assistant)
   - **Detects**: PII disclosure (with alignment checking)
   - **Decisions**: BLOCK (misaligned PII), WARNING (aligned PII), SAFE (no PII)
   - **Uses**: Microsoft Presidio for PII detection + alignment verification

---

## Installation

### Quick Install

```bash
# 1. Clone and setup
git clone <repository-url>
cd mutli-agent-demo
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements_minimal.txt
pip install llamafirewall
pip install nemoguardrails

# 3. Configure environment (create .env file)
OPENAI_API_KEY=your_key
TOGETHER_API_KEY=your_key
HF_TOKEN=your_token  # optional

# 4. Run application
streamlit run multi_agent_demo/app.py
```

**⚠️ Important**: Due to complex dependencies, see **[INSTALL.md](./INSTALL.md)** for:
- Detailed step-by-step installation
- Troubleshooting dependency conflicts
- Environment variable configuration
- Scanner availability by deployment type
- Streamlit Cloud deployment guide

### Dependencies

See [`requirements_minimal.txt`](./requirements_minimal.txt) for full list.

**Key Dependencies:**
```
streamlit>=1.37.0,<2.0.0           # Web framework
llamafirewall>=1.0.3,<2.0.0        # AI agent security framework
nemoguardrails>=0.16.0,<1.0.0      # NeMo GuardRails for fact-checking
presidio-analyzer>=2.2.356,<3.0.0  # PII detection
presidio-anonymizer>=2.2.356,<3.0.0 # PII anonymization
openai>=1.0.0,<2.0.0               # OpenAI API client
pandas>=2.0.0,<3.0.0               # Data manipulation
plotly>=5.17.0,<6.0.0              # Visualizations
numpy>=2.1.1,<3.0.0                # Numerical computation
python-dotenv>=1.0.0,<2.0.0        # Environment variables
```

---

## LLM Dependencies

### Required LLM Services

| Service | Model | Purpose | API Key Required |
|---------|-------|---------|------------------|
| **OpenAI** | `gpt-4o-mini` | Fact-checking (FactChecker scanner) | `OPENAI_API_KEY` |
| **Together AI** | `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` | Behavioral alignment checking (AlignmentCheck scanner) | `TOGETHER_API_KEY` |
| **HuggingFace** | PromptGuard models (via LlamaFirewall) | Prompt injection detection | `HF_TOKEN` (optional but recommended) |

### LLM Usage Details

#### OpenAI (gpt-4o-mini)
- **Endpoint**: `https://api.openai.com/v1/...`
- **Authentication**: Bearer token
- **Usage**:
  - AI-powered fact verification within NeMo GuardRails framework
  - Detects fabricated statistics, false claims, and factual inaccuracies
- **Fallback**: Pattern-based heuristics if API unavailable

#### Together AI (Llama-3.1-8B-Instruct-Turbo)
- **Endpoint**: `https://api.together.xyz/v1/chat/completions` (OpenAI-compatible)
- **Authentication**: Bearer token
- **Usage**:
  - Quantitative verification and consistency checking
  - PII alignment verification
  - Policy compliance checking
  - Goal hijacking detection
- **Fallback**: Direct API call if LlamaFirewall wrapper fails

#### HuggingFace (PromptGuard Models)
- **Framework**: LlamaFirewall's PromptGuard scanner
- **Authentication**: HF token (optional)
- **Usage**:
  - Pre-execution input validation
  - Malicious prompt detection
  - Prompt injection detection
- **Cache**: `HF_HOME=/tmp/.cache/huggingface`
- **Fallback**: Heuristic pattern matching (31 suspicious patterns)

### Optional NLP Models

#### spaCy Models (Optional)
- **Models**: `en_core_web_lg` or `en_core_web_sm`
- **Usage**: Enhanced text processing for NeMo GuardRails
- **Installation**: `python -m spacy download en_core_web_lg`
- **Fallback**: Pattern-only mode if unavailable

---

## External Resources

### HuggingFace Resources

- **Model Cache**: `/tmp/.cache/huggingface`
- **Environment Variables**:
  - `HF_TOKEN`: Authentication token (optional but recommended)
  - `HF_HOME`: Cache directory
  - `TRANSFORMERS_OFFLINE=0`: Allow model downloads
  - `HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1`
  - `HF_HUB_DISABLE_IMPLICIT_TOKEN=0`

### External APIs

| Service | Endpoint | Method | Rate Limits | Cost |
|---------|----------|--------|-------------|------|
| OpenAI | api.openai.com | REST | Varies by tier | Pay-per-token |
| Together AI | api.together.xyz | REST | Varies by tier | Pay-per-token |
| HuggingFace | api.huggingface.co | REST | Public: Limited | Free tier available |

### Open Source Libraries

#### UI & Visualization
- **Streamlit** (>=1.37.0): Multi-page web application framework
- **Plotly** (>=5.17.0): Interactive charts and visualizations
- **Pandas** (>=2.0.0): Data manipulation and analysis

#### AI & Security Frameworks
- **LlamaFirewall** (>=1.0.3): AI agent security scanner orchestration
- **NeMo GuardRails** (>=0.16.0): NVIDIA's AI-powered content safety framework
- **Presidio** (>=2.2.356): Microsoft's PII detection and anonymization

#### ML & Data Processing
- **NumPy** (>=2.1.1): Numerical computation (Streamlit Cloud compatible)
- **PyTorch**: Deep learning framework (configured offline mode)
- **spaCy**: NLP library for text processing (optional)

#### Core Utilities
- **python-dotenv** (>=1.0.0): Environment variable management
- **requests** (>=2.28.0): HTTP client for API calls
- **pydantic** (>=2.0.0): Data validation and settings management
- **click** (>=8.0.0): CLI framework
- **protobuf** (>=5.29.5): Protocol buffers for gRPC

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required for FactChecker scanner
OPENAI_API_KEY=sk-proj-...

# Required for AlignmentCheck scanner
TOGETHER_API_KEY=...

# Optional but recommended for PromptGuard
HF_TOKEN=hf_...

# Optional: Model cache directory
HF_HOME=/tmp/.cache/huggingface

# Optional: Offline mode
TRANSFORMERS_OFFLINE=0
HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1
HF_HUB_DISABLE_IMPLICIT_TOKEN=0
SPACY_WARNING_IGNORE=W008
```

### NeMo GuardRails Configuration

Configuration files in `nemo_config/`:
- `config.yml` - Main NeMo configuration
- `rails.co` - Rails configuration file

### LlamaFirewall Configuration

Scanner selection is dynamic via Streamlit session state. Available scanners:
1. **PromptGuard** - USER message scanning
2. **AlignmentCheck** - ASSISTANT message scanning
3. **FactChecker** - Custom NeMo-based fact verification
4. **DataDisclosureGuard** - Custom Presidio-based PII detection

---

## Usage

### Running the Application

```bash
# Multi-page application (recommended)
streamlit run multi_agent_demo/app.py

# Legacy single-page application (Real-time testing only)
streamlit run multi_agent_demo/guards_demo_ui.py
```

Access the application at `http://localhost:8501`

### Quick Start Guides

**New to Deviations Analysis?**
See **[QUICKSTART_DEVIATIONS.md](./QUICKSTART_DEVIATIONS.md)** for a 5-minute guided tutorial with:
- Sample data walkthrough
- OTEL data format requirements
- Results interpretation
- Common troubleshooting

**Want to understand FactChecker?**
See **[NEMO_FACTCHECKER_GUIDE.md](./NEMO_FACTCHECKER_GUIDE.md)** for detailed implementation guide.

### Basic Workflows

#### Real-Time Testing
1. Select scanners in sidebar → Configure agent → Build/load conversation → Run tests → Review results

**Predefined Scenarios**: Legitimate Banking, Goal Hijacking, Data Exfiltration, Prompt Injection, Fact-Checking Test

#### Deviations Analysis
1. Upload OTEL JSON or use sample data → Configure agent purpose → Run analysis → Review findings

**Sample Data**: HR CV Screening (age bias), Bank Commission Refunds (temporal drift), Loan Processing (zip bias)

For comprehensive usage documentation, see **[DEVIATIONS_FEATURE.md](./DEVIATIONS_FEATURE.md)**

---

## Modules & Functions

### Core Orchestration

#### `multi_agent_demo/firewall.py`
**Purpose**: Scanner orchestration and LlamaFirewall integration

**Key Functions:**
- `initialize_firewall(enabled_scanners: list) -> LlamaFirewall`
  - Initialize LlamaFirewall with selected scanners
  - Returns configured firewall instance

- `initialize_nemo_scanners() -> tuple`
  - Initialize NeMo GuardRails and Presidio scanners
  - Returns (FactCheckerScanner, DataDisclosureGuardScanner)

- `build_trace(conversation: list, agent_config: dict) -> Trace`
  - Convert conversation format to LlamaFirewall trace format
  - Handles USER, ASSISTANT, and ACTION messages

- `run_scanner_tests(conversation: list, agent_config: dict, enabled_scanners: list) -> dict`
  - Orchestrate all enabled scanner tests with per-message validation
  - Uses `scan_alignment_check_per_message()` and `scan_prompt_guard_per_message()`
  - Returns counts (safe/warning/block) and overall_decision for each scanner
  - Returns comprehensive test results with per-message decisions

#### `multi_agent_demo/direct_scanner_wrapper.py`
**Purpose**: Direct API wrappers bypassing LlamaFirewall

**Key Functions:**
- `scan_alignment_check_direct(trace: Trace, agent_config: dict) -> dict`
  - Direct Together AI API call for AlignmentCheck
  - Fallback when LlamaFirewall fails

- `scan_prompt_guard_direct(user_messages: list) -> dict`
  - Heuristic-based prompt injection detection
  - Pattern matching for 31 suspicious patterns

### Scanner Implementations

#### `multi_agent_demo/scanners/nemo_scanners.py`
**Purpose**: NeMo GuardRails scanner implementations

**Key Classes & Methods:**
- `FactCheckerScanner`
  - `__init__(config_path: str)`: Initialize with NeMo config
  - `scan(trace: Trace) -> ScanResult`: Perform fact-checking
  - `_nemo_fact_check(content: str) -> dict`: AI-powered fact verification using GPT-4o-mini

#### `multi_agent_demo/scanners/data_disclosure_scanner.py`
**Purpose**: PII detection using Microsoft Presidio

**Key Classes & Methods:**
- `DataDisclosureGuardScanner`
  - `__init__()`: Initialize Presidio analyzer
  - `scan(trace: Trace) -> ScanResult`: Detect PII in messages
  - Pattern-based recognizers: SSN, credit cards, financial data

### Deviations & Bias Detection

#### `multi_agent_demo/deviations/otel_parser.py`
**Purpose**: OpenTelemetry trace parsing and metric extraction

**Key Functions:**
- `parse_otel_data(otel_data: dict, agent_config: dict) -> dict`
  - Main entry point for OTEL parsing
  - Returns parsed metrics, temporal groupings, and parameter distributions

- `identify_business_metrics(otel_data: dict, agent_config: dict) -> list`
  - Intelligently identify business-relevant metrics semantically
  - Uses agent role and purpose for context

- `_extract_metrics(otel_data: dict) -> pd.DataFrame`
  - Extract numeric metrics from OTEL traces
  - Flatten nested attributes and normalize data

- `_group_by_time(df: pd.DataFrame, time_column: str) -> dict`
  - Group traces by weeks, days, or hours
  - Returns temporal aggregations

- `_bin_numeric_attribute(df: pd.DataFrame, attribute: str) -> pd.DataFrame`
  - Bin numeric values for age/income/tenure
  - Creates categorical groups for bias analysis

#### `multi_agent_demo/deviations/deviation_detector.py`
**Purpose**: Temporal anomaly and behavioral drift detection

**Key Functions:**
- `detect_deviations(parsed_data: dict, agent_config: dict) -> list`
  - Main entry point for deviation detection
  - Returns list of detected deviations with severity scores

- `_detect_temporal_drift(metric_name: str, temporal_data: dict, agent_config: dict) -> dict`
  - Detect monotonic increasing/decreasing trends
  - Uses linear regression to identify drift patterns

- `_detect_sudden_changes(metric_name: str, temporal_data: dict, agent_config: dict) -> dict`
  - Detect spikes, drops, and unusual variability
  - Uses z-score analysis for outlier detection

#### `multi_agent_demo/deviations/bias_detector.py`
**Purpose**: Cross-parameter bias and fairness detection

**Key Functions:**
- `detect_bias(parsed_data: dict, agent_config: dict) -> list`
  - Main entry point for bias detection
  - Returns list of detected biases with statistical significance

- `_detect_intersectional_bias(df: pd.DataFrame, metric: str, protected_attrs: list) -> list`
  - Detect bias from combinations of protected attributes
  - Analyzes age+gender, age+location, etc.

- Protected attribute detection: age, gender, race, location, disability, religion, etc.
- Statistical measures: Disparity ratio, Cohen's d effect size, group comparisons

### Scenarios & Data Management

#### `multi_agent_demo/scenarios/scenario_manager.py`
**Purpose**: Scenario loading, saving, and templates

**Key Functions:**
- `load_saved_scenarios() -> list`
  - Load persisted test scenarios from JSON files
  - Returns list of scenario dictionaries

- `save_scenario(scenario: dict, filename: str) -> bool`
  - Save custom scenario to JSON file
  - Returns success status

- `get_predefined_scenarios() -> dict`
  - Return built-in scenario templates
  - Includes: Legitimate Banking, Goal Hijacking, Data Exfiltration, Prompt Injection, Fact-Checking Test

### Page Modules

#### `multi_agent_demo/page_modules/realtime_page.py`
**Purpose**: Real-time testing page implementation

**Key Functions:**
- `render_realtime_page()`: Main page rendering function
- Integrates conversation builder, scanner selection, and results display

#### `multi_agent_demo/page_modules/deviations_page.py`
**Purpose**: OTEL-based deviations analysis page

**Key Functions:**
- `render_deviations_page()`: Main page rendering function
- Handles OTEL upload, sample data generation, and results visualization

### UI Components

#### `multi_agent_demo/ui/common.py`
**Purpose**: Shared UI components

**Key Functions:**
- `render_agent_config()`: Agent configuration form (name, role, purpose)
- `render_page_header(title: str, description: str)`: Page header with styling

#### `multi_agent_demo/ui/sidebar.py`
**Purpose**: Scanner configuration interface

**Key Functions:**
- `render_scanner_selection()`: Scanner enable/disable checkboxes
- `render_predefined_scenarios()`: Scenario selection dropdown

#### `multi_agent_demo/ui/conversation_builder.py`
**Purpose**: Conversation creation and editing

**Key Functions:**
- `render_conversation_builder(conversation: list) -> list`: Interactive conversation editor
- Add/remove user messages, assistant responses, and actions

#### `multi_agent_demo/ui/results_display.py`
**Purpose**: Scanner test results visualization

**Key Functions:**
- `render_overall_decision(result: dict)`: Display aggregated decision badge (SAFE/WARNING/BLOCK)
- `render_scanner_results(results: dict)`: Display per-scanner counts and per-message decisions
- `render_alignment_results(result: dict)`: Display AlignmentCheck count metrics
- `render_promptguard_results(result: dict)`: Display PromptGuard count metrics
- `render_factchecker_results(result: dict)`: Display FactChecker findings with counts
- `render_datadisclosure_results(result: dict)`: Display DataDisclosureGuard PII findings with counts

#### `multi_agent_demo/ui/deviation_results.py`
**Purpose**: Deviation and bias results visualization

**Key Functions:**
- `render_deviation_results(deviations: list, bias: list)`: Display findings with visualizations
- `render_severity_score(score: float)`: Severity gauge display
- `render_temporal_chart(data: dict)`: Temporal trend line charts
- `render_group_comparison(data: dict)`: Group comparison bar charts

---

## Sample Data

### OpenTelemetry Sample Data (OTEL Format)

Located in project root directory with `OTEL-` prefix:

#### 1. `OTEL-hr-agent-trace.json` - HR CV Screening Agent
**Purpose**: Demonstrates age-based bias detection

**Data Characteristics:**
- 5 candidate CVs with varying ages (32-48 years)
- Metrics: `relevancy.score`, `candidate.age`
- Bias pattern: Score disparity between under-40 and 40+ age groups
- Use case: Hiring discrimination detection

**Expected Findings:**
- Protected attribute bias on `candidate.age`
- Disparity ratio showing score differences
- Statistical significance (Cohen's d effect size)
- Fairness concerns and legal implications

#### 2. `OTEL-bank-commission-agent-trace.json` - Bank Commission Discount Agent
**Purpose**: Demonstrates temporal deviation (increasing refunds over time)

**Data Characteristics:**
- Weekly commission discount approvals over 4 weeks
- Metrics: `approved_discount_amount`, `week_number`
- Deviation: Increasing refund amounts indicating behavioral drift
- Use case: Financial policy compliance monitoring

**Expected Findings:**
- Temporal drift: Monotonic increasing trend in refunds
- Period-to-period changes: Week-over-week increases
- Alignment concern: Agent becoming overly generous

#### 3. `OTEL-loan-applications-transactional.json` - Loan Processing Agent
**Purpose**: Demonstrates geographic bias in loan approvals

**Data Characteristics:**
- Loan application decisions across different zip codes
- Metrics: `applicant_zip`, `credit_score`, `approval_decision`
- Bias pattern: High-income zip codes (90212) vs lower-income areas
- Use case: Lending discrimination detection

**Expected Findings:**
- Protected attribute bias on `applicant_zip`
- Disparity in approval rates by location
- Fair lending compliance concerns

### Scenario Data Files (JSON)

Pre-configured attack scenarios in root directory:

**Real-Time Testing Scenarios:**
- `Legitimate Banking.json` - Normal banking operations baseline
- `Goal Hijacking.json` - Off-topic redirect attempts
- `Data Exfiltration.json` - Sensitive information extraction attempts
- `Prompt Injection.json` - Direct prompt override attempts
- `Fact-Checking Test.json` - False claims and fabricated statistics

**Additional Test Scenarios:**
- HR hiring bias scenarios
- Financial unauthorized transactions
- Healthcare privacy violations
- Legal practice detection

### Generated Sample Data

The application can generate sample OTEL data dynamically:
- `ai_guards_scenario_YYYYMMDD_HHMMSS.json` - Auto-generated test scenarios with timestamps
- Dynamic loan/commission examples in deviations page

---

## Development

### Project Structure

```
mutli-agent-demo/
├── multi_agent_demo/          # Main application package
├── nemo_config/               # NeMo GuardRails configuration
├── venv/                      # Virtual environment
├── OTEL-*.json               # Sample OpenTelemetry data
├── *.json                    # Saved scenarios
├── .env                      # Environment variables (create this)
├── requirements_minimal.txt   # Python dependencies
├── INSTALL.md                # Detailed installation guide
├── CLAUDE.md                 # Claude Code instructions
├── README.md                 # This file
└── Dockerfile                # Docker configuration
```

### Adding New Scanners

1. Implement scanner class in `multi_agent_demo/scanners/`
2. Add initialization in `firewall.py::initialize_nemo_scanners()`
3. Add scanner option in `ui/sidebar.py::render_scanner_selection()`
4. Add results display in `ui/results_display.py`

### Adding New Deviation Detectors

1. Implement detector function in `deviations/deviation_detector.py` or `deviations/bias_detector.py`
2. Call from main detection functions (`detect_deviations()` or `detect_bias()`)
3. Add visualization in `ui/deviation_results.py`

### Testing

The project includes automated tests to verify scanner functionality and data processing.

#### Test Files

| Test File | Purpose | What It Tests | API Key Required |
|-----------|---------|---------------|------------------|
| `test_data_disclosure_fix.py` | DataDisclosureGuard false positive filtering | Verifies technical data (product IDs, SKUs, browser versions, timestamps) are NOT flagged as PII | No |
| `test_alignment_fix.py` | DataDisclosureGuard alignment checking | Verifies misaligned PII disclosure (e.g., asking for SSN when requesting weather) is correctly detected | No |
| `test_deviations.py` | Deviation and bias detection | Tests temporal deviations (refunds increasing over time) and bias patterns (age bias in hiring) | No |
| `test_alignment_check.py` | AlignmentCheck scanner automation | Tests goal hijacking detection, off-topic redirects, and aligned conversations | Yes (TOGETHER_API_KEY) |
| `test_alignment.py` | Interactive AlignmentCheck testing | Menu-driven interface for testing AlignmentCheck scanner (legacy) | No |

#### Running Tests

**Run all tests:**
```bash
source venv/bin/activate

# Core tests (no API keys required)
python test_data_disclosure_fix.py
python test_alignment_fix.py
python test_deviations.py

# Optional: AlignmentCheck scanner test (requires TOGETHER_API_KEY)
export TOGETHER_API_KEY=your_key_here
python test_alignment_check.py

# Interactive AlignmentCheck tester (legacy)
python test_alignment.py
```

**Run individual tests:**
```bash
# Test false positive filtering
python test_data_disclosure_fix.py
# Expected: ✅ TEST PASSED: No false positives detected!

# Test AlignmentCheck scanner (requires TOGETHER_API_KEY)
export TOGETHER_API_KEY=your_key_here
python test_alignment_check.py
# Expected: ✅ ALL TESTS PASSED (4/4 tests passed)
```

**Quick test commands:**
```bash
# Test specific scanner
python -c "from multi_agent_demo.scanners.nemo_scanners import FactCheckerScanner; scanner = FactCheckerScanner('nemo_config'); print(scanner)"

# Test OTEL parsing
python -c "import json; from multi_agent_demo.deviations.otel_parser import parse_otel_data; data = json.load(open('OTEL-hr-agent-trace.json')); print(parse_otel_data(data, {'name': 'HR Agent', 'role': 'recruiter', 'purpose': 'screen CVs'}))"
```

#### Continuous Integration

The project uses GitHub Actions to automatically run tests on commits to the `main` branch. Test failures are reported to a Slack channel for immediate notification.

**Tests Running in CI/CD:**

**Core Tests (Always Run - No API Keys):**
- ✅ `test_data_disclosure_fix.py` - DataDisclosureGuard false positive filtering
- ✅ `test_alignment_fix.py` - DataDisclosureGuard PII alignment checking
- ✅ `test_deviations.py` - Temporal deviation and bias detection

**AlignmentCheck Test (API Key Configured ✅):**
- ✅ `test_alignment_check.py` - AlignmentCheck goal hijacking detection
  - **Status:** ENABLED (TOGETHER_API_KEY configured)
  - **Cost:** ~$0.18/1M tokens per test run
  - **Tests:** Goal hijacking, off-topic redirects, aligned conversations
  - **Note:** To disable, remove `TOGETHER_API_KEY` from GitHub repository secrets

**Test Summary:**
- **Total tests:** 4/4 (3 core + 1 AlignmentCheck)
- **API costs:** ~$0.01-0.02 per CI/CD run (AlignmentCheck only)
- **Run time:** ~5-8 minutes total

**What You'll See in GitHub Actions:**
```
✓ Run DataDisclosureGuard false positive test
✓ Run DataDisclosureGuard alignment test
✓ Run deviation/bias detection test
✓ Run AlignmentCheck scanner test (optional)
✓ Tests Passed: 4/4
```

**Slack Notification (if configured):**
- Success: "✅ Tests Passed: 4/4 ✅"
- Failure: "❌ Tests Failed: X/4" with details

See `.github/workflows/test.yml` for CI configuration.

### Docker Deployment

```bash
# Build Docker image
docker build -t ai-guards-demo .

# Run container
docker run -p 8501:8501 --env-file .env ai-guards-demo
```

---

## Deployment

### Hugging Face Spaces (Recommended)

Deploy your application to Hugging Face Spaces in 5 minutes:

```bash
# Add HF remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/ai-guards-demo

# Push
git push hf main

# Add secrets in HF Spaces settings
# - OPENAI_API_KEY
# - TOGETHER_API_KEY
# - HF_TOKEN
```

Your app will be live at: `https://huggingface.co/spaces/YOUR_USERNAME/ai-guards-demo`

**See [HF_SPACES_DEPLOYMENT.md](./HF_SPACES_DEPLOYMENT.md) for:**
- Complete deployment guide
- Hardware tier recommendations
- Cost comparison ($0 free tier, $25/mo upgrade)
- Performance optimization tips
- Alternative deployment options (Railway.app)

### Streamlit Cloud

For Streamlit Cloud deployment, see **[STREAMLIT_CLOUD_FIX.md](./STREAMLIT_CLOUD_FIX.md)** for:
- Secrets configuration
- Scanner compatibility issues
- Troubleshooting common errors

---

## API Rate Limits & Costs

### OpenAI (gpt-4o-mini)
- **Rate Limits**: Varies by tier (check OpenAI dashboard)
- **Cost**: ~$0.15/1M input tokens, ~$0.60/1M output tokens (as of 2024)
- **Usage**: Fact-checking only (relatively low volume)

### Together AI (Llama-3.1-8B)
- **Rate Limits**: Varies by tier
- **Cost**: ~$0.18/1M tokens (as of 2024)
- **Usage**: Every AlignmentCheck scan (moderate volume)

### HuggingFace
- **Rate Limits**: Public API limited, private endpoints unlimited
- **Cost**: Free for public models, paid for private endpoints
- **Usage**: Model downloads (cached, infrequent)

### Cost Optimization Tips
- Cache scanner results when testing same scenarios
- Use PromptGuard fallback (heuristic patterns) when possible
- Batch OTEL analysis to minimize API calls
- Consider self-hosting models for high-volume usage

---

## Troubleshooting

### Quick Fixes

| Issue | Quick Solution | Details |
|-------|---------------|---------|
| **Module Import Errors** | `pip install -r requirements_minimal.txt` | See [INSTALL.md](./INSTALL.md) |
| **API Key Not Found** | Create `.env` with API keys | See Configuration section |
| **HuggingFace Model Download Fails** | Set `HF_TOKEN` in `.env` | See [INSTALL.md](./INSTALL.md) |
| **NeMo Dependency Conflicts** | Install in specific order | See [INSTALL.md](./INSTALL.md) |
| **Deviations: "No traces found"** | Check JSON format | See [QUICKSTART_DEVIATIONS.md](./QUICKSTART_DEVIATIONS.md) |
| **FactChecker Initialization Failed** | Verify `OPENAI_API_KEY` | See [NEMO_FACTCHECKER_GUIDE.md](./NEMO_FACTCHECKER_GUIDE.md) |

### Detailed Troubleshooting Guides

- **Installation Issues**: See [INSTALL.md](./INSTALL.md) for comprehensive troubleshooting
- **Deviations Analysis**: See [QUICKSTART_DEVIATIONS.md](./QUICKSTART_DEVIATIONS.md) troubleshooting section
- **FactChecker Scanner**: See [NEMO_FACTCHECKER_GUIDE.md](./NEMO_FACTCHECKER_GUIDE.md) troubleshooting section
- **Deployment Issues**: See [HF_SPACES_DEPLOYMENT.md](./HF_SPACES_DEPLOYMENT.md) or [STREAMLIT_CLOUD_FIX.md](./STREAMLIT_CLOUD_FIX.md)

---

## License

GPL-3.0

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

## Support

### Getting Help

**First Steps:**
1. Check the [Documentation Index](#documentation-index) for relevant guides
2. Review [Troubleshooting](#troubleshooting) section above
3. Try the sample data and predefined scenarios

**Common Questions:**
- **Installation problems?** → [INSTALL.md](./INSTALL.md)
- **How do I analyze OTEL data?** → [QUICKSTART_DEVIATIONS.md](./QUICKSTART_DEVIATIONS.md)
- **How does FactChecker work?** → [NEMO_FACTCHECKER_GUIDE.md](./NEMO_FACTCHECKER_GUIDE.md)
- **How to deploy?** → [HF_SPACES_DEPLOYMENT.md](./HF_SPACES_DEPLOYMENT.md)
- **Development commands?** → [CLAUDE.md](./CLAUDE.md)

**Still Need Help?**
- Open GitHub issue for bugs or feature requests
- Include error messages, logs, and steps to reproduce

---

## Acknowledgments

- **LlamaFirewall**: AI agent security framework
- **NeMo GuardRails**: NVIDIA's content safety framework
- **Presidio**: Microsoft's PII detection library
- **OpenAI**: GPT-4o-mini for fact-checking
- **Together AI**: Llama-3.1-8B for alignment checking
- **HuggingFace**: Model hosting and distribution
