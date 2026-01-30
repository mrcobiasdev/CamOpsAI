# documentation Specification

## Purpose
TBD - created by archiving change reorganize-documentation. Update Purpose after archive.
## Requirements
### Requirement: Documentation Structure

The system SHALL maintain a structured documentation hierarchy under `/docs/` with clear categorization by purpose and audience.

#### Scenario: Organized documentation folders

- **WHEN** a developer or user accesses the `/docs/` directory
- **THEN** they SHALL find documentation organized into the following subdirectories:
  - `overview/` - Project overview, introduction, and getting started guides
  - `architecture/` - System architecture, design, and component documentation
  - `features/` - Detailed feature-specific documentation (motion detection, WhatsApp, etc.)
  - `guides/` - User guides, tutorials, and troubleshooting information
  - `development/` - Developer documentation (API reference, implementation notes)
  - `appendix/` - Appendices, changelog, and reference materials

#### Scenario: Clear file organization

- **WHEN** looking for specific information
- **THEN** users SHALL be able to locate files based on their category (overview, architecture, features, guides, development, or appendix)
- **AND** each directory SHALL contain only relevant files for that category

### Requirement: README as Academic Report

The root `README.md` file SHALL follow academic technical report format suitable for course project submission.

#### Scenario: Academic report structure

- **WHEN** opening README.md
- **THEN** the file SHALL contain the following sections in order:
  1. Title (academic format)
  2. Abstract (project summary in 1-2 paragraphs)
  3. Keywords (5-7 relevant keywords)
  4. Introduction (context, problem statement, objectives)
  5. Methodology (tools used: OpenCode, OpenSpec; workflow description)
  6. System Architecture (overview, components, Mermaid diagram)
  7. Implementation (key features, algorithms, technical details)
  8. Results and Evaluation
  9. Limitations and Future Work
  10. Conclusions
  11. References (internal and external links)
  12. Documentation Map (table of all documentation files)
  13. Change Traceability (list of file moves and renames)

#### Scenario: Formal academic tone

- **WHEN** reading README.md
- **THEN** the language SHALL be formal and objective
- **AND** technical terminology SHALL be used correctly
- **AND** the tone SHALL be appropriate for academic submission

### Requirement: OpenCode and OpenSpec Documentation

The README.md SHALL document the use of OpenCode and OpenSpec tools in the project, explaining their purpose and workflow.

#### Scenario: OpenCode documentation

- **WHEN** reading the Methodology section
- **THEN** readers SHALL find:
  - What OpenCode is (AI coding assistant)
  - Why it was used (to accelerate development, handle complex tasks)
  - How it was used (through CLI interactions for code generation, refactoring, debugging)
  - Examples of prompts and interactions

#### Scenario: OpenSpec documentation

- **WHEN** reading the Methodology section
- **THEN** readers SHALL find:
  - What OpenSpec is (spec-driven development workflow)
  - Why it was used (to maintain structured proposals, track changes, ensure quality)
  - How it was used (proposal creation, spec deltas, archiving)
  - The three-stage workflow: Creating Changes, Implementing Changes, Archiving Changes

### Requirement: Archived Proposals Summary

The documentation SHALL include a summary of all archived OpenSpec proposals showing project evolution and key decisions.

#### Scenario: Proposals summary table

- **WHEN** accessing `docs/appendix/archived-proposals-summary.md`
- **THEN** readers SHALL find a table with columns:
  - Proposal ID (e.g., 2026-01-20-implement-motion-detection)
  - Date (YYYY-MM-DD)
  - Title (brief description)
  - Status (Implemented, Partially Implemented, Cancelled, Superseded)
  - Reason for Archive (completed, superseded, no longer relevant)

#### Scenario: Proposal descriptions

- **WHEN** reading archived-proposals-summary.md
- **THEN** each proposal SHALL have:
  - Brief description of what was proposed
  - Key implementation details
  - Impact on the project
  - Reason for archival status

### Requirement: Documentation Map

The README.md SHALL include a complete documentation map table listing all documentation files with their type, purpose, and status.

#### Scenario: Complete documentation map

- **WHEN** reading the Documentation Map section
- **THEN** the table SHALL include for each file:
  - File path (e.g., `docs/features/motion-detection.md`)
  - Type (guide, reference, tutorial, specification, etc.)
  - Objective (what the document covers)
  - Status (current, updated, new, archived)

#### Scenario: Map comprehensiveness

- **WHEN** checking the Documentation Map
- **THEN** it SHALL include ALL files in the `/docs/` directory
- **AND** it SHALL be kept synchronized with actual file structure

### Requirement: Change Traceability

The README.md SHALL include a Change Traceability section documenting all file moves, renames, and consolidations performed during documentation reorganization.

#### Scenario: File move tracking

- **WHEN** reading the Change Traceability section
- **THEN** readers SHALL find a list of all file operations:
  - Original path → New path
  - Consolidation operations (multiple files → single file)
  - Files removed (reason provided)

#### Scenario: Clear traceability

- **WHEN** verifying documentation changes
- **THEN** each file operation SHALL be documented with:
  - Source and destination paths
  - Type of operation (move, rename, consolidate, remove)
  - Reason for the operation

### Requirement: Internal Link Integrity

All internal markdown links SHALL work correctly after documentation reorganization.

#### Scenario: Link validation

- **WHEN** documentation is reorganized
- **THEN** all internal links SHALL be updated to point to new file locations
- **AND** no broken links SHALL remain

#### Scenario: Cross-references

- **WHEN** documentation references other documentation
- **THEN** all cross-references SHALL use correct paths
- **AND** clicking links SHALL navigate to the intended content

### Requirement: Content Preservation

All information from existing documentation SHALL be preserved during reorganization and consolidation.

#### Scenario: No information loss

- **WHEN** consolidating multiple files
- **THEN** all important information SHALL be retained in the consolidated document
- **AND** no technical details, instructions, or examples SHALL be lost

#### Scenario: Content verification

- **WHEN** reorganization is complete
- **THEN** a comparison SHALL show that all original content is present
- **AND** no information has been accidentally deleted

