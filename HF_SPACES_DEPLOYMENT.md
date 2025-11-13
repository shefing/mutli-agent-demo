# Deploying to Hugging Face Spaces

## Quick Start (5 minutes)

### 1. Create Space
1. Go to https://huggingface.co/new-space
2. Choose:
   - **Name**: `ai-guards-demo`
   - **SDK**: Streamlit
   - **Hardware**: CPU basic (free) or CPU upgrade ($25/mo)
   - **Visibility**: Public or Private

### 2. Add Configuration
Create `README.md` in repo root:

```yaml
---
title: AI Agent Guards Demo
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.32.0
app_file: multi_agent_demo/guards_demo_ui.py
pinned: false
license: mit
---

# AI Agent Guards Testing Application

Demo app for testing AI Agent Guards (security scanners) with custom scenarios.

## Features
- PromptGuard: Detects malicious prompts
- AlignmentCheck: Identifies goal hijacking
- FactChecker: AI-powered fact verification
```

### 3. Push to HF
```bash
# Add HF remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/ai-guards-demo

# Push
git push hf main
```

### 4. Add Secrets
In HF Spaces settings, add:
- `OPENAI_API_KEY`
- `TOGETHER_API_KEY`
- `HF_TOKEN`

### 5. Done!
Your app will be live at: `https://huggingface.co/spaces/YOUR_USERNAME/ai-guards-demo`

## Cost Comparison

| Tier | vCPU | RAM | Storage | Cost | Best For |
|------|------|-----|---------|------|----------|
| CPU Basic (Free) | 2 | 16GB | 50GB | $0 | Testing, 1-3 users |
| CPU Upgrade | 8 | 32GB | 100GB | $25/mo | Production, 3-10 users |
| GPU T4 | 4 | 16GB | 100GB | $60/mo | Large models |

## Performance Tips

1. **Use CPU Basic first** - likely sufficient for your load
2. **Monitor usage** - HF provides metrics dashboard
3. **Upgrade if needed** - one-click upgrade to $25/mo tier
4. **Cache models** - your app already does this well

## Alternative: Railway.app

If HF doesn't work:
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Cost: ~$10-20/mo for similar resources.
