## ADDED Requirements

This spec delta adds tracking for initial frames discarded during camera connection.

### Requirement: Initial Frames Discarded Tracking

The system SHALL track the number of initial frames discarded during camera connection and include this information in camera statistics.

#### Scenario: Camera status includes discarded frame count
- **GIVEN** a camera has connected and discarded 5 initial frames
- **WHEN** GET `/api/v1/cameras/{id}/status` is called
- **THEN** the response shall include `initial_frames_discarded` = 5
- **AND** the value shall be an integer >= 0

#### Scenario: Discard counter increments with each discard
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 5
- **WHEN** frames are discarded after connection
- **THEN** `initial_frames_discarded` shall increment by 1 for each frame
- **AND** after 5 frames, the counter shall equal 5

#### Scenario: Discard counter resets on connection
- **GIVEN** a camera has `initial_frames_discarded` = 10 from previous connections
- **WHEN** the camera connects again and discards 5 frames
- **THEN** `initial_frames_discarded` shall be reset to 0 at start of connection
- **AND** shall increment to 5 during the discard period

#### Scenario: Zero frames discarded shows zero counter
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 0
- **WHEN** camera connects
- **THEN** `initial_frames_discarded` shall equal 0
- **AND** the value shall be visible in camera status endpoint

#### Scenario: Discard counter does not affect other statistics
- **GIVEN** a camera has discarded 5 initial frames
- **AND** has captured 10 frames for processing
- **WHEN** statistics are queried
- **THEN** `initial_frames_discarded` shall be 5
- **AND** `frames_captured` shall be 10
- **AND** the counters shall be independent
- **AND** `initial_frames_discarded` shall not be included in `frames_captured`

#### Scenario: Multiple connections accumulate discarded count
- **GIVEN** `INITIAL_FRAMES_TO_DISCARD` is set to 5
- **AND** camera connects and discards 5 frames (counter = 5)
- **AND** camera reconnects and discards another 5 frames (counter = 10)
- **WHEN** camera status is queried
- **THEN** `initial_frames_discarded` shall equal 10
- **AND** the counter shall reflect total discarded since last reset
