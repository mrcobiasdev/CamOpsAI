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
## Requirements
### Requirement: Decoder Error Tracking in CameraState
The system SHALL extend CameraState to include decoder error statistics.

#### Scenario: Track decoder metrics in CameraState
- **GIVEN** a camera is capturing frames
- **WHEN** decoder errors occur
- **THEN** CameraState shall include:
  - `decoder_error_count`: total decoder errors encountered
  - `decoder_error_rate`: percentage of frames with decoder errors
  - `last_decoder_error`: timestamp or message of last error

#### Scenario: Reset decoder statistics on camera restart
- **GIVEN** a camera has existing decoder error statistics
- **WHEN** the camera is restarted
- **THEN** decoder error statistics shall be reset to zero

### Requirement: Hot-Reload Configuration
The system SHALL support hot-reload of camera configuration without requiring application restart.

#### Scenario: Update motion threshold on running camera
- **GIVEN** a camera is currently capturing with `motion_threshold` = 10.0
- **WHEN** `adjust_threshold.py` is executed and threshold is changed to 5.0
- **THEN** database shall be updated with new threshold
- **AND** `FrameGrabber.config.motion_threshold` shall be updated immediately
- **AND** `MotionDetector` shall be reinitialized with new threshold
- **AND** next frame comparison shall use 5.0
- **AND** no application restart is required

#### Scenario: Update motion detection enabled status
- **GIVEN** a camera is currently capturing with `motion_detection_enabled` = true
- **WHEN** motion detection is disabled via configuration update
- **THEN** `FrameGrabber.config.motion_detection_enabled` shall be updated
- **AND** `FrameGrabber._motion_detector` shall be set to None
- **AND** motion detection shall stop immediately
- **AND** no application restart is required

#### Scenario: Re-enable motion detection
- **GIVEN** a camera is capturing with `motion_detection_enabled` = false
- **WHEN** motion detection is enabled via configuration update
- **THEN** `FrameGrabber.config.motion_detection_enabled` shall be updated
- **AND** new `MotionDetector` shall be created with current threshold
- **AND** motion detection shall resume immediately
- **AND** no application restart is required

#### Scenario: Concurrent configuration updates
- **GIVEN** a camera is capturing frames
- **WHEN** two configuration updates are triggered simultaneously
- **THEN** updates shall be serialized (one at a time)
- **AND** no race conditions shall occur
- **AND** final configuration shall reflect the last update
- **AND** `FrameGrabber` shall remain stable

#### Scenario: Update configuration logs change
- **GIVEN** a camera configuration is updated at runtime
- **WHEN** `update_config()` is called on `FrameGrabber`
- **THEN** system shall log "Configuration updated: camera=X, field=Y, old_value=Z, new_value=W"
- **AND** if threshold changed, log "Motion detector reinitialized with new threshold: T%"
- **AND** administrator shall be able to trace configuration changes

#### Scenario: FrameGrabber update_config() method signature
- **GIVEN** a running `FrameGrabber` instance
- **WHEN** configuration needs to be updated
- **THEN** `FrameGrabber.update_config(new_config: CameraConfig)` shall exist
- **AND** method shall accept a complete `CameraConfig` object
- **AND** method shall update internal `self.config`
- **AND** method shall reinitialize components if needed

#### Scenario: CameraManager integration for hot-reload
- **GIVEN** `adjust_threshold.py` updates camera in database
- **WHEN** database update completes successfully
- **THEN** `CameraManager.update_camera_config(camera_id)` shall be called
- **AND** method shall fetch fresh camera data from database
- **AND** method shall call `FrameGrabber.update_config()`
- **AND** method shall return True on success, False on failure

#### Scenario: Configuration update failure handling
- **GIVEN** `update_config()` is called on `FrameGrabber`
- **WHEN** an error occurs during update (e.g., invalid config)
- **THEN** old configuration shall remain active
- **AND** error shall be logged with details
- **AND** `FrameGrabber` shall continue capturing without interruption
- **AND** no crash or exception shall propagate to caller

#### Scenario: Preserve MotionDetector state if possible
- **GIVEN** a camera is capturing and has a stable baseline frame
- **WHEN** only `frame_interval` is updated (not threshold)
- **THEN** `MotionDetector` shall NOT be reinitialized
- **AND** existing baseline frame shall be preserved
- **AND** motion detection shall continue without interruption

#### Scenario: Validate configuration before update
- **GIVEN** a configuration update is requested
- **WHEN** new config contains invalid values (e.g., threshold < 0 or > 100)
- **THEN** `update_config()` shall log a warning
- **AND** configuration shall not be updated
- **AND** old configuration shall remain active
- **AND** method shall return False indicating update failed

#### Scenario: Batch configuration updates
- **GIVEN** multiple cameras are updated via `adjust_threshold.py`
- **WHEN** batch update completes
- **THEN** each `FrameGrabber` shall be updated independently
- **AND** all running grabbers shall reflect new configurations
- **AND** message shall indicate "X cameras updated (in execution)"

### Requirement: Motion Sensitivity Configuration
The system SHALL support configurable motion sensitivity levels to optimize detection for different scenarios without manual parameter tuning.

#### Scenario: Create camera with default sensitivity
- **GIVEN** a new camera is created without specifying sensitivity
- **WHEN** the camera is saved to the database
- **THEN** motion_sensitivity shall default to "medium"
- **AND** MotionDetector shall use medium sensitivity preset parameters

#### Scenario: Create camera with high sensitivity for outdoor monitoring
- **GIVEN** a new camera is created for outdoor vehicle detection
- **WHEN** motion_sensitivity is set to "high"
- **THEN** camera shall use aggressive motion detection parameters
- **AND** vehicles and people shall be reliably detected (score >= 25%)

#### Scenario: Create camera with low sensitivity for stable scenes
- **GIVEN** a new camera monitors mostly static indoor area
- **WHEN** motion_sensitivity is set to "low"
- **THEN** camera shall use conservative detection parameters
- **AND** only significant movements shall trigger detection

#### Scenario: Update camera sensitivity at runtime
- **GIVEN** an existing camera with motion_sensitivity = "medium"
- **WHEN** sensitivity is updated to "high" via hot-reload
- **THEN** MotionDetector shall be reinitialized with high sensitivity parameters
- **AND** next frame comparison shall use new parameters
- **AND** no application restart is required

#### Scenario: Sensitivity presets apply correct parameters
- **GIVEN** a camera with motion_sensitivity = "medium"
- **WHEN** MotionDetector is initialized
- **THEN** blur_kernel shall be (2, 2)
- **AND** pixel_threshold shall be 10
- **AND** pixel_scale shall be 15
- **AND** bg_var_threshold shall be 10
- **AND** bg_history shall be 500

#### Scenario: Custom sensitivity allows manual tuning
- **GIVEN** a camera with motion_sensitivity = "custom"
- **WHEN** MotionDetector is initialized
- **THEN** parameters shall be loaded from camera-specific config
- **AND** user-defined values shall override preset defaults
- **AND** system shall not auto-adjust parameters

#### Scenario: Sensitivity level persists across restarts
- **GIVEN** a camera with motion_sensitivity = "high"
- **WHEN** application is restarted
- **THEN** camera shall reload with "high" sensitivity from database
- **AND** motion detection shall use same parameters as before restart

#### Scenario: Sensitivity affects motion scores predictably
- **GIVEN** identical scene with vehicle passing
- **WHEN** tested with low, medium, and high sensitivity
- **THEN** high sensitivity shall produce score >= medium score >= low score
- **AND** relative ordering shall be consistent across different scenes

#### Scenario: Invalid sensitivity value is rejected
- **GIVEN** an attempt to set motion_sensitivity to invalid value
- **WHEN** camera configuration is validated
- **THEN** system shall reject values other than "low", "medium", "high", "custom"
- **AND** error message shall list valid options
- **AND** current sensitivity shall remain unchanged

### Requirement: Motion Detection Debugging
The system SHALL provide tools to visualize and troubleshoot motion detection issues.

#### Scenario: Enable debug mode to save motion analysis frames
- **GIVEN** a camera has motion detection issues
- **WHEN** debug mode is enabled in MotionDetector
- **THEN** system shall save preprocessed frames to debug directory
- **AND** system shall save pixel difference masks
- **AND** system shall save background subtraction masks
- **AND** files shall be timestamped and include camera ID

#### Scenario: Debug mode logs detailed algorithm steps
- **GIVEN** MotionDetector is in debug mode
- **WHEN** motion is detected on a frame
- **THEN** system shall log preprocessing parameters
- **AND** system shall log pixel_diff_score and bg_sub_score separately
- **AND** system shall log which components contribute most to final score
- **AND** logs shall include frame timestamp

#### Scenario: Debug mode does not impact performance significantly
- **GIVEN** MotionDetector is in debug mode
- **WHEN** frames are processed
- **THEN** performance overhead shall be < 10ms per frame
- **AND** debug file I/O shall not block frame processing

#### Scenario: Debug files are cleaned up automatically
- **GIVEN** debug mode has been running
- **WHEN** debug directory size exceeds 100MB or age > 24 hours
- **THEN** oldest debug files shall be automatically deleted
- **AND** system shall log cleanup operation

### Requirement: Motion Detection Calibration
The system SHALL provide interactive tools to test and tune motion detection parameters.

#### Scenario: Visualize motion detection on test video
- **GIVEN** a test video file with known motion events
- **WHEN** visualization tool is run with video path
- **THEN** tool shall output video with motion mask overlay
- **AND** tool shall display motion score on each frame
- **AND** tool shall generate histogram of score distribution
- **AND** output shall be saved to specified path

#### Scenario: Test different sensitivity presets on video
- **GIVEN** a test video file
- **WHEN** visualization tool is run with --all-sensitivities flag
- **THEN** tool shall generate output for low, medium, and high presets
- **AND** tool shall compare scores side-by-side
- **AND** tool shall report detection accuracy if ground truth provided

#### Scenario: Calibrate motion detection on live camera
- **GIVEN** a running camera with suboptimal detection
- **WHEN** calibration tool is launched with camera ID
- **THEN** tool shall display live camera feed
- **AND** tool shall overlay motion mask in real-time
- **AND** tool shall show current motion score
- **AND** tool shall provide sliders to adjust parameters
- **AND** tool shall allow saving tuned parameters to database

#### Scenario: Calibration tool validates parameter ranges
- **GIVEN** user adjusts parameters in calibration tool
- **WHEN** parameter value is out of valid range
- **THEN** tool shall clamp value to valid range
- **AND** tool shall display warning message
- **AND** tool shall show recommended values

#### Scenario: Calibration saves custom sensitivity profile
- **GIVEN** user has tuned parameters via calibration tool
- **WHEN** user clicks "Save"
- **THEN** system shall update camera with motion_sensitivity="custom"
- **AND** system shall save individual parameter values
- **AND** system shall call hot-reload to apply immediately
- **AND** system shall confirm save success to user

### Requirement: Motion Detection Benchmarking
The system SHALL validate motion detection accuracy against known test cases.

#### Scenario: Benchmark against vehicle detection dataset
- **GIVEN** test videos with vehicles passing at various speeds and angles
- **WHEN** motion detection is run with medium sensitivity
- **THEN** true positive rate shall be >= 90% for lateral views
- **AND** true positive rate shall be >= 80% for frontal views
- **AND** false positive rate shall be <= 10% for static frames

#### Scenario: Benchmark against person detection dataset
- **GIVEN** test videos with people walking at various speeds
- **WHEN** motion detection is run with medium sensitivity
- **THEN** true positive rate shall be >= 85% for normal walking speed
- **AND** true positive rate shall be >= 70% for slow walking speed
- **AND** detection shall work for people at various distances from camera

#### Scenario: Benchmark performance across sensitivity levels
- **GIVEN** benchmark test dataset
- **WHEN** tests are run with low, medium, and high sensitivity
- **THEN** high sensitivity shall have highest true positive rate
- **AND** low sensitivity shall have lowest false positive rate
- **AND** medium sensitivity shall balance true positives and false positives
- **AND** all levels shall process frames in < 50ms

#### Scenario: Benchmark reports detailed metrics
- **GIVEN** benchmark tests are complete
- **WHEN** results are generated
- **THEN** report shall include true positive / false positive / true negative / false negative counts
- **AND** report shall include precision, recall, and F1 score per sensitivity
- **AND** report shall include average motion scores per scenario type
- **AND** report shall highlight any failed test cases

