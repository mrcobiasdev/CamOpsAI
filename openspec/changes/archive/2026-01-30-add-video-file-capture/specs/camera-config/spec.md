# camera-config Specification Delta

## ADDED Requirements

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
