# git-workflow Specification

## Purpose
TBD - created by archiving change initialize-git-repository. Update Purpose after archive.
## Requirements
### Requirement: The repository SHALL be initialized with a structured commit history

The repository SHALL be initialized with multiple logical commits that group related changes together, following conventional commit message format.

#### Scenario: Initial project structure commit contains core files
- **GIVEN** project is ready to be committed
- **WHEN** creating initial commit
- **THEN** commit shall include README.md, requirements.txt, src/, tests/, tools/, docs/, and alembic/
- **AND** commit message shall follow conventional commits format with "feat:" prefix
- **AND** commit shall provide a clear description of project capabilities

#### Scenario: .gitignore commit is separate from initial commit
- **GIVEN** .gitignore file has been created
- **WHEN** creating .gitignore commit
- **THEN** commit shall contain only .gitignore file
- **AND** commit message shall use "chore:" prefix
- **AND** commit message shall describe what patterns are being excluded

#### Scenario: OpenSpec changes are committed separately
- **GIVEN** openspec specs and archived changes exist
- **WHEN** creating openspec-related commits
- **THEN** archived changes shall be committed with "feat:" prefix
- **AND** spec files shall be committed with "feat:" prefix
- **AND** commit messages shall clearly describe the capability added

### Requirement: The repository SHALL follow conventional commit message format

The repository SHALL follow conventional commits format (type: subject) with descriptive body text for all commits.

#### Scenario: Commit message uses type prefix
- **GIVEN** a developer creates a commit
- **WHEN** writing the commit message
- **THEN** message shall start with one of: feat, fix, docs, style, refactor, test, or chore
- **AND** type shall be followed by a colon and space
- **AND** subject shall be in lowercase and not end with a period

#### Scenario: Commit message includes descriptive body
- **GIVEN** a commit includes significant changes
- **WHEN** writing the commit message
- **THEN** message body shall provide additional context
- **AND** body shall explain why the change was made
- **AND** body may list bullet points for clarity

### Requirement: The repository SHALL not commit sensitive files

The repository SHALL ensure that sensitive files containing credentials, API keys, or secrets are never committed to version control.

#### Scenario: .env file is excluded from commits
- **GIVEN** a developer creates a .env file with credentials
- **WHEN** running git status or attempting to commit
- **THEN** the .env file shall not appear in tracked or staged files
- **AND** the .gitignore pattern for .env shall prevent it from being committed

#### Scenario: .env.example is committed as template
- **GIVEN** the project requires environment configuration
- **WHEN** committing .env.example
- **THEN** the .env.example file shall be committed to the repository
- **AND** the file shall contain placeholder values without real credentials
- **AND** the file shall serve as a template for .env creation

### Requirement: The repository SHALL be pushed to GitHub remote

The repository SHALL be configured with a remote GitHub origin and all local commits shall be pushed to establish the remote repository.

#### Scenario: Remote origin is configured
- **GIVEN** a GitHub repository URL is available
- **WHEN** setting up the remote
- **THEN** git remote add origin shall be used with the repository URL
- **AND** the remote shall be named "origin"

#### Scenario: Initial commits are pushed to main branch
- **GIVEN** all local commits have been created
- **WHEN** pushing to the remote repository
- **THEN** git push -u origin main shall be used
- **AND** the --set-upstream flag shall track the main branch
- **AND** all local commits shall be uploaded to GitHub

## ADDED Requirements

### Requirement: The repository SHALL commit archived OpenSpec changes

The repository SHALL ensure that when OpenSpec changes are archived, the resulting file changes are committed to Git with conventional commit messages.

#### Scenario: Archive triggers immediate commit
- **GIVEN** a developer archives a change using `openspec archive <id>`
- **WHEN** the archive command completes successfully
- **THEN** the developer SHALL commit the archived change and spec updates
- **AND** the commit message SHALL follow conventional commits format
- **AND** the commit message SHALL describe the change that was archived

#### Scenario: Commit includes all archive changes
- **GIVEN** a change has been archived
- **WHEN** creating a commit
- **THEN** the commit SHALL include the archived folder in `changes/archive/`
- **AND** the commit SHALL include any spec updates in `specs/`
- **AND** the commit SHA SHALL match the archive date

#### Scenario: Commit message references archived change
- **GIVEN** an archived change is being committed
- **WHEN** writing the commit message
- **THEN** the commit message SHALL use "docs:" or "chore:" prefix
- **AND** the subject SHALL include the change ID
- **AND** the body SHALL describe what capability was added or modified
