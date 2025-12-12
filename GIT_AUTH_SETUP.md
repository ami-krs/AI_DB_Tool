# 🔐 Git Authentication Setup for GitHub

## Quick Fix: Use Personal Access Token (PAT)

### Step 1: Create Personal Access Token
1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. **Note**: "AI_DB_Tool Push"
4. **Expiration**: 90 days (or your choice)
5. **Scopes**: Check ✅ **`repo`** (full control)
6. Click **"Generate token"**
7. **COPY THE TOKEN** - you won't see it again!

### Step 2: Update Remote URL with Token

**Option A: Update remote URL (token stored in URL - less secure but convenient)**
```bash
cd '/Users/pallavipriya/Downloads/AI Projects/AI_DB_Tool'
git remote set-url origin https://YOUR_TOKEN@github.com/ami-krs/AI_DB_Tool.git
git push origin develop
```

**Option B: Use token as password (more secure - token not stored)**
```bash
cd '/Users/pallavipriya/Downloads/AI Projects/AI_DB_Tool'
git push origin develop
# When prompted:
# Username: ami-krs
# Password: [paste your PAT token here]
```

**Option C: Use SSH (most secure - recommended for long-term)**
```bash
# 1. Check if you have SSH key
ls -la ~/.ssh/id_*.pub

# 2. If no key, generate one
ssh-keygen -t ed25519 -C "ami.krs@gmail.com"
# Press Enter to accept default location
# Press Enter for no passphrase (or set one)

# 3. Copy public key
cat ~/.ssh/id_ed25519.pub
# Copy the output

# 4. Add to GitHub: https://github.com/settings/keys
# Click "New SSH key", paste the key

# 5. Test connection
ssh -T git@github.com

# 6. Update remote to use SSH
git remote set-url origin git@github.com:ami-krs/AI_DB_Tool.git

# 7. Push
git push origin develop
```

---

## Recommended: Option B (Token as Password)

This is the most secure approach - the token is stored in macOS Keychain, not in the repo URL.

1. Create PAT (see Step 1 above)
2. Run: `git push origin develop`
3. When prompted:
   - **Username**: `ami-krs`
   - **Password**: Paste your PAT token (not your GitHub password!)
4. macOS Keychain will remember it

---

## Troubleshooting

### If still getting authentication errors:
```bash
# Clear all cached credentials
git credential-osxkeychain erase <<EOF
host=github.com
protocol=https
EOF

# Try push again
git push origin develop
```

### If token expires:
- Create a new token
- Update credentials in Keychain Access app, or
- Use Option A to update remote URL with new token

---

## Security Notes

- ⚠️ **Never commit tokens to your repository**
- ✅ Tokens stored in macOS Keychain are encrypted
- ✅ SSH keys are the most secure long-term solution
- ✅ PAT tokens can be revoked anytime from GitHub settings

