# Push/Pull Procedure for ClonePerfin

## Overview
This repository has a special configuration to keep the local database (`finance_tracker.db`) persistent while allowing code changes to sync with GitHub.

## Initial Setup (Already Completed)
```bash
# Configure git to skip database changes
git update-index --skip-worktree finance_tracker.db
```

## Push Procedure
When pushing code changes to GitHub:

```bash
# Check status (database should not show as modified)
git status

# Add your code changes
git add .

# Commit changes
git commit -m "Your commit message"

# Push to GitHub
git push origin main
```

## Pull Procedure
When pulling code changes from GitHub:

```bash
# Pull latest code changes
git pull origin main
```

**Note:** The database file (`finance_tracker.db`) will remain untouched and maintain your local data.

## Working with Branches
For testing new features:

```bash
# Create and switch to development branch
git checkout -b development

# Make changes and commit
git add .
git commit -m "Feature changes"

# Switch back to main
git checkout main

# Merge development branch (database stays local)
git merge development

# Push merged changes
git push origin main

# Clean up branch (optional)
git branch -d development
```

## Important Notes
- The database file is configured to be skipped during git operations
- Your personal finance data stays local and private
- Only code changes sync with GitHub
- If you ever need to include database changes, run: `git update-index --no-skip-worktree finance_tracker.db`

## Repository Structure
- **Code files**: Synced with GitHub (app.py, templates/, static/, etc.)
- **Database**: Local only (`finance_tracker.db`)
- **Configuration**: This procedure document