# Migration to uv Lock Files for Reproducible Builds

## Executive Summary

This document outlines the migration plan for transitioning from `requirements.txt` to `uv`'s modern project management with lock files, addressing the reproducibility gap identified in [PR #17 review comment](https://github.com/dremdem/stupid_chat_bot/pull/17#discussion_r2592772548).

**Problem**: Current Docker setup uses `uv pip install --system -r requirements.txt`, which doesn't leverage uv's lock file capabilities for dependency version freezing and hash verification.

**Solution**: Migrate to `pyproject.toml` + `uv.lock` + `uv sync` workflow for guaranteed reproducible builds.

---

## Current State Analysis

### What We Have Now

**Backend Dependency Management**:
```dockerfile
# backend/Dockerfile
RUN uv pip install --system -r requirements.txt
```

**Current `requirements.txt`**:
```txt
fastapi==0.115.5
uvicorn[standard]==0.32.1
pydantic==2.10.3
pydantic-settings==2.6.1
python-dotenv==1.0.1
websockets==14.1
litellm==1.80.5
```

**Existing Configuration**:
- `pyproject.toml` exists but only contains tool configs (black, ruff, pytest)
- No `[project]` section
- No `uv.lock` file

### The Problem

1. **No Transitive Dependency Locking**: While direct dependencies are pinned, their dependencies are not
2. **No Hash Verification**: No cryptographic validation of downloaded packages
3. **Non-Deterministic Builds**: Two builds at different times could have different dependency trees
4. **Missing uv Features**: Not using uv's modern project management capabilities

**Example Risk Scenario**:
```
Today: fastapi==0.115.5 → starlette==0.41.2 → anyio==4.6.2
Next month: fastapi==0.115.5 → starlette==0.41.2 → anyio==4.7.0
                                                     ↑ Different version!
```

---

## Migration Strategy

### Option A: Full uv Project Migration (Recommended)

**Description**: Convert to a full uv-managed project with `pyproject.toml` + `uv.lock`.

**Approach**:
1. Add `[project]` section to `pyproject.toml`
2. Run `uv lock` to generate lock file
3. Update Dockerfile to use `uv sync --frozen`
4. Keep `requirements.txt` for backward compatibility (generated from lock)

**Pros**:
- ✅ Full reproducibility with hash verification
- ✅ Cross-platform lock files
- ✅ Leverages all uv features (workspace support, dev dependencies, etc.)
- ✅ Modern Python packaging standards (PEP 621)
- ✅ Foundation for future improvements (monorepo, extras, etc.)

**Cons**:
- ⚠️ Larger change scope
- ⚠️ Requires updating development workflow documentation
- ⚠️ Need to educate team on new commands

**Impact**: Medium - requires changes to docs and developer workflow

---

### Option B: Export Lock File to requirements.txt

**Description**: Use `uv export` to generate a fully locked `requirements.txt` with hashes.

**Approach**:
1. Create minimal `pyproject.toml` with dependencies
2. Run `uv lock` to generate lock file
3. Run `uv export --format requirements.txt > requirements.txt`
4. Commit the exported requirements.txt
5. Keep using `uv pip install --system -r requirements.txt` in Docker

**Pros**:
- ✅ Minimal changes to existing workflow
- ✅ Hash verification included
- ✅ Easy to review locked versions (plain text)
- ✅ Compatible with non-uv tools

**Cons**:
- ❌ Two-step process to update dependencies (lock → export)
- ❌ `requirements.txt` becomes large (includes all transitive deps + hashes)
- ❌ Not using uv's full capabilities
- ❌ Lock file and requirements.txt can drift

**Impact**: Low - minimal workflow changes

---

### Option C: Hybrid Approach (Recommended for Gradual Migration)

**Description**: Implement Option A but maintain Option B as fallback.

**Approach**:
1. Implement full uv project (Option A)
2. Add CI step to export `requirements.txt` for compatibility
3. Gradually phase out requirements.txt once team is comfortable
4. Keep both approaches working during transition period

**Pros**:
- ✅ Best of both worlds
- ✅ Smooth migration path
- ✅ Fallback if issues arise
- ✅ Team can learn gradually

**Cons**:
- ⚠️ Temporary complexity (two systems)
- ⚠️ Need to keep both in sync

**Impact**: Medium initially, Low after migration complete

---

## Recommended Implementation: Option C (Hybrid)

### Phase 1: Add uv Project Structure (Week 1)

#### Step 1: Update pyproject.toml

```toml
# backend/pyproject.toml

[project]
name = "stupid-chat-bot-backend"
version = "0.1.0"
description = "Backend for Stupid Chat Bot"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi==0.115.5",
    "uvicorn[standard]==0.32.1",
    "pydantic==2.10.3",
    "pydantic-settings==2.6.1",
    "python-dotenv==1.0.1",
    "websockets==14.1",
    "litellm==1.80.5",
]

[project.optional-dependencies]
dev = [
    "black>=24.0.0",
    "ruff>=0.5.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
]

[tool.black]
line-length = 100
target-version = ['py312']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = []

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### Step 2: Generate Lock File

```bash
cd backend
uv lock
```

This creates `uv.lock` with:
- Exact versions of all dependencies (direct + transitive)
- SHA256 hashes for all packages
- Cross-platform compatibility markers

#### Step 3: Export for Backward Compatibility

```bash
uv export --format requirements.txt --no-hashes > requirements.txt
uv export --format requirements.txt > requirements-locked.txt
```

**Files generated**:
- `requirements.txt` - Human-readable, no hashes (for review)
- `requirements-locked.txt` - Full lock with hashes (for production)

#### Step 4: Update Dockerfile

**Option 1: Use uv sync (Primary)**

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies from lock file (with hashes!)
RUN uv sync --frozen --no-dev --no-editable

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Option 2: Fallback with requirements-locked.txt**

```dockerfile
# backend/Dockerfile.fallback
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy locked requirements
COPY requirements-locked.txt .

# Install with hash verification
RUN uv pip install --system --require-hashes -r requirements-locked.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Step 5: Update docker-compose.yml

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile  # Uses uv sync
    # ... rest of config
```

---

### Phase 2: Update Development Workflow (Week 1-2)

#### Update CLAUDE.md

**Add section: Dependency Management**

```markdown
## Dependency Management

### Backend Dependencies

The backend uses `uv` for modern, reproducible dependency management.

#### File Structure
- `pyproject.toml` - Project metadata and dependency specifications
- `uv.lock` - Lock file with exact versions and hashes (DO NOT edit manually)
- `requirements.txt` - Exported for compatibility (generated from uv.lock)
- `requirements-locked.txt` - Full lock with hashes (generated from uv.lock)

#### Adding Dependencies

**Option 1: Using uv (Recommended)**
```bash
cd backend
# Add to pyproject.toml and lock
uv add <package-name>

# Or manually edit pyproject.toml, then:
uv lock

# Export for compatibility
uv export --format requirements.txt --no-hashes > requirements.txt
uv export --format requirements.txt > requirements-locked.txt

# Rebuild Docker image
docker-compose build backend
```

**Option 2: Using Docker (Quick Testing)**
```bash
# Install in running container
docker-compose exec backend uv add <package-name>

# Or with pip (temporary, not persisted in image)
docker-compose exec backend pip install <package-name>

# Don't forget to update lock file on host!
cd backend
uv lock
```

#### Updating Dependencies

```bash
cd backend
# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package <package-name>

# Export
uv export --format requirements.txt --no-hashes > requirements.txt
uv export --format requirements.txt > requirements-locked.txt

# Rebuild
docker-compose build backend
```

#### Syncing Environment

```bash
# Install from lock file (local development)
cd backend
uv sync

# Install dev dependencies
uv sync --all-extras
```
```

#### Update Development Commands

```bash
# Old workflow
pip install <package>
pip freeze > requirements.txt

# New workflow
uv add <package>                    # Adds to pyproject.toml and locks
uv export --format requirements.txt --no-hashes > requirements.txt
uv export --format requirements.txt > requirements-locked.txt
```

---

### Phase 3: CI/CD Integration (Week 2)

#### Update GitHub Actions

```yaml
# .github/workflows/ci.yml

name: CI

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        run: pip install uv

      - name: Verify lock file is up to date
        run: |
          cd backend
          uv lock --check

      - name: Install dependencies
        run: |
          cd backend
          uv sync --frozen --all-extras

      - name: Run tests
        run: |
          cd backend
          uv run pytest

      - name: Verify exported requirements.txt matches
        run: |
          cd backend
          uv export --format requirements.txt --no-hashes > requirements-test.txt
          diff requirements.txt requirements-test.txt
```

#### Add Make Target for Lock Verification

```makefile
# Makefile addition

.PHONY: lock-check lock-update lock-export

lock-check: ## Verify lock file is up to date
	cd backend && uv lock --check
	@echo "✓ Lock file is up to date"

lock-update: ## Update lock file
	cd backend && uv lock --upgrade
	$(MAKE) lock-export
	@echo "✓ Lock file updated"

lock-export: ## Export lock file to requirements.txt
	cd backend && uv export --format requirements.txt --no-hashes > requirements.txt
	cd backend && uv export --format requirements.txt > requirements-locked.txt
	@echo "✓ Requirements files exported"

backend-add-dep: ## Add backend dependency (usage: make backend-add-dep PKG=package-name)
	@if [ -z "$(PKG)" ]; then echo "Usage: make backend-add-dep PKG=package-name"; exit 1; fi
	cd backend && uv add $(PKG)
	$(MAKE) lock-export
	@echo "✓ Added $(PKG) and updated lock files"
```

---

### Phase 4: Docker Dev Environment Integration (Week 2-3)

#### Update Dockerfile.dev

```dockerfile
# backend/Dockerfile.dev
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install ALL dependencies including dev extras
RUN uv sync --frozen --all-extras

# Create non-root user
RUN useradd -m -u 1000 developer && \
    chown -R developer:developer /app

USER developer

# Expose ports
EXPOSE 8000 5678

# Command will be overridden by docker-compose
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Update docker-compose.dev.yml

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app
      # Note: uv installs to .venv by default when in project mode
      # Mount as volume to persist across container restarts
      - backend_venv:/app/.venv
    command: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    # ... rest of config

volumes:
  backend_venv:
```

---

## Verification & Testing Plan

### Pre-Migration Checklist

- [ ] Back up current `requirements.txt`
- [ ] Document current dependency versions
- [ ] Test current setup works as expected
- [ ] Ensure all tests pass with current setup

### Migration Verification Steps

#### Step 1: Lock File Generation
```bash
cd backend
uv lock
# Verify uv.lock was created
ls -lh uv.lock
# Should see file with size > 0
```

#### Step 2: Verify Lock File Completeness
```bash
# Check that all dependencies are locked
uv lock --check
# Should output: "Lockfile is up-to-date"
```

#### Step 3: Test Local Sync
```bash
# Create fresh virtual environment
cd backend
rm -rf .venv
uv sync --frozen
# Verify installation
uv run python -c "import fastapi; print(fastapi.__version__)"
# Should print: 0.115.5
```

#### Step 4: Test Docker Build
```bash
# Build image
docker build -t test-backend ./backend

# Verify dependencies
docker run --rm test-backend uv run python -c "import fastapi; print(fastapi.__version__)"
# Should print: 0.115.5

# Check for hash verification in build logs
docker build --no-cache -t test-backend ./backend 2>&1 | grep -i hash
```

#### Step 5: Test Exported Requirements
```bash
cd backend
uv export --format requirements.txt > requirements-test.txt

# Compare with existing
diff requirements.txt requirements-test.txt

# Should show only transitive dependencies added
```

#### Step 6: Integration Test
```bash
# Start services
docker-compose up -d

# Test API
curl http://localhost:8000/health

# Check logs for any dependency errors
docker-compose logs backend | grep -i error
```

### Post-Migration Verification

- [ ] All tests pass in Docker
- [ ] Application starts successfully
- [ ] No dependency conflicts
- [ ] Lock file can be regenerated (`uv lock --check` passes)
- [ ] Requirements export matches expected format
- [ ] CI pipeline passes
- [ ] Development workflow documented

---

## Rollback Plan

If issues arise during migration:

### Immediate Rollback
```bash
# Restore old requirements.txt
git checkout HEAD -- backend/requirements.txt

# Restore old Dockerfile
git checkout HEAD -- backend/Dockerfile

# Rebuild
docker-compose build backend
docker-compose up -d
```

### Partial Rollback (Keep Lock File, Use requirements-locked.txt)
```bash
# Switch Dockerfile to use requirements-locked.txt
# Edit backend/Dockerfile to use Option 2 (fallback)

# Rebuild
docker-compose build backend
```

---

## Migration Timeline

### Week 1: Foundation
- **Day 1-2**: Update `pyproject.toml`, generate lock file
- **Day 3**: Update Dockerfile with both options
- **Day 4**: Test locally and in Docker
- **Day 5**: Update documentation

### Week 2: Integration
- **Day 1-2**: Update CI/CD pipeline
- **Day 3**: Create Make targets
- **Day 4-5**: Team testing and feedback

### Week 3: Rollout
- **Day 1**: Merge to development branch
- **Day 2-3**: Monitor for issues
- **Day 4**: Update Dockerfile.dev
- **Day 5**: Complete migration, remove fallback

---

## Benefits After Migration

### Immediate Benefits
1. **100% Reproducible Builds**: Same dependencies every time
2. **Hash Verification**: Security against compromised packages
3. **Transitive Dependency Locking**: No surprise updates
4. **CI Verification**: `uv lock --check` catches drift

### Long-term Benefits
1. **Foundation for Monorepo**: uv supports workspace features
2. **Better Dependency Management**: Easy upgrades and audits
3. **Modern Standards**: PEP 621 compliance
4. **Performance**: uv is significantly faster than pip

---

## Commands Reference

### Common Operations

```bash
# Add dependency
uv add <package>

# Add dev dependency
uv add --dev <package>

# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package <package>

# Install from lock
uv sync --frozen

# Install with dev dependencies
uv sync --frozen --all-extras

# Verify lock file
uv lock --check

# Export to requirements.txt
uv export --format requirements.txt --no-hashes > requirements.txt
uv export --format requirements.txt > requirements-locked.txt

# Run command in uv environment
uv run <command>

# Run tests
uv run pytest
```

### Docker Commands

```bash
# Build with uv sync
docker build -t backend-test ./backend

# Build with requirements-locked.txt (fallback)
docker build -f backend/Dockerfile.fallback -t backend-test ./backend

# Run container
docker run -p 8000:8000 backend-test

# Check installed packages
docker run --rm backend-test uv run pip list
```

---

## Security Considerations

### Hash Verification

Lock files include SHA256 hashes for all packages:
```toml
# Example from uv.lock
[[package]]
name = "fastapi"
version = "0.115.5"
source = { registry = "https://pypi.org/simple" }
dependencies = ["starlette", "pydantic"]
sdist = { url = "...", hash = "sha256:..." }
wheels = [
    { url = "...", hash = "sha256:..." },
]
```

This protects against:
- Compromised package registry
- Man-in-the-middle attacks
- Package substitution

### Dependency Auditing

```bash
# Check for known vulnerabilities (future enhancement)
uv tree  # Visualize dependency tree
```

---

## Troubleshooting

### Issue: Lock file is out of date

```bash
# Error: Lockfile is out of date
# Solution:
cd backend
uv lock
uv export --format requirements.txt --no-hashes > requirements.txt
```

### Issue: Docker build fails with hash mismatch

```bash
# Error: Hash mismatch when installing dependencies
# Cause: Network issues or corrupted download
# Solution: Rebuild without cache
docker build --no-cache -t backend ./backend
```

### Issue: Conflicting dependencies

```bash
# Error: Unable to resolve dependencies
# Solution: Check pyproject.toml for version conflicts
cd backend
uv lock --verbose  # See detailed resolution
```

### Issue: Different behavior in Docker vs local

```bash
# Verify both use same lock file
cd backend
uv lock --check  # Should pass

# Verify Docker uses frozen install
# Check Dockerfile has: uv sync --frozen
```

---

## References

- [uv Documentation - Lock and Sync](https://docs.astral.sh/uv/concepts/projects/sync/)
- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [Docker Best Practices for Python](https://docs.docker.com/language/python/build-images/)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-05
**Author**: Claude (AI Assistant)
**Status**: Ready for Implementation
