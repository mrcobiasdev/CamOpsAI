# frame-processing-queue Specification

## Purpose
TBD - created by archiving change clear-queue-on-startup. Update Purpose after archive.
## Requirements
### Requirement: Queue Statistics Reset
The system SHALL provide a method to reset processing queue statistics and SHALL automatically reset them when the application starts.

#### Scenario: Reset queue statistics on application startup
- **GIVEN** the application is starting
- **WHEN** the FrameQueue is initialized
- **THEN** `_processed_count` shall be set to 0
- **AND** `_dropped_count` shall be set to 0
- **AND** `clear()` method shall be called explicitly

#### Scenario: Clear method resets counters
- **GIVEN** a FrameQueue has processed 100 frames and dropped 5 frames
- **WHEN** `clear()` is called
- **THEN** `_processed_count` shall be 0
- **AND** `_dropped_count` shall be 0
- **AND** queue size shall remain unchanged
- **AND** worker status shall remain unchanged

#### Scenario: Clear method can be called during runtime
- **GIVEN** the application is running and has processed frames
- **WHEN** an administrator calls `frame_queue.clear()` via API or admin endpoint
- **THEN** `_processed_count` shall reset to 0
- **AND** `_dropped_count` shall reset to 0
- **AND** queue shall continue processing new frames normally
- **AND** existing frames in queue shall not be affected

#### Scenario: Clear method does not affect queue content
- **GIVEN** a FrameQueue contains 10 frames waiting to be processed
- **WHEN** `clear()` is called
- **THEN** the 10 frames shall remain in the queue
- **AND** workers shall continue processing the frames
- **AND** only the counters shall be reset

### Requirement: Queue Statistics Tracking
The system SHALL track and report queue statistics for monitoring and debugging.

#### Scenario: Track processed frame count
- **GIVEN** a FrameQueue is processing frames
- **WHEN** a frame is successfully processed
- **THEN** `_processed_count` shall increment by 1
- **AND** the counter shall be accessible via `processed_count` property
- **AND** the counter shall be included in `get_stats()` output

#### Scenario: Track dropped frame count
- **GIVEN** a FrameQueue is at maximum capacity
- **WHEN** a new frame is attempted to be added
- **THEN** the frame shall be dropped
- **AND** `_dropped_count` shall increment by 1
- **AND** a warning shall be logged
- **AND** the counter shall be accessible via `dropped_count` property

#### Scenario: Get stats includes all counters
- **GIVEN** a FrameQueue has processed 50 frames and dropped 3 frames
- **WHEN** `get_stats()` is called
- **THEN** the returned dict shall contain `processed` = 50
- **AND** the returned dict shall contain `dropped` = 3
- **AND** the returned dict shall contain `queue_size`
- **AND** the returned dict shall contain `max_size`
- **AND** the returned dict shall contain `workers`
- **AND** the returned dict shall contain `running`

### Requirement: Queue Initialization
The system SHALL initialize the processing queue with proper default configuration.

#### Scenario: Initialize queue with default values
- **GIVEN** a FrameQueue is created without specifying max_size
- **WHEN** `__init__()` completes
- **THEN** `max_size` shall default to `settings.max_queue_size`
- **AND** `_processed_count` shall be 0
- **AND** `_dropped_count` shall be 0
- **AND** `_running` shall be False
- **AND** `_workers` shall be an empty list

#### Scenario: Initialize queue with custom max_size
- **GIVEN** a FrameQueue is created with `max_size` = 200
- **WHEN** `__init__()` completes
- **THEN** `max_size` shall be 200
- **AND** the internal `asyncio.Queue` shall have `maxsize` = 200
- **AND** all other initialization shall proceed normally

#### Scenario: Initialize queue with processor and workers
- **GIVEN** a FrameQueue is created with `processor` = process_frame and `num_workers` = 4
- **WHEN** `__init__()` completes
- **THEN** `_processor` shall be set to the provided processor function
- **AND** `_num_workers` shall be 4
- **AND** workers shall not start until `start_workers()` is called

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

