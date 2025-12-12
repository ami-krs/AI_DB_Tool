# 🚀 Streamlit Cloud Setup Guide

## Setting Up API Keys (Required for AI Features)

Your app will work without API keys for basic database operations, but AI features (chatbot, query generation) require API keys.

### Step 1: Get Your API Keys

#### OpenAI API Key:
1. Go to https://platform.openai.com/api-keys
2. Sign in or create account
3. Click **"Create new secret key"**
4. Name it: "AI Database Tool"
5. Copy the key (starts with `sk-...`)

#### Anthropic API Key (Alternative):
1. Go to https://console.anthropic.com/
2. Sign in or create account
3. Go to **API Keys**
4. Click **"Create Key"**
5. Copy the key

### Step 2: Add Secrets to Streamlit Cloud

1. Go to your Streamlit Cloud app dashboard
2. Click **"Manage app"** (bottom right)
3. Click **"Settings"** (gear icon)
4. Scroll to **"Secrets"** section
5. Click **"Edit secrets"**
6. Add your API key(s):

```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "sk-your-actual-key-here"
# OR
ANTHROPIC_API_KEY = "sk-ant-your-actual-key-here"
```

7. Click **"Save"**
8. Your app will automatically redeploy

### Step 3: Verify It Works

1. Wait for deployment to complete
2. Connect to a database
3. Try the AI Chatbot - it should work now!

---

## What Works Without API Keys

✅ **All Database Operations:**
- Connect to databases
- Execute SQL queries
- Browse tables and schemas
- View data
- Export results
- Use CodeMirror/Monaco editors (without AI autocomplete)

❌ **What Requires API Keys:**
- AI Chatbot
- AI Query Generation
- AI Query Optimization
- AI Query Debugging
- Editor AI Autocomplete (needs API server)

---

## Troubleshooting

### "AI features unavailable" message
- ✅ This is normal if API keys aren't set
- ✅ Database features still work
- Set API keys in Streamlit Cloud secrets to enable AI

### API server not working
- The autocomplete API server (`api_server.py`) needs separate deployment
- Or integrate autocomplete directly into Streamlit app
- For now, editors work without autocomplete

### Component errors
- Make sure component build directories are in git
- Check that `webapp/components/*/build/` files are committed

---

## Security Notes

- ⚠️ **Never commit API keys to GitHub**
- ✅ Use Streamlit Cloud secrets (encrypted)
- ✅ Keys are only accessible to your app
- ✅ You can rotate keys anytime

---

## Cost Considerations

### OpenAI:
- GPT-4o: ~$0.01-0.03 per query
- GPT-4o-mini: ~$0.001-0.003 per query (cheaper)
- Free tier: $5 credit for new accounts

### Anthropic:
- Claude 3.5 Sonnet: Similar pricing
- Check current rates on their website

**Tip:** Start with GPT-4o-mini for cost-effective testing!

