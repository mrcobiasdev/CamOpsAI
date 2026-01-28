# Tasks: Discard Initial Frames on Camera Connection

## Phase 1: Configuration and State Management

- [x] Add `initial_frames_to_discard` environment variable to settings (src/config/settings.py)
  - Default value: 5
  - Type: int
  - Validation: >= 0

- [x] Add `initial_frames_discarded` field to `CameraState` (src/capture/camera.py)
  - Type: int
  - Default: 0

- [x] Update `reset_stats()` method in `CameraState` to reset `initial_frames_discarded` to 0

## Phase 2: Frame Discarding Logic

- [x] Implement `_discard_initial_frames()` method in `FrameGrabber` (src/capture/frame_grabber.py)
  - Loop for `settings.initial_frames_to_discard` iterations
  - Call `_grab_frame()` for each iteration
  - Use discarded frames to stabilize motion detector baseline (call detect_motion)
  - Log each discarded frame at DEBUG level
  - Increment `initial_frames_discarded` counter
  - Handle failed frame reads gracefully (continue to next frame)

- [x] Modify `connect()` method in `FrameGrabber` to call `_discard_initial_frames()`
  - Call after resetting stats and motion detector
  - Call before returning success

- [x] Verify reconnection flow benefits from discarding
  - `_reconnect()` already calls `connect()`, so discarding will happen automatically

## Phase 3: API and Statistics

- [x] Add `initial_frames_discarded` field to `CameraStatusResponse` schema (src/api/schemas.py)
  - Type: int
  - Required field

- [x] Update camera status endpoint to include `initial_frames_discarded` (src/api/routes/cameras.py)
  - Map `CameraState.initial_frames_discarded` to response

## Phase 4: Testing

- [x] Unit test for `CameraState.reset_stats()` resets `initial_frames_discarded`
- [x] Unit test for `_discard_initial_frames()` with count = 0
- [x] Unit test for `_discard_initial_frames()` with count = 5 (default)
- [x] Unit test for `_discard_initial_frames()` with failed frame reads
- [x] Integration test for initial connection discards frames
- [x] Integration test for reconnection discards frames
- [x] Verify motion detector is stabilized with discarded frames
- [x] Verify debug logs are generated for discarded frames
- [x] Verify counter increments correctly
- [x] Verify normal frame processing resumes after discard

## Phase 5: Documentation

- [x] Add environment variable documentation to README or .env.example
- [x] Update API documentation for camera status endpoint

## Dependencies

- Phase 2 depends on Phase 1 (configuration must exist before implementing logic)
- Phase 3 depends on Phase 2 (logic must be implemented before exposing via API)
- Phase 4 depends on Phase 3 (API must expose counter for verification)

## Parallel Work

The following tasks can be done in parallel:
- All Phase 1 tasks
- All Phase 4 tasks (after Phase 2 is complete)

## Estimated Effort

- Phase 1: 30 minutes
- Phase 2: 1 hour
- Phase 3: 30 minutes
- Phase 4: 2 hours
- Phase 5: 30 minutes

**Total estimated effort**: 4.5 hours
