# Initialize Git Repository - Design

## Overview
Initialize the CamOpsAI project Git repository with a structured commit history that follows best practices and provides a clean foundation for future development.

## Commit Structure

The repository will be initialized with the following commit sequence:

### Commit 1: Initial project structure
**Scope:** Core project files and documentation
- `README.md` - Project documentation
- `requirements.txt` - Python dependencies
- `run.py` - Application entry point
- `src/` - All source code modules
  - `main.py`, `config/`, `capture/`, `analysis/`, `storage/`, `alerts/`, `api/`
- `tests/` - Test suite
  - All test files and fixtures
- `tools/` - Utility scripts
- `docs/` - Documentation files
- `alembic/` - Database migrations
- `alembic.ini` - Alembic configuration
- `.env.example` - Environment configuration template

**Commit message:**
```
feat: initial project structure

Add complete CamOpsAI codebase with camera capture,
LLM vision analysis, motion detection, and WhatsApp
notifications functionality.

- FastAPI backend with PostgreSQL integration
- RTSP camera capture with OpenCV
- Multi-provider LLM vision (OpenAI, Anthropic, Gemini)
- Motion detection with configurable sensitivity
- WhatsApp Business API notifications
- Comprehensive test suite
```

### Commit 2: Add .gitignore
**Scope:** Git ignore configuration
- `.gitignore` - Python and project-specific ignore patterns

**Commit message:**
```
chore: add .gitignore

Configure .gitignore to exclude sensitive files,
generated content, and development artifacts from
version control.

- Environment files (.env, .env.local)
- Python artifacts (venv, __pycache__, caches)
- Generated content (frames/, sessions/)
- IDE and OS-specific files
```

### Commit 3: Add openspec repository-security spec
**Scope:** OpenSpec specifications and archived changes
- `openspec/specs/repository-security/` - New capability spec
- `openspec/changes/archive/2026-01-27-add-gitignore/` - Archived change

**Commit message:**
```
feat: add repository-security spec and archive add-gitignore

Add repository-security capability spec and archive
the add-gitignore change that introduced .gitignore.

- Define requirements for excluding sensitive files
- Define requirements for generated content exclusion
- Archive add-gitignore change to history
```

### Commit 4: Add openspec AGENTS.md
**Scope:** OpenSpec agent instructions
- `AGENTS.md` - Agent instructions (project root)
- `openspec/AGENTS.md` - OpenSpec agent instructions
- `openspec/project.md` - Project context

**Commit message:**
```
docs: add openspec agent instructions

Configure OpenSpec agent instructions for AI-assisted
development and spec-driven workflows.

```

### Commit 5: Add .opencode command history
**Scope:** OpenSpec command history
- `.opencode/command/openspec-*.md` - Command history files

**Commit message:**
```
chore: add openspec command history

Track openspec command interactions for context and
reproducibility.

```

## Trade-offs

### Option 1: Single large commit
- **Pros:** Simple, atomic, represents complete project state
- **Cons:** Harder to review, loses logical grouping, difficult to revert specific changes

### Option 2: Multiple logical commits (Chosen)
- **Pros:** Clear history, easier review, logical grouping, better for blame/history analysis
- **Cons:** Slightly more complex to create

## Remote Configuration

Assumptions:
- GitHub repository already exists
- Remote origin is configured as: `git remote add origin <repository-url>`
- Default branch is `main`
- Initial push will use: `git push -u origin main`

## Security Considerations
- `.env` file must never be committed (ensured by .gitignore)
- `.env.example` is committed as a template without sensitive values
- No sensitive credentials or API keys in committed files

## References
- Git commit message conventions: https://www.conventionalcommits.org/
- Python project structure: https://docs.python-guide.org/writing/structure/
