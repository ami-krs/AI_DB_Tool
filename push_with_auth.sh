#!/bin/bash
# Helper script to push with GitHub authentication

cd '/Users/pallavipriya/Downloads/AI Projects/AI_DB_Tool'

echo "🔐 GitHub Push Authentication Helper"
echo "====================================="
echo ""
echo "You need a Personal Access Token (PAT) to push."
echo ""
echo "If you don't have one yet:"
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Generate new token (classic)"
echo "3. Check 'repo' scope"
echo "4. Copy the token"
echo ""
read -p "Do you have a PAT token ready? (y/n): " has_token

if [ "$has_token" != "y" ]; then
    echo ""
    echo "Please create a token first, then run this script again."
    exit 1
fi

echo ""
read -sp "Enter your GitHub username (ami-krs): " username
echo ""
read -sp "Enter your Personal Access Token: " token
echo ""

# Method 1: Try with GIT_ASKPASS
export GIT_ASKPASS=echo
export GIT_TERMINAL_PROMPT=1

# Update remote with token
git remote set-url origin "https://${username}:${token}@github.com/ami-krs/AI_DB_Tool.git"

echo ""
echo "✅ Remote URL updated with token"
echo "🚀 Pushing to develop branch..."
echo ""

git push origin develop

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "⚠️  Note: Your token is stored in the remote URL."
    echo "   For better security, consider using SSH keys instead."
else
    echo ""
    echo "❌ Push failed. Please check:"
    echo "   1. Token has 'repo' scope"
    echo "   2. Token hasn't expired"
    echo "   3. You have push access to the repository"
fi

