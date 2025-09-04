# Multi-Domain AI Agent Applications with LlamaFirewall Integration

This project demonstrates a multi-agent system with specialized agents for different domains (banking, travel, email), all protected by LlamaFirewall security.

## Features

- **Multiple Specialized Agents**: Banking, Travel, and Email agents with domain-specific capabilities
- **Security Integration**: LlamaFirewall with PromptGuard and AlignmentCheck scanners
- **Scenario Testing**: Automated testing of both legitimate and attack scenarios
- **Interactive Demo**: Chat with the multi-agent system directly

## Setup Instructions

### Prerequisites

- Python 3.8+
- OpenAI API key
- Together API key (for LlamaFirewall AlignmentCheck)
- HuggingFace token (for PromptGuard models)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure LlamaFirewall
llamafirewall configure
```

### Environment Configuration

Create a `.env` file in the project root with the following:

```
# OpenAI API key for the main LLM
OPENAI_API_KEY=your_openai_key_here

# Together API key for LlamaFirewall AlignmentCheck
TOGETHER_API_KEY=your_together_key_here

# HuggingFace token for PromptGuard models
HF_TOKEN=your_huggingface_token

# Optional: Organization settings
OPENAI_ORGANIZATION=your_org_id
```

## Usage

Run the main application:

```bash
python main.py
```

Choose from the following options:
1. Interactive Demo - Chat with the multi-agent system
2. Scenario Testing - Run automated alignment check scenarios
3. Both - Run tests followed by interactive demo

## Project Structure

```
multi_agent_demo/
├── src/
│   ├── agents/       # Specialized agents
│   ├── tools/        # Domain-specific tools
│   ├── security/     # LlamaFirewall integration
│   └── demo/         # Test scenarios
├── main.py           # Main application
├── requirements.txt  # Dependencies
└── README.md         # This file
```