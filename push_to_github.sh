#!/bin/bash
# Script to push code to GitHub for Streamlit Cloud deployment

echo "🚀 Preparing to push to GitHub..."
echo ""

cd "$(dirname "$0")"

# Check if we're on the right branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Show commits ready to push
echo ""
echo "📦 Commits ready to push:"
git log origin/$CURRENT_BRANCH..HEAD --oneline

echo ""
echo "📁 Files changed:"
git diff --stat origin/$CURRENT_BRANCH..HEAD

echo ""
read -p "Do you want to push to GitHub? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Pushing to GitHub..."
    
    # Try push
    if git push origin $CURRENT_BRANCH; then
        echo ""
        echo "✅ Successfully pushed to GitHub!"
        echo ""
        echo "📡 Streamlit Cloud will automatically detect the changes and redeploy."
        echo "   Check your Streamlit Cloud dashboard for deployment status."
        echo ""
        echo "🔗 To manually restart the app:"
        echo "   1. Go to https://share.streamlit.io/"
        echo "   2. Find your app"
        echo "   3. Click '⋮' (three dots) → 'Reboot app'"
    else
        echo ""
        echo "❌ Push failed. This might be due to authentication."
        echo ""
        echo "💡 Try one of these options:"
        echo "   1. Use GitHub Desktop or Git GUI to push"
        echo "   2. Update your GitHub token in the remote URL:"
        echo "      git remote set-url origin https://YOUR_TOKEN@github.com/ami-krs/AI_DB_Tool.git"
        echo "   3. Use SSH instead:"
        echo "      git remote set-url origin git@github.com:ami-krs/AI_DB_Tool.git"
    fi
else
    echo "❌ Push cancelled."
fi
