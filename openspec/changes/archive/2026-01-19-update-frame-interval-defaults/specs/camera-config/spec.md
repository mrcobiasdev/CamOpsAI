# Spec Delta: Camera Configuration

## ADDED Requirements

### Requirement: Global Frame Interval Default
The system SHALL use the `FRAME_INTERVAL_SECONDS` environment variable as the global default interval for new cameras when no per-camera interval is specified.

#### Scenario: New camera without explicit interval uses global default
- **GIVEN** `FRAME_INTERVAL_SECONDS` is set to 120 in `.env`
- **WHEN** a new camera is created without specifying `frame_interval`
- **THEN** the camera shall use 120 seconds as the capture interval
- **AND** the database shall store `frame_interval` as 120

#### Scenario: Existing camera keeps its interval
- **GIVEN** a camera exists with `frame_interval` = 30
- **WHEN** `FRAME_INTERVAL_SECONDS` is changed to 120 in `.env`
- **THEN** the existing camera shall continue using 30 seconds
- **AND** the capture interval shall not change for existing cameras

#### Scenario: Camera created with explicit interval overrides global default
- **GIVEN** `FRAME_INTERVAL_SECONDS` is set to 120 in `.env`
- **WHEN** a new camera is created with `frame_interval` = 60
- **THEN** the camera shall use 60 seconds as the capture interval
- **AND** the database shall store `frame_interval` as 60

### Requirement: Per-Camera Interval Persistence
The system SHALL store and use the per-camera `frame_interval` value from the database, ignoring the global default for cameras that already have an interval set.

#### Scenario: Camera loaded from database uses stored interval
- **GIVEN** a camera in the database has `frame_interval` = 45
- **WHEN** the camera is loaded at application startup
- **THEN** the camera configuration shall use 45 seconds
- **AND** the capture loop shall wait 45 seconds between frames
- **REGARDLESS** of `FRAME_INTERVAL_SECONDS` value in `.env`

### Requirement: Settings Integration
The system SHALL read `FRAME_INTERVAL_SECONDS` from environment at application startup and make it available as `settings.frame_interval_seconds` to all components.

#### Scenario: Settings loads from .env
- **GIVEN** `.env` contains `FRAME_INTERVAL_SECONDS=120`
- **WHEN** the application starts
- **THEN** `settings.frame_interval_seconds` shall equal 120
- **AND** the value shall be accessible in `CameraConfig` and API schemas

#### Scenario: Missing env variable uses code default
- **GIVEN** `.env` does not contain `FRAME_INTERVAL_SECONDS`
- **WHEN** the application starts
- **THEN** `settings.frame_interval_seconds` shall default to 10
- **AND** new cameras shall use 10 seconds as interval
