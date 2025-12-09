# 🚀 Deployment Guide - AI Database Tool

## Quick Deploy to Streamlit Community Cloud (FREE)

### Prerequisites
1. ✅ Code pushed to GitHub
2. ✅ `requirements.txt` exists (already done)
3. ✅ GitHub account

### Step-by-Step Deployment

#### 1. Push to GitHub
```bash
cd '/Users/pallavipriya/Downloads/AI Projects/AI_DB_Tool'
git add .
git commit -m "Ready for cloud deployment"
git push origin main  # or your branch name
```

#### 2. Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click **"New app"**
4. Fill in:
   - **Repository**: Select your `AI_DB_Tool` repo
   - **Branch**: `main` (or your branch)
   - **Main file path**: `webapp/app.py`
5. Click **"Deploy!"**

#### 3. Configure Secrets (Environment Variables)
After deployment, go to **Settings → Secrets** and add:

```toml
# .streamlit/secrets.toml (in Streamlit Cloud settings)
OPENAI_API_KEY = "your-openai-key"
ANTHROPIC_API_KEY = "your-anthropic-key"  # if using Claude

# Database connection strings (optional - users can connect via UI)
# Or leave empty and users connect via the sidebar
```

#### 4. Your App URL
Your app will be live at:
```
https://your-app-name.streamlit.app
```

---

## Alternative: Deploy to Render (FREE)

### 1. Create `Procfile`
Create a file named `Procfile` (no extension) in the root:

```
web: streamlit run webapp/app.py --server.port=$PORT --server.address=0.0.0.0
```

### 2. Deploy on Render
1. Go to https://render.com
2. Sign up (free)
3. **New → Web Service**
4. Connect GitHub repo
5. Settings:
   - **Name**: `ai-database-tool`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run webapp/app.py --server.port=$PORT --server.address=0.0.0.0`
6. Add environment variables (same as Streamlit secrets)
7. Click **"Create Web Service"**

**Note**: Free tier spins down after 15 min inactivity (takes ~30s to wake up)

---

## Alternative: Deploy to Railway (FREE - $5 credit/month)

### 1. Create `Procfile`
Same as Render above.

### 2. Deploy on Railway
1. Go to https://railway.app
2. Sign up with GitHub
3. **New Project → Deploy from GitHub**
4. Select your repo
5. Railway auto-detects Python
6. Add environment variables
7. Deploy!

---

## Important Notes

### ✅ What Works in Cloud
- ✅ Streamlit app
- ✅ Database connections (Neon, Supabase, etc.)
- ✅ AI features (OpenAI/Anthropic)
- ✅ All editor features

### ⚠️ What Needs Adjustment
- ⚠️ **API Server** (`api_server.py`): Needs separate deployment
  - Option 1: Deploy as separate service on Render/Railway
  - Option 2: Integrate autocomplete into main Streamlit app
  - Option 3: Use serverless function (Vercel/Netlify)

### 🔒 Security Best Practices
1. **Never commit secrets** to GitHub
2. Use environment variables for:
   - API keys (OpenAI, Anthropic)
   - Database passwords
   - Any sensitive data
3. Add `.env` to `.gitignore` (if not already)

---

## Troubleshooting

### App won't start
- Check `requirements.txt` has all dependencies
- Verify main file path is correct
- Check logs in deployment dashboard

### Database connection fails
- Ensure database allows connections from cloud IPs
- Check firewall settings
- Verify connection string is correct

### API server not working
- Deploy `api_server.py` as separate service
- Update API URL in Streamlit app settings
- Or integrate autocomplete directly into Streamlit

---

## Recommended: Streamlit Community Cloud
- ✅ Easiest setup
- ✅ Free forever
- ✅ Built for Streamlit
- ✅ Automatic HTTPS
- ✅ No credit card needed
- ✅ Auto-deploys on git push

---

## Next Steps After Deployment

1. Test all features
2. Share URL with team/users
3. Set up custom domain (optional)
4. Monitor usage
5. Set up alerts (if needed)

