## ADDED Requirements

This spec delta adds requirements for discarding initial frames after camera connection and reconnection to allow stream stabilization.

### Requirement: Initial Frame Discard on Connection

The system SHALL discard a configurable number of initial frames after establishing a successful camera connection to allow the RTSP stream to stabilize.

#### Scenario: Discard frames after initial connection
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 5
- **WHEN** a camera connects for the first time
- **THEN** the system shall discard the first 5 frames after successful connection
- **AND** discarded frames shall be used to stabilize motion detector baseline
- **AND** frame processing shall not begin until discard period completes
- **AND** each discarded frame shall be logged at DEBUG level
- **AND** `initial_frames_discarded` counter shall be incremented for each frame

#### Scenario: Discard frames after reconnection
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 5
- **AND** camera has disconnected due to errors
- **WHEN** camera successfully reconnects
- **THEN** the system shall discard the first 5 frames after successful reconnection
- **AND** discarded frames shall be used to stabilize motion detector baseline
- **AND** frame processing shall not begin until discard period completes
- **AND** each discarded frame shall be logged at DEBUG level
- **AND** `initial_frames_discarded` counter shall be incremented for each frame

#### Scenario: Failed frame read during discard period
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 5
- **AND** frame read fails during discard period
- **WHEN** the failure occurs
- **THEN** the system shall log the failure at DEBUG level
- **AND** shall continue to the next frame discard iteration
- **AND** shall not block the connection process

#### Scenario: Discard count is zero
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 0
- **WHEN** a camera connects
- **THEN** the system shall not discard any frames
- **AND** frame processing shall begin immediately
- **AND** `initial_frames_discarded` counter shall remain 0

#### Scenario: Discard log shows progress
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 5
- **AND** logger level is set to DEBUG
- **WHEN** frames are being discarded after connection
- **THEN** each discarded frame shall be logged with message containing:
  - Frame number (e.g., "Discarded initial frame 1/5")
  - Camera name
- **AND** log level shall be DEBUG

#### Scenario: Discard counter tracks total discarded
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 5
- **AND** camera connects and discards 5 frames
- **AND** camera later reconnects and discards another 5 frames
- **WHEN** statistics are queried
- **THEN** `initial_frames_discarded` shall equal 10
- **AND** counter shall be reset to 0 on next manual reset

#### Scenario: Discard completes successfully
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 5
- **WHEN** all 5 frames are discarded after connection
- **THEN** the system shall log "Discarded 5 initial frames for camera {name} (stream stabilization + motion detector baseline)"
- **AND** normal frame processing shall resume
- **AND** motion detector shall have a stable baseline for subsequent frames
- **AND** motion detection shall work normally on subsequent frames

#### Scenario: Connection status during discard
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 5
- **WHEN** frames are being discarded after connection
- **THEN** camera status shall remain CONNECTED during discard period
- **AND** camera status shall transition to CAPTURING only when processing begins

#### Scenario: Discard applies to all cameras equally
- **GIVEN** multiple cameras are configured
- **AND** `INITIAL_FRAMES_TO_DISCARD` is set to 5
- **WHEN** each camera connects or reconnects
- **THEN** all cameras shall discard 5 initial frames
- **AND** the behavior shall be consistent across all cameras
