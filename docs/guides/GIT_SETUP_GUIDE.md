# Git Setup Guide for CoinPulse
**Purpose**: Initialize version control to prevent feature loss
**Priority**: HIGH - Do this IMMEDIATELY
**Time Required**: 5 minutes

---

## Why Git is Critical

**Without Git**:
- ❌ Can't track what changed
- ❌ Can't see who deleted code
- ❌ Can't rollback mistakes
- ❌ Can't see history of changes

**With Git**:
- ✅ Every change tracked
- ✅ Can rollback any mistake
- ✅ Can see what was deleted and when
- ✅ Safe to experiment (can always undo)

---

## Step 1: Initialize Git Repository

```bash
# Navigate to project directory
cd "D:\Claude\Projects\Active\코인펄스"

# Initialize Git
git init

# Result: Initialized empty Git repository in D:/Claude/Projects/Active/코인펄스/.git/
```

---

## Step 2: Create .gitignore File

Create a file named `.gitignore` in the project root to exclude unnecessary files:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/
dist/
build/

# Logs
*.log
logs/

# API Keys and Secrets
*.env
*_keys.json
secrets.json
upbit_keys.txt

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
desktop.ini

# Backup files
*.backup
*.bak
*_backup_*

# Test data
test_data/
temp/
```

---

## Step 3: Create Initial Commit

```bash
# Add all files to staging
git add .

# Create first commit with baseline
git commit -m "Initial commit - Baseline before feature fixes

- Chart server on port 8080
- Trading server on port 8081
- MA toggle working
- Support/Resistance NOT implemented
- Avg price/pending orders code exists but not displaying
- Feature registry created
"

# Result: [main (root-commit) abc123] Initial commit - Baseline before feature fixes
```

---

## Step 4: Create Branch for Bug Fixes

```bash
# Create branch for debugging avg price issue
git checkout -b bugfix/avg-price-lines

# Now you're on the bugfix branch
# Any changes made here won't affect main branch until merged
```

---

## Step 5: Make Changes and Commit

```bash
# After making code changes:
git add frontend/js/trading_chart_working.js

# Commit with descriptive message
git commit -m "Fix: Average price line now displays correctly

- Issue: Line not showing despite code being implemented
- Root cause: API server on port 8081 was not running
- Fix: Added server status check and error handling
- Verified: Line now shows gold (#FFD700) on chart
- Updated: FEATURE_REGISTRY.md status to Working
"
```

---

## Step 6: Merge Back to Main

```bash
# Switch back to main branch
git checkout main

# Merge the fix
git merge bugfix/avg-price-lines

# Result: Fast-forward merge (your changes now in main)
```

---

## Common Git Commands

### View Status
```bash
git status
# Shows what files are changed, staged, or untracked
```

### View History
```bash
git log
# Shows all commits with messages

git log --oneline
# Shows compact history
```

### See What Changed
```bash
git diff
# Shows unstaged changes

git diff --staged
# Shows staged changes
```

### Undo Changes
```bash
# Undo changes to a file (before commit)
git checkout -- filename.js

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - CAREFUL!
git reset --hard HEAD~1
```

### View File at Previous Commit
```bash
git show HEAD:frontend/js/trading_chart_working.js
# Shows file contents from last commit
```

### Search for Deleted Code
```bash
# Find when a function was deleted
git log -S "toggleSupportResistance" --source --all

# Show commits that changed a specific file
git log -- frontend/js/trading_chart_working.js
```

---

## Workflow for Feature Development

### 1. Before Starting Work
```bash
# Make sure you're on main and up to date
git checkout main
git status
```

### 2. Create Feature Branch
```bash
# Create branch for new feature
git checkout -b feature/support-resistance

# Now you can work without affecting main
```

### 3. Make Changes and Test
```bash
# Write code
# Test in browser
# Verify it works
```

### 4. Commit Frequently
```bash
# Commit after each logical change
git add .
git commit -m "Add toggleSupportResistance function"

# Continue working
git add .
git commit -m "Add drawSupportResistance function"

# Continue working
git add .
git commit -m "Add event listener for S/R toggle button"
```

### 5. Verify Feature Complete
```bash
# Check FEATURE_REGISTRY.md verification checklist
# Run browser tests
# Update documentation
```

### 6. Merge to Main
```bash
git checkout main
git merge feature/support-resistance

# Update FEATURE_REGISTRY.md
git add FEATURE_REGISTRY.md
git commit -m "Update feature registry - Support/Resistance now working"
```

---

## Protecting Against Feature Loss

### Daily Commit Habit
```bash
# At end of each coding session:
git add .
git commit -m "End of day commit - [brief description of what you worked on]"

# This way you never lose more than 1 day of work
```

### Before Making Risky Changes
```bash
# Create a backup branch
git branch backup-before-refactor

# Now make your risky changes
# If something breaks, you can:
git checkout backup-before-refactor
```

### Tag Important Milestones
```bash
# When a major feature is complete:
git tag -a v1.0-ma-toggle -m "MA toggle fully working"
git tag -a v1.1-support-resistance -m "Support/Resistance implemented"

# View all tags:
git tag
```

---

## Debugging with Git

### Find When Something Broke
```bash
# Binary search through commits to find when bug was introduced
git bisect start
git bisect bad  # Current version is broken
git bisect good abc123  # This old commit was good

# Git will checkout middle commit
# Test it, then tell Git:
git bisect good  # or git bisect bad

# Repeat until Git finds the breaking commit
```

### See Who Changed What
```bash
# See who last modified each line
git blame frontend/js/trading_chart_working.js

# See specific line range
git blame -L 2327,2427 frontend/js/trading_chart_working.js
```

### Compare Branches
```bash
# See what's different between branches
git diff main..feature/support-resistance

# See which files differ
git diff --name-only main..feature/support-resistance
```

---

## Integration with FEATURE_REGISTRY.md

### After Every Feature Change:

1. **Update code**
2. **Test in browser**
3. **Update FEATURE_REGISTRY.md**
4. **Commit all together**:

```bash
git add frontend/js/trading_chart_working.js
git add FEATURE_REGISTRY.md
git commit -m "Implement Support/Resistance toggle

Feature: Support/Resistance Lines
Status: ✅ Working (verified in browser)
Files:
  - trading_chart_working.js Lines 2100-2250
  - Event listener added Line 1360
Test: document.getElementById('support-resistance-toggle').click()
Verified: 2025-10-17

Updated FEATURE_REGISTRY.md with implementation details
"
```

This way, code and documentation are ALWAYS in sync!

---

## Git with Remote Repository (Optional but Recommended)

### Setup GitHub
```bash
# Create repository on GitHub
# Then link it:
git remote add origin https://github.com/yourusername/coinpulse.git

# Push your code
git push -u origin main
```

### Benefits of Remote Repository:
- ✅ Backup in the cloud
- ✅ Access from multiple computers
- ✅ Share with collaborators
- ✅ Free private repositories

---

## Quick Reference Card

```bash
# Start work
git status                          # Check current state
git checkout -b feature/new-thing   # Create branch

# During work
git add .                           # Stage changes
git commit -m "message"             # Commit changes

# After work
git checkout main                   # Go back to main
git merge feature/new-thing         # Merge changes
git branch -d feature/new-thing     # Delete branch (optional)

# View history
git log --oneline                   # See commits
git diff                            # See changes

# Undo mistakes
git checkout -- file.js             # Undo file changes
git reset --soft HEAD~1             # Undo last commit
```

---

## Next Steps

1. **Right now**: Run Step 1-3 to create initial commit
2. **Before any changes**: Create feature branch
3. **After each change**: Commit with descriptive message
4. **Daily habit**: Commit at end of each session
5. **Weekly audit**: Check git log to see all changes made

---

**Remember**: Git is your safety net. Commit often, write clear messages, and you'll never lose work again!

**Status**: ✅ Ready to Use
**Priority**: HIGH
**Time to Setup**: 5 minutes
**Value**: Prevents all future feature loss
