# Git Worktree Strategy

Git worktrees allow you to work on multiple feature branches simultaneously without stashing or switching branches.

## Why Use Worktrees?

- Work on multiple PRs in parallel
- Keep development environments isolated
- No need to stash changes or switch branches
- Run separate dev servers, tests, or builds for each branch
- Main worktree stays on master for quick reference

## Setup Worktree for New Feature

```bash
# Create worktree for new feature branch
git worktree add ../stupid_chat_bot-feature-name -b feature-name

# Navigate to worktree
cd ../stupid_chat_bot-feature-name

# Verify you're on the new branch
git branch --show-current
```

## Working with Worktrees

Each worktree is completely independent:
- Has its own working directory
- Can run separate dev servers on different ports
- Changes don't affect other worktrees
- Can commit and push independently

```bash
# In first worktree (e.g., feature-auth)
cd ../stupid_chat_bot-feature-auth
npm run dev  # Runs on port 5173

# In second worktree (e.g., feature-ui)
cd ../stupid_chat_bot-feature-ui
npm run dev -- --port 5174  # Runs on different port
```

## List All Worktrees

```bash
# See all active worktrees
git worktree list

# Example output:
# /Users/user/work/study/stupid_chat_bot        d368f36 [master]
# /Users/user/work/study/stupid_chat_bot-auth   a1b2c3d [feature-auth]
# /Users/user/work/study/stupid_chat_bot-ui     e4f5g6h [feature-ui]
```

## Cleanup After PR Merge

```bash
# Remove worktree (do this from any worktree or main repo)
git worktree remove ../stupid_chat_bot-feature-name

# Delete the merged branch
git branch -d feature-name

# If branch was deleted on remote, prune local references
git fetch --prune
```

## Best Practices

- **Naming Convention**: Use consistent naming like `../project-name-branch-name`
- **Directory Organization**: Keep worktrees in the same parent directory as main repo
- **Branch Naming**: Match worktree folder name to branch name for clarity
- **Cleanup Promptly**: Remove worktrees after PR is merged to avoid clutter
- **Main Worktree**: Keep the main worktree on master branch for quick checks and updates
- **Documentation**: When creating worktrees, document active ones if working on long-term features

## Common Workflows

### Creating PR from Worktree

```bash
# Create and navigate to worktree
git worktree add ../stupid_chat_bot-issue-123 -b claude/issue-123-feature-name
cd ../stupid_chat_bot-issue-123

# Make changes, commit, and push
git add .
git commit -m "feat: implement feature XYZ"
git push -u origin claude/issue-123-feature-name

# Create PR
gh pr create --title "Feature: XYZ" --body "Implements feature for issue #123"
```

### Addressing PR Comments in Worktree

```bash
# Already in the worktree for the PR
cd ../stupid_chat_bot-issue-123

# Read PR comments
gh pr view 123

# Make changes, commit individually per comment
git add path/to/file.py
git commit -m "fix: address PR comment about error handling"

git add path/to/other.py
git commit -m "fix: add missing type hints per review"

# Push changes
git push

# Reply to comments
gh pr review 123 --comment --body "Fixed error handling and added type hints"
```
