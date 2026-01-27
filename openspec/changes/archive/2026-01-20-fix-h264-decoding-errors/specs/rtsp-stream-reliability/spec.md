# RTSP Stream Reliability Specification

## Purpose
Ensure reliable RTSP stream capture and H.264 video decoding with graceful error handling to prevent frame loss and maintain motion detection accuracy.

## ADDED Requirements

### Requirement: RTSP Transport Protocol Configuration
The system SHALL allow configuration of RTSP transport protocol (TCP or UDP) via environment variable `RTSP_TRANSPORT`.

#### Scenario: Default TCP transport for reliability
- **GIVEN** `RTSP_TRANSPORT` is not specified in `.env`
- **WHEN** a camera connects via RTSP
- **THEN** the VideoCapture shall use TCP transport protocol
- **AND** this provides better packet loss handling than UDP

#### Scenario: Explicit UDP transport for low latency
- **GIVEN** `RTSP_TRANSPORT` is set to "udp" in `.env`
- **WHEN** a camera connects via RTSP
- **THEN** the VideoCapture shall use UDP transport protocol
- **AND** this provides lower latency but may be less reliable

#### Scenario: Invalid transport protocol defaults to TCP
- **GIVEN** `RTSP_TRANSPORT` is set to "invalid" in `.env`
- **WHEN** a camera connects via RTSP
- **THEN** the system shall log a warning and default to TCP
- **AND** camera connection shall succeed

### Requirement: FFmpeg Error Recovery Options
The system SHALL configure FFmpeg backend with error recovery options to handle corrupted H.264 packets gracefully.

#### Scenario: FFmpeg ignores decoding errors
- **GIVEN** RTSP stream sends corrupted H.264 packet
- **WHEN** FFmpeg attempts to decode the packet
- **THEN** FFmpeg shall ignore the error using `err_detect;ignore_err`
- **AND** decoding shall continue with the next packet
- **AND** the capture loop shall continue without reconnection

#### Scenario: FFmpeg generates timestamps for incomplete frames
- **GIVEN** RTSP stream sends incomplete access unit
- **WHEN** FFmpeg attempts to decode
- **THEN** FFmpeg shall generate presentation timestamps using `fflags;genpts`
- **AND** frames shall have valid timestamps even if incomplete

#### Scenario: FFmpeg minimizes buffering
- **GIVEN** camera is configured with minimal latency requirements
- **WHEN** VideoCapture is created
- **THEN** FFmpeg shall set `fflags;nobuffer` and `flags;low_delay`
- **AND** frames shall be delivered with minimal delay

### Requirement: Decoder Error Handling
The system SHALL distinguish between decoder errors and connection issues, handling each appropriately.

#### Scenario: H.264 decoder error is logged but skipped
- **GIVEN** FFmpeg returns error "no frame" or "missing picture in access unit"
- **WHEN** the error occurs in `_grab_frame()`
- **THEN** the system shall log the error at DEBUG level
- **AND** shall increment the decoder error counter
- **AND** shall skip the current frame without attempting reconnection
- **AND** shall continue the capture loop

#### Scenario: Consecutive decoder errors trigger reconnection
- **GIVEN** `RTSP_MAX_CONSECUTIVE_ERRORS` is set to 10
- **WHEN** 10 consecutive frames fail to decode
- **THEN** the system shall log a warning about excessive errors
- **AND** shall attempt to reconnect to the camera
- **AND** shall reset the consecutive error counter

#### Scenario: Successful frame resets error counter
- **GIVEN** there have been 5 consecutive decoder errors
- **WHEN** the next frame is successfully decoded and validated
- **THEN** the consecutive error counter shall be reset to 0
- **AND** reconnection shall not be triggered

### Requirement: Frame Validation
The system SHALL validate decoded frames before processing to ensure quality and prevent processing corrupted data.

#### Scenario: Valid frame passes validation
- **GIVEN** a frame is successfully decoded with resolution 1920x1080
- **WHEN** frame validation is performed
- **THEN** the frame shall pass all validation checks
- **AND** shall proceed to motion detection

#### Scenario: Empty frame is rejected
- **GIVEN** decoder returns a frame with size 0
- **WHEN** frame validation is performed
- **THEN** the frame shall be rejected
- **AND** the error counter shall be incremented
- **AND** the capture loop shall continue to the next frame

#### Scenario: Uniform color frame is rejected
- **GIVEN** decoder returns a frame where all pixels are identical
- **WHEN** frame validation is performed
- **THEN** the frame shall be rejected as potentially corrupted
- **AND** the error counter shall be incremented
- **AND** the system shall log "Frame rejected: uniform color (possible corruption)"

#### Scenario: Resolution too low is rejected
- **GIVEN** decoder returns a frame with resolution 64x48
- **WHEN** frame validation is performed
- **THEN** the frame shall be rejected as below minimum resolution
- **AND** the system shall log "Frame rejected: resolution too low (64x48, min 160x120)"

### Requirement: Decoder Error Tracking
The system SHALL track decoder errors and maintain error rate statistics for monitoring and health checks.

#### Scenario: Record decoder error
- **GIVEN** a decoder error occurs
- **WHEN** the error is detected
- **THEN** `decoder_error_count` in CameraState shall be incremented
- **AND** `decoder_error_rate` shall be calculated as (error_count / frames_captured) * 100
- **AND** `last_decoder_error` shall be updated with the error message

#### Scenario: Calculate error rate
- **GIVEN** camera has captured 1000 frames
- **AND** has encountered 50 decoder errors
- **WHEN** error rate is calculated
- **THEN** `decoder_error_rate` shall be 5.0% (50/1000 * 100)

#### Scenario: Reset statistics on reconnection
- **GIVEN** camera has decoder_error_count = 25
- **WHEN** camera reconnects
- **THEN** `decoder_error_count` shall be reset to 0
- **AND** `decoder_error_rate` shall be recalculated from zero

### Requirement: Health Monitoring
The system SHALL provide decoder health statistics via the stats API endpoint.

#### Scenario: Stats endpoint includes decoder health
- **GIVEN** multiple cameras are active with various decoder error rates
- **WHEN** GET `/api/v1/stats` is called
- **THEN** the response shall include `decoder_health` object with:
  - `total_errors`: sum of all decoder errors across cameras
  - `avg_error_rate`: average decoder error rate across cameras

#### Scenario: Camera status endpoint includes decoder errors
- **GIVEN** a camera has experienced 15 decoder errors
- **WHEN** GET `/api/v1/cameras/{id}/status` is called
- **THEN** the response shall include:
  - `decoder_error_count`: 15
  - `decoder_error_rate`: calculated percentage
  - `last_decoder_error`: timestamp or message of last error

### Requirement: Motion Detection Continuity
The system SHALL continue motion detection even when encountering occasional decoder errors.

#### Scenario: Motion detection works after decoder error
- **GIVEN** a decoder error occurs for frame 100
- **WHEN** frame 101 is successfully decoded and has motion
- **THEN** motion detection shall work correctly on frame 101
- **AND** the motion score shall be compared against threshold
- **AND** the frame shall be sent to LLM if motion >= threshold

#### Scenario: Motion detection baseline preserved across errors
- **GIVEN** motion detector has a baseline frame
- **WHEN** 5 consecutive frames fail to decode
- **THEN** the baseline frame shall be preserved
- **AND** motion detection shall use the original baseline when decoding resumes
- **AND** motion detection shall not be affected by skipped frames
