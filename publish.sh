#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOY_DIR="/tmp/quartz-deploy"

echo "==> Copying published notes from vault..."
python3 "$REPO_DIR/scripts/copy_published.py"

echo "==> Building Quartz..."
cd "$REPO_DIR"
npx quartz build

echo "==> Deploying to gh-pages..."
if [ ! -d "$DEPLOY_DIR" ]; then
    git worktree add "$DEPLOY_DIR" gh-pages
fi

rsync -av --delete --exclude='.git' "$REPO_DIR/public/" "$DEPLOY_DIR/"

cd "$DEPLOY_DIR"
git add --all
git commit -m "Deploy $(date +%Y-%m-%d-%H%M)" || echo "Nothing to commit."
git push origin gh-pages

cd "$REPO_DIR"
echo "==> Done! Site: https://terryberk.github.io/knowledge-garden/"
