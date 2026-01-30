# frame-processing-queue Specification Delta

## ADDED Requirements

### Requirement: Video File End-of-Stream Handling
The system SHALL detect and handle video file end-of-stream events gracefully without attempting reconnection.

#### Scenario: Detect end of video file
- **GIVEN** a video file camera is capturing frames
- **WHEN** OpenCV VideoCapture read() returns False (end of file)
- **THEN** FrameGrabber shall detect end-of-stream condition
- **AND** capture loop shall exit normally
- **AND** camera status shall update to "disconnected"
- **AND** system shall log "Video file playback completed"

#### Scenario: No reconnection attempts for video file end
- **GIVEN** a video file camera reaches end of file
- **WHEN** capture loop exits
- **THEN** system shall NOT invoke reconnection logic
- **AND** consecutive_errors counter shall be ignored
- **AND** camera shall be removed from active cameras list

#### Scenario: Report video file completion statistics
- **GIVEN** a video file camera has finished processing
- **WHEN** capture stops
- **THEN** system shall log final statistics
- **AND** log shall include: total_frames_processed, frames_sent, frames_filtered, video_duration_seconds
- **AND** statistics endpoint shall return these metrics for the camera

#### Scenario: Handle video file reading errors
- **GIVEN** a video file camera is capturing frames
- **WHEN** OpenCV read() fails with error mid-stream
- **THEN** camera status shall change to "error"
- **AND** system shall log error with frame position
- **AND** capture shall stop without reconnection attempt
- **AND** error message shall include "Video file read error at position X"

### Requirement: Video File Frame Position Tracking
The system SHALL track and report the current frame position for video file cameras.

#### Scenario: Track current frame number
- **GIVEN** a video file camera is capturing frames
- **WHEN** frames are processed
- **THEN** CameraState shall include `current_frame_number`
- **AND** value shall represent the current position in video
- **AND** value shall be updated with each frame capture

#### Scenario: Report video file progress
- **GIVEN** a video file camera is active
- **WHEN** camera status is queried via API
- **THEN** status response shall include video file metadata
- **AND** metadata shall include: current_frame, total_frames, progress_percentage
- **AND** progress_percentage shall be (current_frame / total_frames * 100)

#### Scenario: Seek to specific frame on restart
- **GIVEN** a video file camera was stopped at frame 500
- **WHEN** camera is started again
- **THEN** capture shall resume from frame 500
- **AND** current_frame_number shall start at 500
- **AND** motion detector shall continue with existing baseline

### Requirement: Video File Pipeline Integration
The system SHALL support full processing pipeline (motion detection → LLM analysis → storage → alerts) for video file cameras.

#### Scenario: Motion detection works with video file frames
- **GIVEN** a video file camera is capturing
- **WHEN** frames are processed
- **THEN** motion detection shall work identically to RTSP cameras
- **AND** motion scores shall be calculated and filtered
- **AND** only frames with motion_score >= threshold shall be sent to LLM

#### Scenario: LLM analysis processes video file frames
- **GIVEN** a video file camera sends frames with motion
- **WHEN** frames are queued for analysis
- **THEN** LLM Vision shall analyze frames
- **AND** results shall be stored in database
- **AND** events shall be associated with the video file camera

#### Scenario: Alerts work with video file cameras
- **GIVEN** a video file camera generates events with keywords
- **WHEN** event keywords match alert rules
- **THEN** alert system shall trigger notifications
- **AND** alerts shall be sent via configured channels (WhatsApp)
- **AND** alert logs shall record video file camera as source

#### Scenario: Video file events include metadata
- **GIVEN** a video file camera creates an event
- **WHEN** event is stored in database
- **THEN** event metadata shall include video file information
- **AND** event shall link to frame position in video
- **AND** query results shall be filterable by video file camera
