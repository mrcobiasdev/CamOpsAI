# Add .gitignore - Design

## Overview
Add a standard Python project `.gitignore` file to protect sensitive information and prevent generated content from being committed to the repository.

## File Structure
```
.gitignore (new)
```

## Content Strategy

The `.gitignore` file will include:

### 1. Environment & Configuration
- `.env` - Contains API keys, database credentials, and sensitive configuration
- `.env.local`, `.env.*.local` - Environment-specific overrides

### 2. Python Artifacts
- `venv/`, `env/`, `.venv/` - Virtual environments
- `__pycache__/` - Python bytecode cache
- `*.py[cod]` - Compiled Python files
- `.pytest_cache/` - Pytest cache directory
- `.ruff_cache/` - Ruff linter cache
- `.mypy_cache/` - Type checking cache
- `.coverage`, `htmlcov/` - Test coverage reports
- `*.egg-info/` - Package metadata

### 3. Generated Content
- `frames/` - Captured images from camera streams (defined in .env as FRAMES_STORAGE_PATH)
- `sessions/` - Session storage including WhatsApp sessions (defined in .env as WHATSAPP_SESSION_DIR)

### 4. Database
- `*.db`, `*.sqlite`, `*.sqlite3` - SQLite databases (if used locally)
- `*.sql` - Database dumps (specific patterns)

### 5. IDE & Editor
- `.vscode/`, `.idea/` - IDE configuration
- `*.swp`, `*.swo` - Vim swap files
- `*~` - Backup files

### 6. OS-Specific
- `.DS_Store` - macOS metadata
- `Thumbs.db` - Windows thumbnail cache
- `.bash_history` - Shell history

## Trade-offs

### Option 1: Minimal .gitignore
Include only essential items (`.env`, `venv`, `__pycache__`)
- **Pros**: Smaller, easier to maintain
- **Cons**: May miss edge cases, less comprehensive protection

### Option 2: Comprehensive .gitignore (Chosen)
Include all standard Python project exclusions plus project-specific directories
- **Pros**: Comprehensive protection, follows Python community best practices
- **Cons**: Slightly larger file, but still manageable

## Security Considerations
- The `.gitignore` file itself is not a security mechanism, it only prevents accidental commits
- Already-tracked sensitive files must be manually removed from git history
- Consider adding a pre-commit hook to validate no secrets are committed (out of scope for this change)

## References
- Python .gitignore template: https://github.com/github/gitignore/blob/main/Python.gitignore
- Project-specific configuration: `.env.example` shows what should be excluded
