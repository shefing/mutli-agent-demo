# Deploy to Hugging Face Spaces - Quick Guide

## Your Current Setup
✅ You already have HF remote: `git@hf.co:spaces/Shefing/aitruism`
✅ README.md updated with Streamlit SDK config
✅ Enhanced AlignmentCheck with quantitative detection

## Step 1: Commit All Changes

```bash
# Add all modified files
git add README.md
git add HF_SPACES_DEPLOYMENT.md
git add DEPLOY_NOW.md
git add multi_agent_demo/direct_scanner_wrapper.py
git add multi_agent_demo/firewall.py
git add multi_agent_demo/ui/conversation_builder.py
git add multi_agent_demo/ui/results_display.py

# Commit changes
git commit -m "feat: Prepare for HF Spaces deployment with enhanced quantitative detection

- Update README.md with Streamlit SDK configuration
- Add quantitative misalignment detection (35 vs 28 orders)
- Support .txt file import for scenarios
- Improve AlignmentCheck prompt focusing
- Add deployment documentation"
```

## Step 2: Push to Hugging Face

```bash
# Push to HF Spaces
git push huggingface main
```

**What happens next:**
- HF will detect the Streamlit SDK from README.md
- It will install dependencies from requirements_minimal.txt
- Your app will be live in ~2-5 minutes at: https://huggingface.co/spaces/Shefing/aitruism

## Step 3: Add API Keys (Secrets)

After deployment starts, add your secrets:

1. Go to: https://huggingface.co/spaces/Shefing/aitruism/settings
2. Scroll to **Repository secrets**
3. Click **+ Add a new secret**
4. Add these three secrets:

| Name | Value |
|------|-------|
| `OPENAI_API_KEY` | Your OpenAI API key (starts with sk-proj-...) |
| `TOGETHER_API_KEY` | Your Together AI key |
| `HF_TOKEN` | Your HuggingFace token (optional, for PromptGuard) |

5. After adding secrets, click **Restart this Space** (top right)

## Step 4: Test Your Deployment

1. Go to: https://huggingface.co/spaces/Shefing/aitruism
2. Wait for "Building" to complete (~2-5 minutes)
3. Test with your delivery route scenario
4. Verify AlignmentCheck detects the 35 vs 28 orders discrepancy

## Monitoring Performance

Watch the **Logs** tab to see:
- Build progress
- Runtime logs
- Scanner debug output (🔢 QUANTITATIVE REQUIREMENT DETECTED, etc.)

## Troubleshooting

### If build fails:
- Check the **Logs** tab for error messages
- Common issues:
  - Missing dependencies → Update requirements_minimal.txt
  - Port conflicts → Streamlit handles this automatically
  - Memory issues → Upgrade to CPU Upgrade ($25/mo)

### If app is slow:
- Check the **Metrics** tab for CPU/RAM usage
- If consistently >80% → Consider upgrading to CPU Upgrade
- For 3 users, CPU Basic should be fine

### If scanners fail:
- Check Repository secrets are set correctly
- Restart the space after adding secrets
- Check logs for API key errors

## Next Steps After Successful Deployment

1. **Test thoroughly** with all 3 concurrent users
2. **Monitor performance** for a few days
3. **Upgrade if needed**: Settings → Change hardware → CPU Upgrade ($25/mo)

## Rollback (if needed)

If something goes wrong:
```bash
# Go back to previous commit
git reset --hard HEAD~1

# Force push to HF
git push huggingface main --force
```

## Questions?

- HF Spaces docs: https://huggingface.co/docs/hub/spaces
- Streamlit docs: https://docs.streamlit.io/
- Your app: https://huggingface.co/spaces/Shefing/aitruism
