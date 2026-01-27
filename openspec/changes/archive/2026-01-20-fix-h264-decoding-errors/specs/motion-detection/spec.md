# motion-detection Specification Extension

## Purpose
Extend existing motion-detection specification to include decoder error tracking in CameraState.

## ADDED Requirements

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
