# camera-config Specification

## Purpose
TBD - created by archiving change update-frame-interval-defaults. Update Purpose after archive.
## Requirements
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

### Requirement: Motion Sensitivity Configuration Storage
The system SHALL persist motion sensitivity settings per camera in the database and load them at runtime.

#### Scenario: New camera without explicit sensitivity uses global default
- **GIVEN** a new camera is created without specifying motion_sensitivity
- **WHEN** the camera is saved to the database
- **THEN** motion_sensitivity shall default to "medium"
- **AND** the database shall store motion_sensitivity as "medium"

#### Scenario: Camera created with explicit sensitivity stores value
- **GIVEN** a new camera is created with motion_sensitivity = "high"
- **WHEN** the camera is saved to the database
- **THEN** the database shall store motion_sensitivity as "high"
- **AND** MotionDetector shall use high sensitivity parameters

#### Scenario: Camera loaded from database uses stored sensitivity
- **GIVEN** a camera in the database has motion_sensitivity = "low"
- **WHEN** the camera is loaded at application startup
- **THEN** CameraConfig shall include motion_sensitivity = "low"
- **AND** MotionDetector shall be initialized with low sensitivity preset

#### Scenario: Update camera sensitivity persists to database
- **GIVEN** an existing camera with motion_sensitivity = "medium"
- **WHEN** sensitivity is updated to "high" via API or CLI
- **THEN** database shall be updated with new value
- **AND** hot-reload shall apply changes immediately
- **AND** value shall persist across application restarts

#### Scenario: Sensitivity field allows only valid values
- **GIVEN** an attempt to set motion_sensitivity
- **WHEN** value is not in ["low", "medium", "high", "custom"]
- **THEN** database constraint shall reject the value
- **AND** error message shall indicate valid options
- **AND** camera configuration shall remain unchanged

#### Scenario: Migration adds sensitivity field to existing cameras
- **GIVEN** existing cameras in database without motion_sensitivity field
- **WHEN** database migration is applied
- **THEN** all cameras shall have motion_sensitivity = "medium" added
- **AND** existing cameras shall maintain all other settings unchanged
- **AND** motion detection behavior shall improve with new default parameters

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

### Requirement: Camera Source Type
The system SHALL support multiple camera source types with a `source_type` field to distinguish between different input sources.

#### Scenario: Create RTSP camera with default source type
- **GIVEN** a new camera is created with an RTSP URL (rtsp://)
- **WHEN** the camera is saved to the database
- **THEN** `source_type` shall default to "rtsp"
- **AND** the system shall process frames from the RTSP stream

#### Scenario: Create video file camera with explicit source type
- **GIVEN** a new camera is created with a video file path and `source_type` = "video_file"
- **WHEN** the camera is saved to the database
- **THEN** `source_type` shall be stored as "video_file"
- **AND** the system shall process frames from the video file

#### Scenario: Auto-detect source type from URL
- **GIVEN** a new camera is created with a URL without specifying `source_type`
- **WHEN** the URL starts with "rtsp://" or "rtmp://"
- **THEN** `source_type` shall be set to "rtsp"
- **WHEN** the URL ends with video extensions (.mp4, .avi, .mov, .mkv, .webm)
- **THEN** `source_type` shall be set to "video_file"

#### Scenario: Invalid source type is rejected
- **GIVEN** an attempt to create a camera with `source_type` not in ["rtsp", "video_file"]
- **WHEN** validation is performed
- **THEN** the system shall reject the configuration
- **AND** error message shall indicate valid options

### Requirement: Video File Validation
The system SHALL validate video file paths before creating a video file camera source.

#### Scenario: Validate video file exists
- **GIVEN** a new camera is created with `source_type` = "video_file"
- **WHEN** the file path is validated
- **THEN** the system shall check if the file exists at the specified path
- **AND** if file does not exist, reject creation with error "Video file not found"

#### Scenario: Validate video file is readable
- **GIVEN** a video file camera is created
- **WHEN** the system validates the file
- **THEN** the system shall attempt to open the video file with OpenCV
- **AND** if file cannot be opened, reject creation with error "Invalid video file format"

#### Scenario: Validate video file extension
- **GIVEN** a new camera is created with `source_type` = "video_file"
- **WHEN** the file path extension is checked
- **THEN** the system shall accept extensions: .mp4, .avi, .mov, .mkv, .webm, .flv, .m4v
- **AND** if extension is not supported, reject creation with error listing valid formats

### Requirement: Video File Path Configuration
The system SHALL store and use the file system path for video file camera sources.

#### Scenario: Store absolute video file path
- **GIVEN** a camera is created with `source_type` = "video_file" and relative path
- **WHEN** the camera is saved to the database
- **THEN** the system shall convert relative path to absolute path
- **AND** the absolute path shall be stored in the database

#### Scenario: Support environment variables in video file paths
- **GIVEN** a camera is created with `source_type` = "video_file" and path containing ${VAR}
- **WHEN** the camera configuration is loaded
- **THEN** the system shall expand environment variables in the path
- **AND** the expanded path shall be used for video processing

### Requirement: Video File Camera Lifecycle
The system SHALL handle video file camera lifecycle differently from RTSP cameras (no reconnection, stop on end).

#### Scenario: Stop camera when video file ends
- **GIVEN** a video file camera is capturing frames
- **WHEN** the video reaches the end of file
- **THEN** the capture shall stop gracefully
- **AND** the camera status shall change to "disconnected"
- **AND** the system shall log "Video file completed: {path}"

#### Scenario: No reconnection for video files
- **GIVEN** a video file camera encounters an error mid-stream
- **WHEN** the error handler is invoked
- **THEN** the system shall NOT attempt to reconnect
- **AND** the camera shall stop with error status
- **AND** the system shall log error with video file path

#### Scenario: Video file camera supports pause/resume
- **GIVEN** a video file camera is currently capturing
- **WHEN** camera is stopped via API call
- **THEN** capture shall pause at current position
- **WHEN** camera is started again
- **THEN** capture shall resume from paused position
- **AND** playback shall continue from where it left off

