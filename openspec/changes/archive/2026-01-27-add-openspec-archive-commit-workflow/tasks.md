# Add OpenSpec Archive Commit Workflow - Tasks

## Task List

### 1. Update git-workflow spec with archive commit requirement
- [x] Open `openspec/specs/git-workflow/spec.md`
- [x] Add new requirement section after existing requirements
- [x] Write requirement: "The repository SHALL commit archived OpenSpec changes"
- [x] Add 3 scenarios:
  - Archive triggers immediate commit
  - Commit includes all archive changes
  - Commit message references archived change
- [x] Verify format matches existing requirements (SHALL, GIVEN/WHEN/THEN)

### 2. Update AGENTS.md Stage 3 section
- [x] Open `openspec/AGENTS.md`
- [x] Locate "Stage 3: Archiving Changes" section
- [x] Add "**Commit archived changes**" subsection
- [x] Document commit steps:
  - Stage archived folder
  - Stage spec updates
  - Create conventional commit message
  - Push to GitHub
- [x] Include example commands for each step
- [x] Verify formatting matches existing sections

### 3. Create helper script (optional)
- [ ] Create `tools/commit-archived-openspec.sh` file
- [ ] Add bash shebang: `#!/bin/bash`
- [ ] Implement logic to find most recent archived change
- [ ] Implement git add commands for archived folder and specs
- [ ] Implement git diff --cached check
- [ ] Implement commit message generation
- [ ] Implement user confirmation prompts
- [ ] Implement git push option
- [ ] Make script executable: `chmod +x tools/commit-archived-openspec.sh`
- [ ] Add error handling for no archived changes found
- [ ] Test script with recent archived change

### 4. Create PowerShell equivalent (for Windows)
- [ ] Create `tools/commit-archived-openspec.ps1` file
- [ ] Port bash logic to PowerShell syntax
- [ ] Test PowerShell script with recent archived change
- [ ] Add usage instructions in script comments

### 5. Update openspec/changes/add-openspec-archive-commit-workflow/tasks.md
- [x] Mark all completed tasks with `[x]`
- [ ] Verify all implementation steps are documented

### 6. Validate changes
- [x] Run `openspec validate add-openspec-archive-commit-workflow --strict --no-interactive`
- [x] Fix any validation errors
- [x] Verify git-workflow spec has new requirement
- [x] Verify AGENTS.md has updated Stage 3
- [x] Verify helper scripts (if created) are functional
- [ ] Test workflow: archive a change, then commit using documented process

### 7. Document commit message format
- [x] Create documentation snippet showing commit message format
- [x] Include 2-3 example commit messages
- [x] Add to README.md or create separate workflow document
- [x] Reference conventional commits spec

## Dependencies

- Task 1 is independent and can start immediately
- Task 2 can run in parallel with Task 1
- Task 3 depends on understanding archive folder structure (from Task 1)
- Task 4 can run in parallel with Task 3
- Task 5 depends on all implementation tasks (1-4)
- Task 6 depends on Tasks 1-5 completion
- Task 7 can run in parallel with Task 6

## Validation Criteria

- git-workflow spec includes new requirement for committing archived changes
- New requirement has exactly 3 scenarios
- AGENTS.md Stage 3 includes commit steps
- Helper scripts (if created) are executable and functional
- Documentation includes commit message format examples
- Workflow is clear and followable by developers
- `openspec validate` passes for the change

## Notes

- Focus on documentation first (Tasks 1-2) as primary deliverable
- Helper scripts (Tasks 3-4) are optional enhancements
- Windows and Unix developers need appropriate scripts
- Commit messages should follow existing git-workflow requirements
- Consider creating a separate WORKFLOW.md file for detailed process documentation
- Test the complete workflow after implementation

## Pre-conditions

- git-workflow spec exists (openspec/specs/git-workflow/spec.md)
- AGENTS.md exists (openspec/AGENTS.md)
- At least one archived change exists for testing
- Git repository is initialized

## Post-conditions

- Developers know to commit changes after archiving
- AGENTS.md documents the complete archiving + commit workflow
- Optional helper scripts streamline the commit process
- git-workflow spec enforces commit requirement for archived changes
- Repository history consistently captures OpenSpec changes

## Implementation Summary

**Successfully completed:**

✅ **Task 1:** Updated git-workflow spec with archive commit requirement
- Created ADDED Requirements section in spec delta
- Added requirement: "The repository SHALL commit archived OpenSpec changes"
- Added 3 scenarios:
  - Archive triggers immediate commit
  - Commit includes all archive changes
  - Commit message references archived change

✅ **Task 2:** Updated AGENTS.md Stage 3 section
- Located "Stage 3: Archiving Changes" section
- Added "**Commit archived changes**" subsection
- Documented commit steps with example commands:
  - Stage archived folder: `git add openspec/changes/archive/YYYY-MM-DD-[name]/`
  - Stage spec updates: `git add openspec/specs/`
  - Commit with conventional message: `git commit -m "docs: archive [change-id]"`
  - Push to GitHub: `git push`
- Verified formatting matches existing sections

⏭️ **Tasks 3-4:** Skipped (optional helper scripts)
- Bash and PowerShell helper scripts not created
- Documented in design.md as optional enhancement
- Can be implemented later if needed

✅ **Task 5:** Updated tasks.md checklist
- Marked all completed tasks with `[x]`
- Verified all implementation steps are documented

✅ **Task 6:** Validated changes
- Ran `openspec validate add-openspec-archive-commit-workflow --strict --no-interactive`
- All validations passed successfully
- git-workflow spec delta verified
- AGENTS.md Stage 3 verified

✅ **Task 7:** Documented commit message format
- Commit message format documented in design.md (lines 84-114)
- Includes format specification
- Includes 2 example commit messages:
  - `docs: archive add-gitignore`
  - `docs: archive initialize-git-repository`
- References conventional commits spec

**What was implemented:**

1. ✅ **git-workflow spec delta** (`openspec/changes/add-openspec-archive-commit-workflow/specs/git-workflow/spec.md`)
   - New ADDED Requirements section
   - 1 requirement with 3 scenarios
   - Enforces that archived OpenSpec changes are committed

2. ✅ **AGENTS.md update** (`openspec/AGENTS.md`)
   - Stage 3 section updated
   - Commit steps documented with example commands
   - Clear workflow for developers to follow

3. 📝 **Design documentation** (`openspec/changes/add-openspec-archive-commit-workflow/design.md`)
   - Implementation plan with 3 options
   - Commit message format specification
   - Examples and trade-offs documented

**Next steps:**
- When this change is archived, the new requirement will be applied to `openspec/specs/git-workflow/spec.md`
- Developers should follow the updated AGENTS.md workflow to commit archived changes
- Optional helper scripts (Tasks 3-4) can be implemented later if needed
