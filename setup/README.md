# Setup Guide

This directory contains setup scripts for initial configuration.

## 🔐 Gmail Authentication

Run the Gmail authentication script to set up API access:

```bash
python setup/authenticate_gmail.py
```

This script will:

1. Check for `credentials.json` (Gmail API credentials)
2. Open your browser for OAuth authentication
3. Create `token.json` with authentication tokens
4. Test Gmail API access
5. Search for existing PG&E emails

## 📋 Prerequisites

Before running the setup:

1. **Download Gmail API credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials for a desktop application
   - Download as `credentials.json` and place in root directory

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🔧 Configuration

After successful authentication:

1. **Update settings**: Edit `config/settings.json` with your information
2. **Deploy to AWS**: Run `deployment/deploy.sh dev`
3. **Test thoroughly**: Always test in development first

## ⚠️ Important Notes

- The `token.json` file contains sensitive authentication data
- Never commit `credentials.json` or `token.json` to version control
- Both files are needed for AWS deployment
- Re-run authentication if you get OAuth errors

## 🆘 Troubleshooting

**"credentials.json not found"**
- Download OAuth credentials from Google Cloud Console
- Ensure file is named exactly `credentials.json`
- Place in the root directory of this project

**"access_denied" error**
- Make sure your email is added as a test user in Google Cloud Console
- Check that Gmail API is enabled for your project
- Verify OAuth consent screen is configured

**"No PG&E emails found"**
- This is normal if you haven't received any bills yet
- The system will work when bills arrive
- You can test with manual bill data if needed