# Deployment Guide - AI Agent Guards Demo

## Current Issue with Streamlit Cloud

Streamlit Cloud has compatibility issues with:
- Python 3.13 and spaCy/blis compilation
- Runtime model downloads (permission errors)
- Heavy ML dependencies

## Recommended Alternatives

### 🏆 Option 1: Hugging Face Spaces (Recommended)

**Best for:** ML/AI applications with heavy dependencies

**Steps:**
1. Go to https://huggingface.co/spaces
2. Create new Space (Streamlit + Docker)
3. Connect to your GitHub repo
4. The included `Dockerfile` will handle everything

**Advantages:**
- Built for ML applications
- Better resource allocation
- No dependency hell
- Free tier: 2 CPUs, 16GB RAM

---

### Option 2: Railway.app

**Best for:** Simple deployment with better resources

**Steps:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

**Pricing:** $5/month for 512MB RAM (free $5 credit/month)

---

### Option 3: Render.com

**Best for:** Docker-based deployments

**Steps:**
1. Go to https://render.com
2. New > Web Service
3. Connect GitHub repo
4. Select "Docker" as environment
5. Deploy

**Pricing:** Free tier available, $7/month for 512MB

---

### Option 4: Google Cloud Run

**Best for:** Production deployments with auto-scaling

**Steps:**
```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-guards-demo

# Deploy to Cloud Run
gcloud run deploy ai-guards-demo \
  --image gcr.io/PROJECT_ID/ai-guards-demo \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Pricing:** Pay per use (generous free tier)

---

## Quick Start: Deploy to Hugging Face Spaces

### 1. Create Account
- Go to https://huggingface.co
- Sign up (free)

### 2. Create New Space
- Click "New Space"
- Name: `ai-agent-guards-demo`
- SDK: **Docker**
- License: Apache 2.0 (or your choice)

### 3. Connect GitHub
- In Space settings, connect to your GitHub repo: `shefing/mutli-agent-demo`
- Or push directly to HF:

```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/ai-agent-guards-demo
git push hf main
```

### 4. Add Secrets
In Space settings, add environment variables:
- `OPENAI_API_KEY`
- `TOGETHER_API_KEY`
- `HF_TOKEN`

### 5. Deploy
Hugging Face will automatically:
- Build the Docker image
- Install all dependencies
- Download spaCy models
- Start the Streamlit app

---

## Comparison Table

| Platform | Free Tier | RAM | Build Time | ML Support | Ease of Use |
|----------|-----------|-----|------------|------------|-------------|
| **Streamlit Cloud** | ✅ Yes | 1GB | Fast | ⚠️ Limited | ⭐⭐⭐⭐⭐ |
| **Hugging Face** | ✅ Yes | 16GB | Medium | ✅ Excellent | ⭐⭐⭐⭐ |
| **Railway** | ⚠️ $5 credit | 512MB+ | Fast | ✅ Good | ⭐⭐⭐⭐ |
| **Render** | ⚠️ Limited | 512MB | Slow | ✅ Good | ⭐⭐⭐⭐ |
| **Cloud Run** | ✅ Yes | 2GB+ | Fast | ✅ Excellent | ⭐⭐⭐ |
| **Fly.io** | ⚠️ Limited | 256MB | Fast | ✅ Good | ⭐⭐⭐ |

---

## Local Development

To run locally (always works):

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run multi_agent_demo/guards_demo_ui.py
```

---

## Troubleshooting

### spaCy Model Issues
If you see "model not found" errors:
```bash
python -m spacy download en_core_web_lg
```

### Presidio Issues
If Presidio fails to initialize, DataDisclosureGuard will be disabled but other scanners will work.

### NeMo GuardRails Issues
If NeMo fails, FactsChecker will be disabled but other scanners will work.

---

## Files for Deployment

- ✅ `Dockerfile` - Container definition for Docker-based platforms
- ✅ `requirements.txt` - Python dependencies
- ✅ `packages.txt` - System packages (for Streamlit Cloud)
- ✅ `.python-version` - Python version specification
- ✅ `.env.example` - Template for environment variables

---

## Recommended: Hugging Face Spaces

For this specific application (AI security guards with ML dependencies), **Hugging Face Spaces** is the best choice because:

1. ✅ **Built for AI/ML** - Expects heavy dependencies like spaCy, transformers
2. ✅ **Docker support** - Full control over environment
3. ✅ **Better resources** - 16GB RAM vs 1GB on Streamlit Cloud
4. ✅ **Community** - Perfect audience for AI security tools
5. ✅ **Free tier** - Generous for development and demos
6. ✅ **No cold starts** - Always-on option available

Would you like me to help you set up deployment on Hugging Face Spaces?
