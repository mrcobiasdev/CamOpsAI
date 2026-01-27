# Add OpenSpec Archive Commit Workflow - Design

## Overview
Extend the git-workflow to ensure OpenSpec archived changes are properly committed to the Git repository, preventing loss of work and maintaining consistent documentation between local and remote repositories.

## Problem Statement

When a developer archives an OpenSpec change using `openspec archive <id>`, the following changes occur:
1. Change folder moves from `changes/<id>/` to `changes/archive/YYYY-MM-DD-<id>/`
2. Spec files in `specs/` are updated (if capability added/modified)
3. OpenSpec metadata files may be updated

Currently, these changes are NOT automatically committed, which creates issues:
- Developer may forget to commit, leading to lost work
- Local and remote repositories diverge
- Inconsistent documentation state
- Risk of accidental cleanup losing changes

## Solution Approach

### Option 1: Document the Workflow (Chosen)
Add clear requirements and documentation to:
- Specify that archived changes must be committed
- Define when to commit (immediately after archiving)
- Document what to commit (archived folder, spec updates)
- Add checklist item to AGENTS.md Stage 3

**Pros:**
- Simple, no new tools required
- Follows existing documentation patterns
- Works with current OpenSpec CLI
- Flexible - developers can use their preferred Git workflow

**Cons:**
- Relies on manual execution
- Developer must remember to commit

### Option 2: Create Helper Script
Create a shell script that:
- Detects recent archiving operations
- Stages archived changes and spec updates
- Creates conventional commit message
- Offers to push to GitHub

**Pros:**
- Reduces manual steps
- Consistent commit messages
- Can include validation

**Cons:**
- Additional maintenance (cross-platform: bash vs PowerShell)
- Requires script execution awareness
- Still requires manual triggering

### Option 3: Modify OpenSpec CLI (Out of Scope)
Integrate commit automation directly into the OpenSpec archive command.

**Pros:**
- Fully automated
- No manual steps

**Cons:**
- Requires modifying external tool
- Out of scope for this change
- May not be maintainable long-term

## Implementation Plan (Chosen: Option 1 + Optional Option 2)

### Primary: Documentation Requirements

Add to `openspec/specs/git-workflow/spec.md`:

```markdown
### Requirement: The repository SHALL commit archived OpenSpec changes

The repository SHALL ensure that when OpenSpec changes are archived,
the resulting file changes are committed to Git with conventional
commit messages.

#### Scenario: Archive triggers immediate commit
- **GIVEN** a developer archives a change using `openspec archive <id>`
- **WHEN** the archive command completes successfully
- **THEN** the developer SHALL commit the archived change and spec updates
- **AND** the commit message SHALL follow conventional commits format
- **AND** the commit message SHALL describe the change that was archived

#### Scenario: Commit includes all archive changes
- **GIVEN** a change has been archived
- **WHEN** creating the commit
- **THEN** the commit SHALL include the archived folder in `changes/archive/`
- **AND** the commit SHALL include any spec updates in `specs/`
- **AND** the commit SHA SHALL match the archive date

#### Scenario: Commit message references archived change
- **GIVEN** an archived change is being committed
- **WHEN** writing the commit message
- **THEN** the commit message SHALL use "docs:" or "chore:" prefix
- **AND** the subject SHALL include the change ID
- **AND** the body SHALL describe what capability was added or modified
```

### Secondary: Update AGENTS.md

Modify `openspec/AGENTS.md` Stage 3 section:

**Before:**
```markdown
### Stage 3: Archiving Changes
After deployment, create separate PR to:
- Move `changes/[name]/` → `changes/archive/YYYY-MM-DD-[name]/`
- Update `specs/` if capabilities changed
- Use `openspec archive <change-id> --skip-specs --yes` for tooling-only changes
- Run `openspec validate --strict --no-interactive` to confirm the archived change passes checks
```

**After:**
```markdown
### Stage 3: Archiving Changes
After deployment, create separate PR to:
- Move `changes/[name]/` → `changes/archive/YYYY-MM-DD-[name]/`
- Update `specs/` if capabilities changed
- Use `openspec archive <change-id> --skip-specs --yes` for tooling-only changes (always pass the change ID explicitly)
- Run `openspec validate --strict --no-interactive` to confirm the archived change passes checks
- **Commit the archived changes**:
  - Stage the archived folder: `git add openspec/changes/archive/YYYY-MM-DD-[name]/`
  - Stage spec updates: `git add openspec/specs/`
  - Commit with conventional message: `git commit -m "docs: archive [change-id]"`
  - Push to GitHub: `git push`
```

### Optional: Helper Script (Nice to Have)

Create `tools/commit-archived-openspec.sh`:

```bash
#!/bin/bash
# Helper script to commit archived OpenSpec changes

# Find most recently archived change
LAST_ARCHIVE=$(ls -t openspec/changes/archive/ | head -1)

if [ -z "$LAST_ARCHIVE" ]; then
    echo "No archived changes found"
    exit 1
fi

echo "Found archived change: $LAST_ARCHIVE"

# Stage archived change and spec updates
git add "openspec/changes/archive/$LAST_ARCHIVE/"
git add openspec/specs/

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "No changes to commit"
    exit 0
fi

# Create commit message
COMMIT_MSG="docs: archive ${LAST_ARCHIVE%-*}"

# Show what will be committed
git diff --cached --stat

# Confirm
read -p "Commit these changes? [y/N] " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "$COMMIT_MSG"
    echo "Committed: $COMMIT_MSG"
    read -p "Push to GitHub? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push
        echo "Pushed to GitHub"
    fi
else
    echo "Aborted"
    git reset
fi
```

## Commit Message Format

When committing archived OpenSpec changes, use:

**Format:**
```
docs: archive <change-id>

Archive <change-id> and update affected specs.

- Archived change: <brief description>
- Updated spec: <capability-name>
- <additional context if needed>
```

**Examples:**
```
docs: archive add-gitignore

Archive add-gitignore and update repository-security spec.

- Archived change: Add .gitignore for repository security
- Updated spec: repository-security (4 requirements added)

docs: archive initialize-git-repository

Archive initialize-git-repository and update git-workflow spec.

- Archived change: Initialize Git repository with commit structure
- Updated spec: git-workflow (4 requirements added)
```

## Trade-offs

**Documentation-only approach:**
- ✅ Simple, maintainable
- ✅ Works immediately without tooling
- ❌ Relies on developer diligence

**Helper script approach:**
- ✅ Streamlines repetitive task
- ✅ Consistent commit messages
- ❌ Platform-specific (bash vs Windows)
- ❌ Requires execution awareness

**Chosen approach:** Documentation first, optional helper script as enhancement.

## Security Considerations
- Archived changes contain no sensitive information
- Commits follow existing git-workflow requirements
- No additional authentication needed (uses existing Git credentials)

## References
- Conventional commits: https://www.conventionalcommits.org/
- git-workflow spec: openspec/specs/git-workflow/spec.md
- OpenSpec AGENTS.md: openspec/AGENTS.md
