# Security Guide - API Key Management

## ⚠️ IMPORTANT: API Key Security

This repository has been configured to prevent API key leaks. Please follow these security guidelines.

## 🔐 How to Set Up API Keys Safely

### 1. **Environment Variables (Recommended)**

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
export PINECONE_API_KEY="your_pinecone_api_key_here"
export SERPAPI_KEY="your_serpapi_key_here"
export PINECONE_ENV="us-east-1"
export PINECONE_INDEX_HOST="your_index_host_url"
```

### 2. **Streamlit Secrets File**

Copy the template and fill in your keys:

```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

Then edit `.streamlit/secrets.toml` with your actual API keys.

### 3. **Using the Check Script**

Copy the template and set environment variables:

```bash
cp check.py.template check.py
export PINECONE_API_KEY="your_pinecone_api_key"
python check.py
```

## 🚫 What NOT to Do

- ❌ **Never commit API keys directly in code**
- ❌ **Never hardcode API keys in Python files**
- ❌ **Never push `.streamlit/secrets.toml` to git**
- ❌ **Never share API keys in public repositories**

## ✅ What TO Do

- ✅ **Use environment variables**
- ✅ **Use `.streamlit/secrets.toml` for local development**
- ✅ **Use template files for documentation**
- ✅ **Keep API keys in secure environment variables**
- ✅ **Rotate API keys regularly**

## 🔧 Files Protected by .gitignore

The following files are excluded from git to prevent API key leaks:

- `.streamlit/secrets.toml` - Contains actual API keys
- `check.py` - Contains hardcoded API keys
- `run_scheduler_with_email.sh` - Contains API keys

## 📝 Template Files

Safe template files are included for reference:

- `.streamlit/secrets.toml.template` - Shows the structure for secrets
- `check.py.template` - Shows how to use environment variables

## 🚨 If You've Already Committed API Keys

If you accidentally committed API keys:

1. **Immediately revoke the exposed API keys**
2. **Generate new API keys**
3. **Update your environment variables**
4. **Use `git filter-branch` to remove from history** (already done for this repo)

## 🔍 Security Monitoring

This repository is monitored by GitGuardian for API key leaks. If a leak is detected:

1. **You'll receive an alert**
2. **The push will be blocked**
3. **Follow the remediation steps provided**

## 📚 Additional Resources

- [GitGuardian Documentation](https://docs.gitguardian.com/)
- [GitHub Security Best Practices](https://docs.github.com/en/github/security)
- [Environment Variables Best Practices](https://12factor.net/config)
