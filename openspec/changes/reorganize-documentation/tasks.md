## 1. Inventory and Analysis

- [x] 1.1 Create complete inventory of `/docs` with file sizes and line counts
- [x] 1.2 Create complete inventory of `/openspec/changes/archive` with proposal dates and titles
- [x] 1.3 Identify overlapping content between documentation files
- [x] 1.4 Identify missing information or gaps in documentation
- [x] 1.5 Analyze current README.md structure and content

## 2. Design New Documentation Structure

- [x] 2.1 Define final folder structure for `/docs`
- [x] 2.2 Map each existing file to its new location
- [x] 2.3 Identify files to be consolidated vs moved
- [x] 2.4 Identify files to be removed (fully integrated elsewhere)
- [x] 2.5 Design documentation map table format

## 3. Create New Directory Structure

- [x] 3.1 Create `docs/overview/` directory
- [x] 3.2 Create `docs/architecture/` directory
- [x] 3.3 Create `docs/features/` directory
- [x] 3.4 Create `docs/guides/` directory
- [x] 3.5 Create `docs/development/` directory
- [x] 3.6 Create `docs/appendix/` directory

## 4. Read and Analyze Archived Proposals

- [x] 4.1 Read all 12 archived proposals (2026-01-19 to 2026-01-30)
- [x] 4.2 Extract key information: title, date, purpose, implementation details
- [x] 4.3 Determine status (implemented/partially implemented/archived)
- [x] 4.4 Identify reason for archival (completed, superseded, cancelled)
- [x] 4.5 Create summary table with all proposals

## 5. Consolidate Documentation Files

- [x] 5.1 Consolidate motion detection files:
  - Read: MOTION_DETECTION.md, MOTION_DETECTION_FIX.md, DIAGNOSTICO_MOTION_SCORE_ZERO.md, IMPLEMENTACAO_THRESHOLD_HOT_RELOAD.md
  - Create unified `docs/features/motion-detection.md`
- [x] 5.2 Consolidate WhatsApp files:
  - Read: WHATSAPP_SESSION_PERSISTENCE.md
  - Extract relevant WhatsApp sections from README.md
  - Create unified `docs/features/whatsapp-notifications.md`
- [x] 5.3 Consolidate troubleshooting files:
  - Read: TROUBLESHOOTING.md, BUG_FIX_FLUSH_VS_COMMIT.md, IMPLEMENTACAO_PERSISTENCIA.md
  - Extract troubleshooting sections from README.md
  - Create unified `docs/guides/troubleshooting.md`
- [x] 5.4 Extract content for `docs/overview/project-overview.md` from README.md
- [x] 5.5 Extract content for `docs/overview/getting-started.md` from README.md installation sections
- [x] 5.6 Extract content for `docs/architecture/system-architecture.md` from README.md
- [x] 5.7 Extract content for `docs/development/api-reference.md` from README.md API sections
- [x] 5.8 Extract content for `docs/features/video-file-capture.md` from README.md video file section
- [x] 5.9 Extract calibration guide from MOTION_DETECTION.md tools section to `docs/guides/calibration-guide.md`
- [x] 5.10 Move CHANGELOG.md to `docs/appendix/changelog.md`

## 6. Create Archived Proposals Summary

- [x] 6.1 Create `docs/appendix/archived-proposals-summary.md`
- [x] 6.2 Add introduction explaining openspec workflow
- [x] 6.3 Create summary table with all proposals (ID, date, title, status, reason)
- [x] 6.4 Add brief descriptions of key proposals and their impact
- [x] 6.5 Add conclusion about project evolution through proposals

## 7. Transform README.md

- [x] 7.1 Add title in academic format
- [x] 7.2 Add abstract section (project summary)
- [x] 7.3 Add keywords section
- [x] 7.4 Add introduction/context section (problem, objectives)
- [x] 7.5 Add methodology section (OpenCode, OpenSpec, workflow explanation)
- [x] 7.6 Add system architecture section with Mermaid diagram
- [x] 7.7 Add implementation section (key features, algorithms)
- [x] 7.8 Add results and evaluation section
- [x] 7.9 Add limitations and future work section
- [x] 7.10 Add conclusions section
- [x] 7.11 Add references section (internal and external links)
- [x] 7.12 Add documentation map table
- [x] 7.13 Add change traceability section (list of file moves/renames)

## 8. Update Internal Links

- [x] 8.1 Update all internal links in new documentation files
- [x] 8.2 Update links in README.md to point to new documentation structure
- [x] 8.3 Verify no broken links remain
- [x] 8.4 Test links manually or with link checker

## 9. Validation

- [x] 9.1 Verify all information is preserved (no content loss)
- [x] 9.2 Verify new folder structure is complete
- [x] 9.3 Verify README.md follows academic report format
- [x] 9.4 Verify archived proposals summary is accurate
- [x] 9.5 Verify all internal links work
- [x] 9.6 Verify documentation map table is complete
- [x] 9.7 Verify change traceability section lists all changes

## 10. Cleanup

- [x] 10.1 Remove old documentation files that have been consolidated
- [x] 10.2 Verify `/docs` root is clean (only subdirectories remain)
- [x] 10.3 Commit changes with appropriate message
- [x] 10.4 Create summary of commits and changes made
