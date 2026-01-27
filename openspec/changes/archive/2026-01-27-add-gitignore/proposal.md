# Change: Add .gitignore for Repository Security

## Why
The CamOpsAI project currently lacks a `.gitignore` file, which means sensitive files and generated content could accidentally be committed to a public repository. Without proper exclusions, developers may inadvertently expose API keys, database credentials, and session data.

## What Changes
- Create root-level `.gitignore` file
- Exclude sensitive configuration files (`.env`)
- Exclude generated content directories (`frames/`, `sessions/`)
- Exclude Python development artifacts (venv, `__pycache__`, caches)
- Exclude IDE and OS-specific files

## Impact
- Affected specs: repository-security (new capability)
- Affected code: Repository root only
- Risk: Low - only affects future commits, not existing tracked files
- Create a root-level `.gitignore` file following Python project best practices
- Exclude sensitive configuration files (`.env`)
- Exclude generated content directories (`frames/`, `sessions/`)
- Exclude Python development artifacts (venv, `__pycache__`, caches)
- Exclude IDE and OS-specific files

## Out of Scope
- Migration or removal of existing sensitive files from git history
- Git hooks or pre-commit configuration
- Documentation about security practices

## Related Work
None

## Risks
- Low risk: Adding a `.gitignore` only affects future commits, not existing tracked files
- Existing sensitive files (if already tracked) would need manual removal from git history

## Timeline
- Estimated effort: 1-2 hours
- Single-task change, can be completed in one session
