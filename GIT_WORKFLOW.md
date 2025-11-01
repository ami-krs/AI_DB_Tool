# 🔄 Git Workflow Guide

## Current Branch Structure

```
master    ← Production-ready code (stable)
develop   ← Development branch (current active branch)
```

---

## 📍 Current Status

**Active Branch:** `develop`  
**Status:** Repository initialized with initial commit

---

## 🚀 Common Git Workflows

### 1. **Creating a New Feature Branch**

```bash
# Make sure you're on develop
git checkout develop

# Create and switch to a new feature branch
git checkout -b feature/your-feature-name

# Example: Add authentication
git checkout -b feature/authentication

# Example: Add advanced visualizations
git checkout -b feature/visualizations

# Example: Fix a bug
git checkout -b fix/table-display-issue
```

### 2. **Making Changes and Committing**

```bash
# After making your changes
git add .

# Or add specific files
git add webapp/app.py

# Commit with descriptive message
git commit -m "Add authentication system with JWT tokens"

# Multiple line commit message
git commit -m "Add authentication system

- Implement JWT token generation
- Add login/logout endpoints
- Secure credential storage
"
```

### 3. **Pushing Changes to Remote**

```bash
# First time pushing a new branch
git push -u origin develop

# Subsequent pushes
git push

# Push to specific branch
git push origin feature/authentication
```

### 4. **Merging Features Back to Develop**

```bash
# Switch to develop
git checkout develop

# Pull latest changes
git pull origin develop

# Merge your feature branch
git merge feature/authentication

# Push merged changes
git push origin develop
```

### 5. **Creating Pull Request (If using GitHub/GitLab)**

```bash
# Push your feature branch
git push -u origin feature/authentication

# Then create PR via web interface
# GitHub: github.com/your-repo/compare/develop...feature/authentication
```

---

## 🌿 Branch Naming Conventions

Follow these patterns for branch names:

- **Features**: `feature/short-description`
  - `feature/authentication`
  - `feature/dark-mode`
  - `feature/query-templates`

- **Fixes**: `fix/issue-description`
  - `fix/table-width-display`
  - `fix/connection-timeout`
  - `fix/export-csv-error`

- **Hotfixes**: `hotfix/urgent-fix`
  - `hotfix/security-patch`
  - `hotfix/api-key-leak`

- **Documentation**: `docs/what-you-changed`
  - `docs/api-reference`
  - `docs/installation-guide`

---

## 📋 Development Workflow Example

### Scenario: Adding Dark Mode

```bash
# 1. Start from develop
git checkout develop

# 2. Pull latest changes
git pull origin develop

# 3. Create feature branch
git checkout -b feature/dark-mode

# 4. Make your changes
# Edit webapp/app.py, add dark mode functionality

# 5. Stage changes
git add webapp/app.py

# 6. Commit
git commit -m "Add dark mode toggle to UI"

# 7. Test your changes locally
streamlit run webapp/app.py

# 8. Push to remote
git push -u origin feature/dark-mode

# 9. Create Pull Request on GitHub/GitLab

# 10. After PR is approved, merge to develop
git checkout develop
git merge feature/dark-mode
git push origin develop

# 11. Delete local feature branch
git branch -d feature/dark-mode
```

---

## 🔄 Switching Between Branches

```bash
# List all branches
git branch

# List all branches (including remote)
git branch -a

# Switch to a branch
git checkout branch-name

# Switch back to previous branch
git checkout -

# New way (Git 2.23+)
git switch branch-name
```

---

## 📊 Viewing History and Changes

```bash
# View commit history
git log

# View commit history (compact)
git log --oneline

# View changes made
git diff

# View staged changes
git diff --staged

# View file history
git log --follow webapp/app.py

# View what changed in a commit
git show <commit-hash>
```

---

## 🗂️ Undoing Changes

```bash
# Unstage a file (keep changes)
git restore --staged filename

# Discard changes in a file
git restore filename

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard last commit completely
git reset --hard HEAD~1

# Revert a specific commit (creates new commit)
git revert <commit-hash>
```

---

## 🔀 Syncing with Remote

```bash
# Fetch latest from remote (no merge)
git fetch origin

# Pull latest and merge
git pull origin develop

# Pull and rebase
git pull --rebase origin develop

# See what's different
git fetch origin
git diff develop origin/develop
```

---

## 🏷️ Tagging Versions

```bash
# Create a version tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# List tags
git tag

# Push tags to remote
git push origin v1.0.0

# Push all tags
git push origin --tags

# Delete a tag
git tag -d v1.0.0
git push origin --delete v1.0.0
```

---

## 🚨 Handling Conflicts

```bash
# If merge conflicts occur
git status  # See which files have conflicts

# Edit the conflicted files, look for:
# <<<<<<< HEAD
# your changes
# =======
# their changes
# >>>>>>> branch-name

# After resolving conflicts
git add <resolved-file>
git commit -m "Merge branch 'feature/xyz' into develop"
```

---

## 📝 Best Practices

### Commit Messages
- ✅ **Good**: "Add user authentication with OAuth2"
- ❌ **Bad**: "updates"

### Keep Commits Focused
- ✅ **Good**: One feature per commit
- ❌ **Bad**: "Added 5 features and fixed 3 bugs"

### Commit Frequently
- ✅ Make small, frequent commits
- ❌ Don't wait days to commit

### Use Descriptive Branches
- ✅ `feature/advanced-visualizations`
- ❌ `my-branch`, `test`, `stuff`

### Keep Develop Updated
- ✅ Regularly merge/pull from develop
- ❌ Don't let feature branches get too old

---

## 🔐 Setting Up GitHub/GitLab

### First Time Setup

```bash
# Add remote repository
git remote add origin https://github.com/yourusername/AI_DB_Tool.git

# Verify remote
git remote -v

# Push to remote
git push -u origin master

# Push develop branch
git checkout develop
git push -u origin develop
```

---

## 📚 Quick Reference

```bash
# Status
git status              # Current status
git log --oneline       # Recent commits

# Common actions
git add .               # Stage all changes
git commit -m "msg"     # Commit changes
git push                # Push to remote

# Branching
git branch              # List branches
git checkout -b name    # Create and switch
git merge branch        # Merge branch

# Undo
git restore file        # Discard changes
git reset HEAD~1        # Undo commit
```

---

## 🎯 Recommended Workflow for AI Database Tool

### **For New Features:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-new-feature
# Make changes, commit
git push -u origin feature/my-new-feature
# Create PR, merge, delete branch
```

### **For Bug Fixes:**
```bash
git checkout develop
git pull origin develop
git checkout -b fix/bug-description
# Fix the bug, commit
git push -u origin fix/bug-description
# Create PR, merge, delete branch
```

### **For Production Release:**
```bash
git checkout master
git pull origin master
git merge develop
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin master
git push origin v1.0.0
```

---

## 🆘 Need Help?

```bash
# Get help for any command
git help <command>

# Examples
git help commit
git help merge
git help branch
```

---

**Current Repository State:**
- ✅ Git initialized
- ✅ Initial commit completed
- ✅ .gitignore configured
- ✅ Currently on `develop` branch
- ⏭️ Ready to add remote repository (GitHub/GitLab)

**Next Steps:**
1. Create GitHub/GitLab repository
2. Add remote: `git remote add origin <url>`
3. Push: `git push -u origin develop`
4. Start adding features!

