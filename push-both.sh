#!/bin/bash

# Script to push changes to both GitHub and GitLab
# Usage: ./push-both.sh "commit message"

if [ -z "$1" ]; then
    echo "Usage: ./push-both.sh \"commit message\""
    exit 1
fi

COMMIT_MESSAGE="$1"

echo "🔄 Adding changes..."
git add .

echo "📝 Committing changes..."
git commit -m "$COMMIT_MESSAGE"

echo "🚀 Pushing to GitHub..."
git push origin main

echo "🦊 Pushing to GitLab..."
git push gitlab main

echo "✅ Successfully pushed to both GitHub and GitLab!"
echo "🔗 GitLab pipeline should trigger automatically."
