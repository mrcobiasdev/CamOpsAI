# frame-processing-queue Specification

## Purpose
Manage the asynchronous processing queue for captured frames, including queue size limits, worker management, and statistics tracking.

## ADDED Requirements

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
