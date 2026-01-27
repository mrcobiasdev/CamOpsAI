# Proposal: Fix Threshold Update Not Working

## Problem Statement

The `adjust_threshold.py` script successfully updates the motion threshold value in the database, but the running `FrameGrabber` instance does not reflect the new value. The motion detector continues using the old threshold value (always 10.0) even after the database update.

## Root Cause Analysis

### Current Behavior
1. `adjust_threshold.py` calls `repo.update(cam.id, motion_threshold=new_threshold)`
2. The `update()` method in `repository.py` successfully updates the `Camera` table in the database
3. However, `FrameGrabber` uses a static `CameraConfig` dataclass object passed during initialization
4. `MotionDetector` is initialized once with `threshold=self.config.motion_threshold` in `FrameGrabber.__init__()`
5. **Problem**: When the database is updated, the `CameraConfig` object in `FrameGrabber` is NOT updated
6. The `MotionDetector` continues using the old threshold value

### Code Location
- `adjust_threshold.py:118` - Updates database
- `src/storage/repository.py:70-99` - `update()` method
- `src/capture/frame_grabber.py:42-43` - MotionDetector initialization
- `src/capture/camera.py:37` - `CameraConfig` dataclass default

## Proposed Solution

Add hot-reload capability to `FrameGrabber` to allow runtime configuration updates without requiring a full restart.

### Option 1: Add `update_config()` method to FrameGrabber
- Add a new method `update_config(new_camera_config: CameraConfig)` to `FrameGrabber`
- This method updates the internal config and reinitializes the `MotionDetector` if threshold changed
- Call this method after database update in `adjust_threshold.py`

### Option 2: Reload camera config on threshold change
- After database update, call `camera_manager.reload_camera(camera_id)` to fetch fresh config
- This is more comprehensive and allows any setting to be updated

### Recommendation
**Option 1** is preferred for this specific issue because:
- Minimal code change
- Direct solution to the reported problem
- Can be extended later to support full config reload

## Impact

### User-Facing
- Users will see threshold changes take effect immediately after running `adjust_threshold.py`
- No need to restart the entire application
- Reduced confusion about threshold not being applied

### Technical
- Minimal code change required
- Maintains existing architecture
- Backward compatible

## Alternatives Considered

### Alternative 1: Require application restart
- **Pros**: Simple, no code change
- **Cons**: Poor UX, application downtime

### Alternative 2: Poll database for config changes
- **Pros**: Always in sync
- **Cons**: Unnecessary complexity, performance overhead

### Alternative 3: Use reactive pattern with config events
- **Pros**: Clean architecture, extensible
- **Cons**: Overkill for this single issue, requires significant refactoring

## Success Criteria

1. Running `adjust_threshold.py` and selecting a new threshold immediately affects motion detection
2. `CameraManager.status()` shows the updated threshold value
3. No application restart required
4. Existing behavior is preserved for normal operation

## Testing Strategy

1. Run `adjust_threshold.py` with camera capturing
2. Verify motion detection uses new threshold (check logs)
3. Verify database value matches runtime value
4. Test all threshold options (1.0, 3.0, 5.0, 10.0, custom)
