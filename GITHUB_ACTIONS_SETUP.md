# GitHub Actions Setup Guide

This guide explains how to set up the automated test suite with Slack notifications for the AI Agent Guards project.

## Overview

The GitHub Actions workflow automatically runs tests when:
- Code is pushed to the `main` branch
- Pull requests are created targeting the `main` branch

## What Gets Tested

The workflow runs 3 test suites:

1. **test_data_disclosure_fix.py** - Verifies DataDisclosureGuard doesn't flag technical data as PII
2. **test_alignment_fix.py** - Verifies DataDisclosureGuard detects misaligned PII disclosure
3. **test_deviations.py** - Tests temporal deviation and bias detection

## Setup Instructions

### 1. Add Slack Webhook Secret to GitHub

The workflow needs a Slack webhook URL to send notifications.

**Steps:**

1. Go to your GitHub repository settings
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `SLACK_WEBHOOK_URL`
5. Value: `<your-slack-webhook-url>` (the webhook URL you received from Slack)
6. Click **Add secret**

**Note**: Never commit the actual webhook URL to your repository. Always use GitHub Secrets.

### 2. Enable GitHub Actions

If GitHub Actions is not already enabled:

1. Go to **Settings** → **Actions** → **General**
2. Under **Actions permissions**, select **Allow all actions and reusable workflows**
3. Click **Save**

### 3. Verify Workflow File

The workflow file is located at: `.github/workflows/test.yml`

It should be automatically detected by GitHub Actions when you push to the repository.

## Workflow Details

### Trigger Events

- **Push to main**: Runs tests automatically
- **Pull Request to main**: Runs tests before merge

### Test Execution

```yaml
- DataDisclosureGuard false positive test
- DataDisclosureGuard alignment test
- Deviation/bias detection test
```

Each test runs independently and continues even if one fails, so you can see all test results.

### Slack Notifications

#### On Failure ❌

Slack notification includes:
- Repository and branch name
- Commit SHA and author
- Commit message
- Number of tests passed/failed
- List of failed tests
- Links to:
  - Workflow run (to see detailed logs)
  - Commit (to see what changed)

#### On Success ✅

Slack notification includes:
- Repository and branch name
- Commit SHA and author
- Commit message
- Confirmation that all 3 tests passed

## Testing the Workflow

To test if the workflow is working:

1. Make a small change to the README or any file
2. Commit and push to `main`:
   ```bash
   git add .
   git commit -m "Test GitHub Actions workflow"
   git push origin main
   ```
3. Check:
   - GitHub Actions tab for workflow run
   - Slack channel for notification

## Troubleshooting

### Workflow Not Running

**Problem**: No workflow runs appear in the Actions tab

**Solutions:**
- Verify `.github/workflows/test.yml` is committed to the repository
- Check that GitHub Actions is enabled in repository settings
- Ensure you pushed to the `main` branch (not another branch)

### Slack Notifications Not Working

**Problem**: Tests run but no Slack notification appears

**Solutions:**
- Verify `SLACK_WEBHOOK_URL` secret is correctly set in GitHub repository settings
- Test the webhook URL manually:
  ```bash
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Test notification from AI Agent Guards"}' \
    <your-slack-webhook-url>
  ```
- Check Slack webhook is still active (webhooks can expire if not used)

### Test Failures

**Problem**: Tests are failing on GitHub Actions but pass locally

**Solutions:**
- Check the workflow logs for specific error messages
- Dependencies might be missing - verify `requirements_minimal.txt` includes all needed packages
- Environment differences between local and CI:
  - Python version (workflow uses 3.11)
  - Operating system (workflow uses Ubuntu)
  - Missing environment variables (tests don't require API keys)

### Installation Errors

**Problem**: `pip install` step fails

**Solutions:**
- Check for dependency conflicts in workflow logs
- Verify `requirements_minimal.txt` is up to date
- Try installing dependencies in a specific order:
  ```yaml
  pip install -r requirements_minimal.txt
  pip install llamafirewall
  pip install nemoguardrails
  pip install presidio-analyzer presidio-anonymizer
  ```

## Workflow Configuration

### Modifying Test Suite

To add more tests to the workflow:

1. Edit `.github/workflows/test.yml`
2. Add a new step:
   ```yaml
   - name: Run your new test
     id: test_new
     continue-on-error: true
     run: |
       python test_new_file.py
       echo "status=$?" >> $GITHUB_OUTPUT
   ```
3. Update the "Collect test results" step to include the new test

### Changing Notification Format

To modify Slack notification appearance:

1. Edit the `payload` section in `.github/workflows/test.yml`
2. Use [Slack Block Kit Builder](https://api.slack.com/block-kit) to design custom layouts
3. Test changes by making a commit

### Running on Different Branches

To run tests on other branches:

1. Edit `.github/workflows/test.yml`
2. Modify the `on` section:
   ```yaml
   on:
     push:
       branches:
         - main
         - develop
         - feature/*
   ```

## Cost Considerations

- **GitHub Actions**: Free for public repositories, 2000 minutes/month for private repos
- **Workflow Duration**: ~5-10 minutes per run
- **Slack Notifications**: Free (webhooks don't count toward API limits)

## Security Best Practices

✅ **Do:**
- Store Slack webhook URL as a GitHub secret (not in code)
- Use `secrets.SLACK_WEBHOOK_URL` in workflow (never hardcode)
- Limit workflow to run only on necessary branches

❌ **Don't:**
- Commit webhook URLs directly to code
- Share webhook URLs publicly (they allow posting to your Slack)
- Store API keys in workflow file (use secrets)

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Slack Block Kit Builder](https://api.slack.com/block-kit)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
