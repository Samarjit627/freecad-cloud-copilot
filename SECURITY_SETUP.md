# 🔐 Security Setup Guide

## 📋 Environment Configuration

This project uses environment variables to securely manage API keys and sensitive configuration data.

### 🚀 Quick Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual API keys:**
   ```bash
   nano .env
   ```

3. **Add your Anthropic API key:**
   - Get your API key from: https://console.anthropic.com/
   - Replace `your_anthropic_api_key_here` with your actual key

### 🔑 Required API Keys

#### Anthropic API Key
- **Purpose:** Powers the cloud backend AI analysis
- **Where to get:** https://console.anthropic.com/
- **Environment variable:** `ANTHROPIC_API_KEY`

### 🛡️ Security Best Practices

✅ **DO:**
- Keep your `.env` file private and never commit it to version control
- Use environment variables for all sensitive data
- Regularly rotate your API keys
- Use different keys for development and production

❌ **DON'T:**
- Hardcode API keys in source code
- Share your `.env` file or API keys
- Commit secrets to Git repositories
- Use production keys in development

### 🔧 Configuration Files

- **`.env`** - Your private environment variables (never committed)
- **`.env.example`** - Template for environment setup (safe to commit)
- **`cloud_config.json`** - Uses environment variable references
- **`.gitignore`** - Prevents accidental commits of secrets

### 🚨 If You Accidentally Commit Secrets

1. **Immediately revoke the exposed API key**
2. **Generate a new API key**
3. **Remove the secret from Git history:**
   ```bash
   git filter-branch --force --index-filter \
   'git rm --cached --ignore-unmatch path/to/file/with/secret' \
   --prune-empty --tag-name-filter cat -- --all
   ```
4. **Force push to update remote repository**

### 📞 Support

If you need help with security setup, please refer to:
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
