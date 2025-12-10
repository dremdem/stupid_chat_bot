# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the "Stupid Chat Bot" - a simple, straightforward AI-powered chat application. The project demonstrates a clean implementation of a modern chat bot using FastAPI for the backend and React for the frontend.

## Tech Stack

- **Backend**: FastAPI (Python 3.12)
  - WebSocket support for real-time messaging
  - AI integration with streaming responses
  - RESTful API design

- **Frontend**: [React](https://react.dev/) with [Vite](https://vite.dev/)
  - Modern [hooks](https://react.dev/reference/react/hooks)-based components (Hooks are functions that let you use state and other React features without writing classes)
  - Real-time WebSocket communication
  - Rich markdown and code rendering

- **AI Integration**: LiteLLM - Universal LLM library supporting multiple providers
  - Supports: Anthropic, OpenAI, Google, Meta, DeepSeek
  - Provider switching via environment variables
  - Streaming support for real-time responses

## Development Commands

### Backend

#### Automated Setup (Recommended for First Time)
```bash
cd backend
# Make scripts executable (one-time setup after cloning)
chmod +x setup_local_env.sh activate_env.sh cleanup_env.sh

# Run automated setup
./setup_local_env.sh

# Activate the environment
source ./activate_env.sh

# Run development server
invoke dev
```

#### Manual Setup
```bash
cd backend
uv sync
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Docker (Recommended for local development)
```bash
docker compose up --build
```

This will start both backend and frontend services:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## Dependency Management

### Backend Dependencies

The backend uses `uv` with `pyproject.toml` + `uv.lock` for reproducible dependency management.

#### File Structure
- `pyproject.toml` - Project metadata and dependency specifications
- `uv.lock` - Lock file with exact versions and SHA256 hashes (DO NOT edit manually)
- `requirements.txt` - Legacy file (kept for reference, may be removed)
- `requirements-dev.txt` - Legacy file (kept for reference, may be removed)

#### Installing Dependencies

**Local development**:
```bash
cd backend
# Install production dependencies
uv sync

# Install with dev dependencies
uv sync --all-extras
```

**Docker development** (recommended):
```bash
docker compose up --build
```

#### Adding Dependencies

**Production dependency**:
```bash
cd backend
uv add <package-name>

# Or manually edit pyproject.toml [project.dependencies], then:
uv lock

# Rebuild Docker image
docker compose build backend
```

**Development dependency**:
```bash
cd backend
uv add --dev <package-name>

# Or manually edit pyproject.toml [project.optional-dependencies.dev], then:
uv lock
```

#### Updating Dependencies

```bash
cd backend
# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package <package-name>

# Rebuild Docker image
docker compose build backend
```

#### Verifying Lock File

```bash
cd backend
# Check if lock file is up to date with pyproject.toml
uv lock --check
```

This command is useful in CI/CD to ensure the lock file hasn't drifted from the project configuration.

### Linting and Formatting

#### Backend
```bash
cd backend
# Format code with black
black .

# Check with ruff
ruff check .
```

#### Frontend
```bash
cd frontend
# Lint with ESLint
npm run lint

# Format with Prettier
npx prettier --write .
```

### Pre-commit Hooks

Pre-commit hooks are configured to automatically check code quality before commits.

#### Setup
```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the git hook scripts
pre-commit install

# (Optional) Run against all files
pre-commit run --all-files
```

#### What's Checked
- **Backend**: Black formatting, Ruff linting
- **Frontend**: ESLint, Prettier formatting
- **Security**: Gitleaks secret detection, private key detection
- **General**: Trailing whitespace, file sizes, YAML validation, merge conflicts

The pre-commit hooks will automatically run when you commit. If any check fails, the commit will be blocked until you fix the issues.

## Architecture

### High-Level Design
- **Frontend**: React SPA connecting via WebSocket
- **Backend**: FastAPI server handling WebSocket connections and AI proxy
- **AI Service**: External LLM API for chat responses
- **Storage**: Database for chat history (to be implemented in Phase 5)

### Key Components
- WebSocket Manager for real-time bidirectional communication
- Chat Service for message processing
- AI Client with streaming support
- Message persistence layer
- Rich UI with animations and markdown rendering

See [README.md](./README.md) for detailed architecture diagrams and component descriptions.

## Implementation Status

The project is currently in **Phase 3** (AI Integration - Complete). See README.md for the complete 7-phase implementation roadmap.

### Completed Phases
- **Phase 0**: Documentation Phase ✓
- **Phase 1**: Foundation Setup ✓
  - Backend structure with FastAPI
  - Frontend structure with React + Vite
  - Docker setup
  - Linting and formatting configuration

- **Phase 1.5**: Code Quality & CI ✓
  - Pre-commit hooks for code quality
  - GitHub Actions CI workflow
  - Security scanning (Gitleaks, Trivy)
  - Development dependencies

- **Phase 2**: Basic Chat Functionality ✓
  - WebSocket implementation
  - Real-time messaging
  - Message broadcasting

- **Phase 3**: AI Integration ✓
  - Universal multi-provider support via LiteLLM
  - Support for top 5 AI providers (Anthropic, OpenAI, Google, Meta, DeepSeek)
  - Streaming responses with typing indicators
  - Markdown rendering with code highlighting
  - Easy provider switching via environment variables

### Next Phase
- **Phase 4**: Enhanced UI/UX - Animations, themes, and polished user experience

## Important Notes

### Git Workflow
- **NEVER push directly to the master branch**
- Always create a feature branch for your changes
- Push to the feature branch and create a Pull Request
- **ALWAYS check CI checks after pushing code**
  - Go to the PR page on GitHub
  - Verify all workflow checks are passing (green checkmarks)
  - If checks fail, review the error logs and fix issues before requesting review
- Wait for CI checks to pass before merging
- All changes must go through the PR review process

### PR Discussion & Comment Management

When addressing PR feedback, there are two scenarios:

1. **In GitHub PR Comments**: When @claude is mentioned in a PR review comment/discussion on GitHub
2. **In Claude Code Session**: When the user asks you to address PR comments directly in a Claude Code session

Follow the appropriate guidelines below based on the context.

#### Responding to PR Comments

1. **Read and Understand Context**
   - Read the entire comment thread to understand the discussion
   - Review related code changes and files
   - Identify the specific concern or question being raised

2. **Reply In-Thread**
   - To reply to a specific review comment thread, use the GitHub API:
     ```bash
     gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments/COMMENT_ID/replies \
       -X POST -f body="Your threaded reply here"
     ```
   - To get the comment ID, fetch PR comments:
     ```bash
     gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments
     ```
   - **Note**: `gh pr review --comment` creates top-level PR comments, NOT threaded replies
   - **NEVER mark comments as resolved** - let the reviewer resolve them
   - Keep replies focused and concise

3. **Comment Reply Format**
   ```markdown
   [Vary your greeting - examples: "Thanks for catching that!", "Good point!",
    "You're right!", "Agreed!", etc. - Acknowledge the specific point]

   [Explain what changes were made or will be made]

   Changes made in: `path/to/file.ext:line_number`
   Commit: [commit-hash]
   ```

4. **Making Changes**
   - Create **individual commits per comment** addressed
   - Use descriptive commit messages that reference the feedback
   - Push changes to the PR branch

5. **Commit Message Format for PR Comments**
   ```
   fix: [brief description addressing comment]

   Addresses PR comment: [link to comment or description]
   - [bullet point of change 1]
   - [bullet point of change 2]

   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

6. **Echo Summary**
   - After addressing comments, provide a summary in the Claude Code session or CI output
   - Include: number of comments addressed, files changed, and overall impact
   - Example: "✅ Addressed 3 PR comments: updated error handling in `app/main.py:45`, fixed typo in docs, and added missing type hints"

#### Best Practices
- Address comments promptly and thoroughly
- Ask clarifying questions if feedback is unclear
- Reference specific line numbers and file paths in responses
- Test changes locally before pushing
- Ensure CI checks pass after addressing comments

### Git Worktree Strategy

Git worktrees allow you to work on multiple feature branches simultaneously without stashing or switching branches.

#### Why Use Worktrees?

- Work on multiple PRs in parallel
- Keep development environments isolated
- No need to stash changes or switch branches
- Run separate dev servers, tests, or builds for each branch
- Main worktree stays on master for quick reference

#### Setup Worktree for New Feature

```bash
# Create worktree for new feature branch
git worktree add ../stupid_chat_bot-feature-name -b feature-name

# Navigate to worktree
cd ../stupid_chat_bot-feature-name

# Verify you're on the new branch
git branch --show-current
```

#### Working with Worktrees

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

#### List All Worktrees

```bash
# See all active worktrees
git worktree list

# Example output:
# /Users/user/work/study/stupid_chat_bot        d368f36 [master]
# /Users/user/work/study/stupid_chat_bot-auth   a1b2c3d [feature-auth]
# /Users/user/work/study/stupid_chat_bot-ui     e4f5g6h [feature-ui]
```

#### Cleanup After PR Merge

```bash
# Remove worktree (do this from any worktree or main repo)
git worktree remove ../stupid_chat_bot-feature-name

# Delete the merged branch
git branch -d feature-name

# If branch was deleted on remote, prune local references
git fetch --prune
```

#### Best Practices

- **Naming Convention**: Use consistent naming like `../project-name-branch-name`
- **Directory Organization**: Keep worktrees in the same parent directory as main repo
- **Branch Naming**: Match worktree folder name to branch name for clarity
- **Cleanup Promptly**: Remove worktrees after PR is merged to avoid clutter
- **Main Worktree**: Keep the main worktree on master branch for quick checks and updates
- **Documentation**: When creating worktrees, document active ones if working on long-term features

#### Common Workflows

**Creating PR from Worktree:**
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

**Addressing PR Comments in Worktree:**
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
gh pr review 123 --comment --body "✅ Fixed error handling and added type hints"
```

### Development Guidelines
- Follow the phased implementation approach outlined in README.md
- Prioritize simplicity ("stupid" chat bot philosophy)
- Use TypeScript for frontend in later phases
- Implement proper error handling and user feedback
- Test WebSocket connections thoroughly
- Follow security best practices for API key management
- Consider rate limiting for AI API calls

### AI Provider Configuration

The application supports multiple AI providers through LiteLLM. To switch providers:

1. **Set environment variables in `.env`:**
   ```bash
   AI_PROVIDER=anthropic  # Options: anthropic, openai, google, meta, deepseek
   ANTHROPIC_API_KEY=your-key-here  # Use the key for your chosen provider
   ```

2. **Available providers and their default models:**
   - `anthropic`: claude-3-5-sonnet-20241022
   - `openai`: gpt-4-turbo
   - `google`: gemini-1.5-pro
   - `meta`: llama-3.1-70b
   - `deepseek`: deepseek-chat

3. **Override default model (optional):**
   ```bash
   AI_MODEL=claude-3-opus-20240229
   ```

4. **Restart the backend:**
   ```bash
   # If using Docker
   docker compose restart backend

   # If running locally
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

No code changes are required to switch providers - it's all configuration-based!
