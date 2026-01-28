# Proposal: Discard Initial Frames on Camera Connection

## Summary

Add capability to discard a configurable number of initial frames after camera startup and reconnection to prevent processing unstable or buffered frames during connection establishment.

## Motivation

When connecting to RTSP camera streams or reconnecting after errors, initial frames may be unstable, buffered, or incomplete. Processing these frames can lead to:
- False motion detections due to stream initialization artifacts
- Wasted processing resources on low-quality frames
- Inconsistent behavior during connection establishment

By discarding a configurable number of initial frames after each successful connection (both initial and reconnections), the system will:
- Only process stable, high-quality frames
- Reduce false positives in motion detection
- Provide more reliable behavior during startup and reconnection scenarios

## Proposed Solution

### Configuration
- Add global environment variable `INITIAL_FRAMES_TO_DISCARD` (default: 5)
- This setting applies to all cameras uniformly

### Behavior
1. **Initial Connection**: After successful camera connection, discard N frames before processing begins
2. **Reconnection**: After successful reconnection, discard N frames before processing resumes
3. **Motion Detector Stabilization**: Discarded frames are used to establish a stable baseline for motion detection but are not processed for motion detection or sent to LLM
4. **Logging**: Log each discarded frame at DEBUG level for debugging
5. **Statistics**: Track total discarded frames in camera statistics

### Impact

This change modifies:
- `camera-config`: Add environment variable for discard count
- `rtsp-stream-reliability`: Add frame discarding logic on connection
- `frame-processing-queue`: Track discarded frame statistics

### Alternatives Considered

1. **Per-camera configuration**: More flexible but adds complexity. Chose global setting for simplicity.
2. **Time-based discard**: Wait X seconds before processing. Chose frame count for more predictable behavior.
3. **Silent discard**: No logging. Chose to log at DEBUG for debugging visibility.

## Implementation Plan

1. Add environment variable `INITIAL_FRAMES_TO_DISCARD` to settings
2. Add `initial_frames_discarded` counter to `CameraState`
3. Implement frame discarding logic in `FrameGrabber.connect()` and after reconnection
4. Use discarded frames to stabilize motion detector baseline (establish stable _previous_frame)
5. Log discarded frames at DEBUG level
6. Update camera status response to include discarded frame count
7. Update database migration (optional, if storing counter in database)

See `tasks.md` for detailed implementation steps.

## Success Criteria

- [x] Frames are discarded after initial connection
- [x] Frames are discarded after reconnection
- [x] Discard count is configurable via environment variable
- [x] Discarded frames are used to stabilize motion detector baseline
- [x] Discarded frames are logged at DEBUG level
- [x] Discarded frame count is tracked in statistics
- [x] Normal frame processing resumes after discard period
- [x] All existing tests pass
