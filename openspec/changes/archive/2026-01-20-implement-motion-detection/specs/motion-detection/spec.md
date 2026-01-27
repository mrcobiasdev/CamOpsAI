# motion-detection Specification

## Purpose
Detect and filter frames with significant motion before LLM analysis to reduce API usage and improve efficiency.

## ADDED Requirements

### Requirement: Motion Detection Configuration
The system SHALL support per-camera motion detection configuration with `motion_detection_enabled` and `motion_threshold` fields.

#### Scenario: Create camera with default motion detection settings
- **GIVEN** a new camera is created without specifying motion detection settings
- **WHEN** the camera is saved to the database
- **THEN** `motion_detection_enabled` shall default to true
- **AND** `motion_threshold` shall default to 10.0 (10% pixel change)

#### Scenario: Create camera with custom motion threshold
- **GIVEN** a new camera is created with `motion_threshold` = 5.0
- **WHEN** the camera is saved to the database
- **THEN** the database shall store `motion_threshold` as 5.0
- **AND** the FrameGrabber shall use 5.0 as the threshold for that camera

#### Scenario: Disable motion detection for specific camera
- **GIVEN** an existing camera with `motion_detection_enabled` = true
- **WHEN** the camera is updated with `motion_detection_enabled` = false
- **THEN** all frames from that camera shall be sent to the LLM
- **AND** no motion filtering shall be applied

#### Scenario: Update motion threshold on running camera
- **GIVEN** a camera is currently capturing with `motion_threshold` = 10.0
- **WHEN** the camera is updated with `motion_threshold` = 5.0
- **THEN** the FrameGrabber shall use the new threshold immediately
- **AND** the next frame comparison shall use 5.0

### Requirement: Motion Detection Algorithm
The system SHALL use a hybrid motion detection algorithm combining pixel difference and background subtraction to detect significant frame changes.

#### Scenario: Static scene with no movement
- **GIVEN** a camera captures 10 consecutive frames of a static room
- **WHEN** the motion detector compares each frame
- **THEN** all frames except the first shall be filtered (motion_score < threshold)
- **AND** only the first frame shall be sent to the LLM

#### Scenario: Scene with person walking through
- **GIVEN** a camera captures frames of a room with a person walking
- **WHEN** the motion detector compares frames with movement
- **THEN** frames showing the person shall have motion_score >= threshold
- **AND** those frames shall be sent to the LLM

#### Scenario: Gradual lighting change (daylight transition)
- **GIVEN** a camera captures frames during sunrise
- **WHEN** the lighting gradually changes
- **THEN** background subtraction shall handle gradual changes
- **AND** frames shall not trigger motion detection unless movement occurs

#### Scenario: Sudden lighting change (light switch)
- **GIVEN** a camera captures frames with lights turned on/off
- **WHEN** sudden lighting change occurs
- **THEN** pixel difference method shall detect the change
- **AND** the frame may trigger motion detection (depending on threshold)

### Requirement: Frame Filtering Logic
The system SHALL filter frames based on motion detection results before queuing for LLM analysis.

#### Scenario: Frame below threshold is filtered
- **GIVEN** motion_threshold = 10.0
- **WHEN** a frame has motion_score = 3.5
- **THEN** the frame shall not be sent to the FrameQueue
- **AND** the system shall log "Frame filtered: motion_score=3.5, threshold=10.0"

#### Scenario: Frame above threshold is sent
- **GIVEN** motion_threshold = 10.0
- **WHEN** a frame has motion_score = 15.2
- **THEN** the frame shall be sent to the FrameQueue
- **AND** the system shall log "Frame sent: motion_score=15.2, threshold=10.0"

#### Scenario: First frame is always sent
- **GIVEN** a camera starts capturing with no previous frame
- **WHEN** the first frame is captured
- **THEN** the frame shall be sent to the FrameQueue regardless of motion
- **AND** the frame shall be stored as the baseline for comparison

#### Scenario: Camera reconnection resets baseline
- **GIVEN** a camera has been capturing with a stored baseline frame
- **WHEN** the camera reconnects after disconnection
- **THEN** the previous baseline shall be discarded
- **AND** the first frame after reconnection shall be sent as new baseline

### Requirement: Performance Overhead
The system SHALL detect motion with minimal overhead, adding less than 50ms processing time per frame.

#### Scenario: Motion detection timing
- **GIVEN** a frame is captured at resolution 1920x1080
- **WHEN** motion detection is performed
- **THEN** the frame shall be downsampled to 320x240 for detection
- **AND** total detection time shall be < 50ms
- **AND** memory usage shall be < 1MB per camera

#### Scenario: Multiple cameras simultaneous detection
- **GIVEN** 5 cameras are capturing simultaneously
- **WHEN** motion detection runs for all cameras
- **THEN** each camera shall process independently
- **AND** total overhead shall scale linearly with camera count

### Requirement: Statistics Tracking
The system SHALL track and report motion detection statistics for monitoring and optimization.

#### Scenario: Track frames captured vs sent
- **GIVEN** a camera has captured 100 frames
- **WHEN** 20 frames were sent and 80 were filtered
- **THEN** the system shall track these counts in CameraState
- **AND** the stats endpoint shall return these values

#### Scenario: Calculate detection rate
- **GIVEN** frames_captured = 100 and frames_sent = 20
- **WHEN** detection rate is calculated
- **THEN** detection_rate shall be 20% (20/100)
- **AND** this metric shall be available in the stats endpoint

#### Scenario: Alert on abnormal detection rate
- **GIVEN** a camera has detection_rate < 5% for 100 consecutive frames
- **WHEN** the next frame is processed
- **THEN** the system shall log a warning "Low detection rate: X% - consider adjusting threshold"

#### Scenario: Alert on high detection rate
- **GIVEN** a camera has detection_rate > 95% for 100 consecutive frames
- **WHEN** the next frame is processed
- **THEN** the system shall log a warning "High detection rate: X% - motion detection may be too lenient"

### Requirement: Logging and Debugging
The system SHALL log motion detection events for debugging without saving filtered frames to disk.

#### Scenario: Log frame filtering decision
- **GIVEN** a frame is processed
- **WHEN** motion detection completes
- **THEN** the system shall log: "Frame processed: camera_id=X, motion_score=Y, threshold=Z, action=filtered/sent"

#### Scenario: Log motion detection errors
- **GIVEN** motion detection fails (e.g., invalid frame)
- **WHEN** the error occurs
- **THEN** the system shall log an error with details
- **AND** the frame shall be sent to the LLM (fail-safe)

#### Scenario: No frames saved for debugging
- **GIVEN** a frame is filtered due to low motion
- **WHEN** the frame is dropped
- **THEN** the frame shall NOT be saved to disk
- **AND** only log entry shall be created

## MODIFIED Requirements

### Requirement: Camera State Tracking
The system SHALL extend CameraState to include motion detection statistics.

#### Scenario: Track motion metrics in CameraState
- **GIVEN** a camera is capturing frames
- **WHEN** motion detection processes frames
- **THEN** CameraState shall include:
  - `frames_captured`: total frames captured
  - `frames_sent`: frames sent to LLM
  - `frames_filtered`: frames dropped by motion detection
  - `avg_motion_score`: average motion score
  - `detection_rate`: frames_sent / frames_captured

#### Scenario: Reset statistics on camera restart
- **GIVEN** a camera has existing motion statistics
- **WHEN** the camera is restarted
- **THEN** motion statistics shall be reset to zero
- **AND** the camera status shall update accordingly
