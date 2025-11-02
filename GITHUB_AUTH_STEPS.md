# 🔐 GitHub Authentication Steps

## ⚠️ Browser Not Opening? Use Personal Access Token!

Since `gh auth login` isn't opening browser, use a **Personal Access Token** instead:

---

## 🎯 **STEP-BY-STEP:**

### **1. Create Personal Access Token**

**Open this URL in your browser:**
```
https://github.com/settings/tokens
```

**Then:**
1. Click: **"Generate new token"** → **"Generate new token (classic)"**
2. **Token name**: `AI_DB_Tool`
3. **Expiration**: 90 days (or No expiration)
4. **Select scopes**: Check ✅ **`repo`** (all repo permissions)
5. Scroll down and click: **"Generate token"**
6. **COPY THE TOKEN** (you won't see it again! Example: `ghp_xxxxxxxxxxxxxx`)

---

### **2. Use Token to Create Repository**

**Run these commands** (replace `YOUR_TOKEN` with the token you just copied):

```bash
cd /Users/pallavipriya/Downloads/AI\ Projects/AI_DB_Tool

# Create repo using token
gh repo create AI_DB_Tool --public --source=. --remote=origin --push --clone=false <<EOF
YOUR_TOKEN
EOF
```

**OR simpler method:**

```bash
cd /Users/pallavipriya/Downloads/AI\ Projects/AI_DB_Tool

# Set token as environment variable (replace YOUR_TOKEN)
export GH_TOKEN=YOUR_TOKEN

# Create repo
gh repo create AI_DB_Tool --public --source=. --remote=origin --push
```

---

### **3. Alternative: Manual Push Without GitHub CLI**

**If above doesn't work, do this:**

```bash
cd /Users/pallavipriya/Downloads/AI\ Projects/AI_DB_Tool

# First, create the repository on GitHub website
# Go to: https://github.com/new
# Name: AI_DB_Tool
# Click: Create repository

# Then run (replace YOUR_USERNAME):
git remote add origin https://github.com/YOUR_USERNAME/AI_DB_Tool.git

# Push using token as password
git push -u origin master
# When prompted:
# Username: YOUR_GITHUB_USERNAME
# Password: PASTE_YOUR_TOKEN_HERE
```

---

## 🔗 **Quick Links:**

**Create Token:**
```
https://github.com/settings/tokens/new
```

**Create Repository:**
```
https://github.com/new
```

---

## ✅ **Verification:**

After pushing:

```bash
# Check remote
git remote -v

# Should show:
# origin  https://github.com/YOUR_USERNAME/AI_DB_Tool.git (fetch)
# origin  https://github.com/YOUR_USERNAME/AI_DB_Tool.git (push)
```

**Your repo will be live at:**
```
https://github.com/YOUR_USERNAME/AI_DB_Tool
```

---

## 🎯 **Recommended Flow:**

1. **Open:** https://github.com/settings/tokens/new
2. **Generate token** with `repo` scope
3. **Copy token**
4. **Run:**
   ```bash
   export GH_TOKEN=YOUR_TOKEN
   gh repo create AI_DB_Tool --public --source=. --remote=origin --push
   ```

---

**That's it!** Your code will be on GitHub! 🚀

