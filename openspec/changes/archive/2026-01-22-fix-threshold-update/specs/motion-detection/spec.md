## ADDED Requirements

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
