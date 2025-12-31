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

# AI Agent Guards Testing Application

A comprehensive demonstration application for testing AI Agent security scanners and behavioral monitoring. Features real-time security testing with multiple scanners and post-hoc behavioral analysis using OpenTelemetry traces.

**Live Demo**: Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

## Table of Contents
- [Overview](#overview)
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

---

## Overview

This application provides two complementary approaches to AI agent security and monitoring:

### 1. Real-Time Security Testing
Interactive web interface for testing AI agent security scanners against custom conversation scenarios. Test how different security scanners detect malicious inputs, goal hijacking, data exfiltration, and factual inaccuracies.

### 2. Post-Hoc Behavioral Analysis
Analyze OpenTelemetry traces to detect temporal deviations and bias patterns in agent behavior over time. Identify behavioral drift, fairness issues, and compliance concerns from production telemetry data.

---

## Features

### Real-Time Testing Page
- **Multi-Scanner Testing**: Test 3 core security scanners simultaneously
  - **PromptGuard**: Pre-execution input validation to detect malicious prompts and prompt injections
  - **AlignmentCheck**: Runtime behavioral monitoring using Llama-3.1-8B for goal hijacking detection
  - **FactChecker**: AI-powered fact verification using NeMo GuardRails + GPT-4o-mini
- **Conversation Builder**: Create custom agent conversations with user messages, assistant responses, and actions
- **Predefined Scenarios**: Load example attack scenarios (Goal Hijacking, Data Exfiltration, Prompt Injection, etc.)
- **Visual Feedback**: Real-time score visualization with gauges, metrics, and decision indicators
- **Test History**: Track scanner performance over multiple tests with trend visualization
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
   - Pre-execution input validation
   - Detects malicious prompts and prompt injections
   - Uses HuggingFace models via LlamaFirewall
   - Fallback: Heuristic pattern matching (31 suspicious patterns)

2. **AlignmentCheck Scanner** (LlamaFirewall + Together AI)
   - Runtime behavioral monitoring
   - Detects goal hijacking and behavioral drift
   - Model: `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo`
   - Fallback: Direct Together API when LlamaFirewall fails

3. **FactChecker Scanner** (NeMo GuardRails + OpenAI)
   - AI-powered fact verification
   - Detects fabricated statistics and false claims
   - Model: `gpt-4o-mini`
   - Uses NeMo GuardRails framework for structured checking

4. **DataDisclosureGuard Scanner** (Presidio) - *Optional*
   - PII detection using Microsoft Presidio
   - Pattern-based recognizers for SSN, credit cards, financial data

---

## Installation

### Prerequisites
- Python 3.9+
- pip package manager
- API keys (see Configuration section)

### Step-by-Step Installation

**⚠️ Important**: Due to complex dependencies, follow the step-by-step guide:

```bash
# 1. Clone the repository
git clone <repository-url>
cd mutli-agent-demo

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install minimal dependencies first
pip install -r requirements_minimal.txt

# 4. Install LlamaFirewall
pip install llamafirewall

# 5. Install NeMo GuardRails (may have conflicts - see INSTALL.md)
pip install nemoguardrails

# 6. Configure LlamaFirewall (optional)
llamafirewall configure
```

For troubleshooting dependency conflicts, see [`INSTALL.md`](./INSTALL.md)

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

### Real-Time Testing Workflow

1. **Select Scanners**: Enable desired scanners in the sidebar (PromptGuard, AlignmentCheck, FactChecker)
2. **Configure Agent**: Set agent name, role, and purpose in the sidebar
3. **Build Conversation**:
   - Load a predefined scenario OR
   - Create custom conversation with user messages, assistant responses, and actions
4. **Run Tests**: Click "Run Scanner Tests" to test all enabled scanners
5. **Review Results**:
   - View AlignmentCheck gauge score
   - Check PromptGuard violation alerts
   - Expand NeMo GuardRails sections for detailed fact-checking
6. **Save Scenario**: Save custom scenarios for future testing

### Deviations Analysis Workflow

1. **Configure Agent**: Set agent name, role, and purpose in shared configuration
2. **Load Data**:
   - Upload your own OpenTelemetry JSON trace OR
   - Use sample data (HR Agent, Bank Commission Agent, Loan Processing Agent)
3. **Analyze**: Click "Analyze OTEL Data" to detect deviations and bias
4. **Review Results**:
   - View overall severity scores
   - Expand deviation findings (temporal drift, sudden changes)
   - Expand bias findings (protected attribute correlations)
   - Examine visualizations (trend charts, group comparisons)
5. **Take Action**: Use recommendations to address identified issues

### Predefined Scenarios

**Real-Time Testing:**
- **Legitimate Banking**: Normal banking operations (baseline)
- **Goal Hijacking**: Attempts to redirect agent from intended purpose
- **Data Exfiltration**: Attempts to extract sensitive information
- **Prompt Injection**: Direct attempts to override agent instructions
- **Fact-Checking Test**: Tests detection of false claims and fabricated statistics

**Deviations Analysis (Sample OTEL Data):**
- **HR CV Screening**: Age-based bias in candidate scoring
- **Bank Commission Refunds**: Temporal drift (increasing refund amounts)
- **Loan Processing**: Zip code bias in approval decisions

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

- `test_prompt_guard(firewall: LlamaFirewall, user_messages: list) -> dict`
  - Test PromptGuard scanner with fallback
  - Returns decisions, scores, and violations

- `test_alignment_check(firewall: LlamaFirewall, trace: Trace) -> dict`
  - Test AlignmentCheck scanner
  - Returns alignment scores and decisions

- `run_scanner_tests(conversation: list, agent_config: dict, enabled_scanners: list) -> dict`
  - Orchestrate all enabled scanner tests
  - Returns comprehensive test results

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
- `render_test_results(results: dict)`: Display AlignmentCheck gauge, PromptGuard alerts
- `render_nemo_results(nemo_results: dict)`: Display fact-checking findings

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

```bash
# Run with sample data
streamlit run multi_agent_demo/app.py

# Test specific scanner
python -c "from multi_agent_demo.scanners.nemo_scanners import FactCheckerScanner; scanner = FactCheckerScanner('nemo_config'); print(scanner)"

# Test OTEL parsing
python -c "import json; from multi_agent_demo.deviations.otel_parser import parse_otel_data; data = json.load(open('OTEL-hr-agent-trace.json')); print(parse_otel_data(data, {'name': 'HR Agent', 'role': 'recruiter', 'purpose': 'screen CVs'}))"
```

### Docker Deployment

```bash
# Build Docker image
docker build -t ai-guards-demo .

# Run container
docker run -p 8501:8501 --env-file .env ai-guards-demo
```

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

### Common Issues

**1. Module Import Errors**
```bash
# Solution: Follow step-by-step installation in INSTALL.md
pip install -r requirements_minimal.txt
pip install llamafirewall
pip install nemoguardrails
```

**2. API Key Not Found**
```bash
# Solution: Create .env file in project root
echo "OPENAI_API_KEY=sk-..." > .env
echo "TOGETHER_API_KEY=..." >> .env
```

**3. HuggingFace Model Download Fails**
```bash
# Solution: Set HF_TOKEN in .env
echo "HF_TOKEN=hf_..." >> .env

# Or configure offline mode
echo "TRANSFORMERS_OFFLINE=1" >> .env
```

**4. NeMo GuardRails Dependency Conflicts**
```bash
# Solution: Install in specific order (see INSTALL.md)
pip install nemoguardrails --no-deps
pip install -r requirements_minimal.txt
```

**5. spaCy Model Not Found**
```bash
# Solution: Download spaCy model (optional)
python -m spacy download en_core_web_lg
# Or use pattern-only mode (automatic fallback)
```

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

For issues and questions:
- Check [INSTALL.md](./INSTALL.md) for installation troubleshooting
- Check [CLAUDE.md](./CLAUDE.md) for development guidance
- Review sample OTEL data for usage examples
- Open GitHub issue for bugs or feature requests

---

## Acknowledgments

- **LlamaFirewall**: AI agent security framework
- **NeMo GuardRails**: NVIDIA's content safety framework
- **Presidio**: Microsoft's PII detection library
- **OpenAI**: GPT-4o-mini for fact-checking
- **Together AI**: Llama-3.1-8B for alignment checking
- **HuggingFace**: Model hosting and distribution
