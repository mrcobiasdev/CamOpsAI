## ADDED Requirements

This spec delta adds configuration for discarding initial frames after camera connection.

### Requirement: Initial Frames Discard Configuration

The system SHALL provide a global environment variable to configure the number of initial frames to discard after camera connection.

#### Scenario: Environment variable sets initial frames to discard
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 10 in `.env`
- **WHEN** the application starts
- **THEN** `settings.initial_frames_to_discard` shall equal 10
- **AND** cameras shall discard 10 frames after each successful connection

#### Scenario: Default value for initial frames discard
- **GIVEN** `.env` does not contain `INITIAL_FRAMES_TO_DISCARD`
- **WHEN** the application starts
- **THEN** `settings.initial_frames_to_discard` shall default to 5
- **AND** cameras shall discard 5 frames after each successful connection

#### Scenario: Zero value disables frame discarding
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 0 in `.env`
- **WHEN** the application starts
- **THEN** `settings.initial_frames_to_discard` shall equal 0
- **AND** cameras shall not discard any frames after connection
- **AND** frame processing shall begin immediately

#### Scenario: Negative value treated as zero
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to -1 in `.env`
- **WHEN** the application starts
- **THEN** the system shall treat the value as 0
- **AND** cameras shall not discard any frames after connection

#### Scenario: Validation ensures non-negative value
- **GIVEN** settings validation is performed
- **WHEN** `INITIAL_FRAMES_TO_DISCARD` is set to -5
- **THEN** the system shall validate that the value is >= 0
- **AND** shall reject negative values or treat them as 0
