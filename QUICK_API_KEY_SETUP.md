# 🔑 Quick API Key Setup Guide

## For Streamlit Cloud Deployment

### Step 1: Get Your OpenAI API Key

1. Go to: **https://platform.openai.com/api-keys**
2. Sign in (or create account)
3. Click **"Create new secret key"**
4. Name it: "AI Database Tool"
5. **Copy the key** (starts with `sk-...`)
   - ⚠️ You won't see it again, so copy it now!

### Step 2: Add to Streamlit Cloud

1. Go to your Streamlit Cloud app: **https://share.streamlit.io**
2. Click on your app
3. Click **"Manage app"** (bottom right, gear icon)
4. Click **"Settings"** (in the menu)
5. Scroll down to **"Secrets"** section
6. Click **"Edit secrets"**
7. Paste this (replace with your actual key):

```toml
OPENAI_API_KEY = "sk-your-actual-key-here"
```

8. Click **"Save"**
9. Your app will automatically redeploy (takes ~1-2 minutes)

### Step 3: Verify

1. Wait for deployment to complete
2. Refresh your app
3. Connect to a database
4. The AI Chatbot should now work! ✅

---

## Alternative: Use Anthropic (Claude)

If you prefer Claude instead of OpenAI:

1. Go to: **https://console.anthropic.com/**
2. Get your API key
3. In Streamlit Cloud secrets, use:

```toml
ANTHROPIC_API_KEY = "sk-ant-your-actual-key-here"
```

---

## For Local Development

If running locally, create a `.streamlit/secrets.toml` file:

```toml
OPENAI_API_KEY = "sk-your-actual-key-here"
```

Or set environment variable:

```bash
export OPENAI_API_KEY="sk-your-actual-key-here"
streamlit run webapp/app.py
```

---

## Cost Information

### OpenAI (Recommended):
- **GPT-4o-mini**: ~$0.001-0.003 per query (very cheap)
- **GPT-4o**: ~$0.01-0.03 per query (more capable)
- **Free tier**: $5 credit for new accounts

### Anthropic:
- Similar pricing to OpenAI
- Check current rates on their website

**Tip**: Start with GPT-4o-mini for cost-effective testing!

---

## What Works Without API Keys

✅ **All Database Features Work:**
- Connect to databases
- Execute SQL queries
- Browse tables and schemas
- View and export data
- Use CodeMirror/Monaco editors (without AI autocomplete)

❌ **Requires API Keys:**
- AI Chatbot
- AI Query Generation
- AI Query Optimization
- AI Query Debugging

---

## Troubleshooting

### "AI features are disabled" still showing?
- ✅ Wait 1-2 minutes for redeployment
- ✅ Refresh the page
- ✅ Check that key starts with `sk-` (OpenAI) or `sk-ant-` (Anthropic)
- ✅ Make sure there are no extra spaces in the secret

### Key not working?
- Check the key is correct (no typos)
- Verify the key hasn't expired
- Make sure you have credits/quota available

