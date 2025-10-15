# Hugging Face Spaces Setup Guide

## Prerequisites
- GitHub account with your `mutli-agent-demo` repo
- API keys ready:
  - OpenAI API key
  - Together AI API key
  - (Optional) Hugging Face token

## Step-by-Step Setup

### 1. Create Hugging Face Account
1. Go to https://huggingface.co
2. Click "Sign Up"
3. Create account (free)
4. Verify your email

### 2. Create a New Space
1. Click your profile → "New Space"
2. Fill in details:
   - **Owner:** Your username
   - **Space name:** `ai-agent-guards-demo` (or your choice)
   - **License:** Apache 2.0 (recommended)
   - **Select the Space SDK:** Choose **Docker** ⚠️ Important!
   - **Space hardware:** CPU basic (free tier)
   - **Visibility:** Public (or Private if preferred)
3. Click "Create Space"

### 3. Connect to GitHub

**Option A: Direct GitHub Integration (Easiest)**
1. In your new Space, go to "Settings" tab
2. Scroll to "Repository"
3. Click "Link to a GitHub repository"
4. Select: `shefing/mutli-agent-demo`
5. Choose branch: `main`
6. Save

**Option B: Manual Git Push**
```bash
# Add Hugging Face as remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/ai-agent-guards-demo

# Push to Hugging Face
git push hf main
```

### 4. Add Environment Secrets

1. In your Space, go to "Settings" tab
2. Scroll to "Variables and secrets"
3. Click "New secret" and add each:

**Required Secrets:**
```
Name: OPENAI_API_KEY
Value: sk-proj-... (your OpenAI key)

Name: TOGETHER_API_KEY
Value: ... (your Together AI key)

Name: HF_TOKEN
Value: hf_... (your Hugging Face token - optional)
```

4. Click "Save" for each secret

### 5. Deploy

Once you push or link to GitHub:
1. Hugging Face will automatically start building
2. Watch the build logs in the "Logs" tab
3. Build takes ~5-10 minutes (downloading dependencies)
4. When complete, your app will be live at:
   ```
   https://huggingface.co/spaces/YOUR_USERNAME/ai-agent-guards-demo
   ```

### 6. Verify Deployment

Check that all scanners work:
1. ✅ **AlignmentCheck** - Should show in scanner list
2. ✅ **PromptGuard** - Should show in scanner list
3. ✅ **FactsChecker** - Should show in scanner list (requires NeMo)
4. ✅ **DataDisclosureGuard** - Should show in scanner list (requires Presidio)

Test a scenario:
1. Select "Legitimate Banking" scenario
2. Enable all 4 scanners
3. Click "Run Scanner Tests"
4. All should return results

---

## Troubleshooting

### Build Fails
- Check "Logs" tab for error details
- Common issues:
  - Missing `Dockerfile` (make sure it's in repo root)
  - Out of memory (upgrade to better hardware tier)

### App Starts But Scanners Missing
- Check environment secrets are set correctly
- Look for error messages in app console

### spaCy Model Issues
If you see "model not found":
- The Dockerfile installs `en_core_web_lg` automatically
- Check build logs to see if download succeeded

---

## What Happens During Build

The Dockerfile does:
1. Uses Python 3.11 (stable, good spaCy support)
2. Installs system build tools
3. Installs all Python packages from `requirements.txt`
4. Downloads spaCy model `en_core_web_lg` (400MB)
5. Copies your application code
6. Starts Streamlit on port 8501

**Build time:** ~5-10 minutes
**Image size:** ~4GB (due to ML dependencies)

---

## Updating Your App

After initial deployment, updates are automatic:

**If using GitHub integration:**
1. Push changes to your GitHub repo
2. Hugging Face auto-rebuilds

**If using direct git:**
```bash
git push hf main
```

---

## Cost

**Free Tier:**
- ✅ 2 CPU cores
- ✅ 16GB RAM
- ✅ 50GB storage
- ✅ No time limits
- ⚠️ May have cold starts if inactive

**Upgrade Options:**
- CPU upgrade (2 → 8 cores): ~$5/month
- GPU (if needed): ~$30/month
- Persistent storage: Available

For your demo, **free tier is perfect**.

---

## Your Space URL

Once deployed, your app will be at:
```
https://huggingface.co/spaces/YOUR_USERNAME/ai-agent-guards-demo
```

You can:
- Share this URL publicly
- Embed in other sites
- Use as live demo for presentations

---

## Files Ready for Deployment

All files are already in your repo:

- ✅ `Dockerfile` - Container definition
- ✅ `requirements.txt` - Python dependencies
- ✅ `.env.example` - Template for secrets
- ✅ `packages.txt` - System packages (not used in Docker)
- ✅ `.python-version` - Python version (not used in Docker)

The Dockerfile has everything needed - you don't need to modify anything!

---

## Quick Checklist

- [ ] Create Hugging Face account
- [ ] Create new Space (SDK: Docker)
- [ ] Link to GitHub repo `shefing/mutli-agent-demo`
- [ ] Add secrets: `OPENAI_API_KEY`, `TOGETHER_API_KEY`, `HF_TOKEN`
- [ ] Wait for build to complete (~5-10 min)
- [ ] Test all 4 scanners work
- [ ] Share your Space URL! 🎉

---

## Support

If you encounter issues:
1. Check build logs in Hugging Face "Logs" tab
2. Check this guide: https://huggingface.co/docs/hub/spaces-sdks-docker
3. Hugging Face community forums: https://discuss.huggingface.co

**Good luck with your deployment! 🚀**
