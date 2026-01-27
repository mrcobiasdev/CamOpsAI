# Change: Add OpenSpec Archive Commit Workflow

## Why
Currently, when OpenSpec changes are archived, the changes to the repository (archived files, spec updates) are not automatically committed to Git. This means developers must manually remember to commit and push these changes after archiving, which can lead to:
- Lost work if not committed promptly
- Incomplete history if changes are forgotten
- Inconsistent documentation between local and remote repositories

## What Changes
- Add requirement to git-workflow spec specifying that archived changes must be committed
- Document the process for committing archived OpenSpec changes
- Optionally create a helper script to automate the commit process after archiving
- Update AGENTS.md to include commit step in Stage 3: Archiving Changes

## Impact
- Affected specs: git-workflow (modified)
- Affected code: Documentation (AGENTS.md), optional helper script
- Risk: Low - this is workflow documentation and optional automation

## Out of Scope
- Creating GitHub Actions to automate commits (CI/CD scope)
- Modifying the openspec CLI tool itself
- Implementing automatic push without user confirmation
- Creating branch protection rules

## Related Work
- git-workflow spec (existing - needs modification)
- initialize-git-repository archived change (recent - shows current manual process)
- repository-security spec (defines what files should be committed)

## Risks
- None significant - this adds clarity and optional automation to existing workflow

## Timeline
- Estimated effort: 1 hour
- Single-session task

## Success Criteria
- git-workflow spec includes requirement for committing archived changes
- AGENTS.md documents the commit step after archiving
- Optional helper script available to streamline the process
- Clear documentation of when to commit and what to commit
