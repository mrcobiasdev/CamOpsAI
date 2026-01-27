# Design: Fix Threshold Update Not Working

## Architectural Overview

### Current Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ adjust_threshold │────▶│ CameraRepository │────▶│   PostgreSQL    │
│     .py        │     │                 │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          │
                                                          ▼
                                                   ┌─────────────────┐
                                                   │   cameras      │
                                                   │   table        │
                                                   └─────────────────┘

┌─────────────────┐
│   Main App     │
│   (startup)    │
└────────┬────────┘
         │
         │ loads CameraConfig (static)
         ▼
┌─────────────────────────┐
│   FrameGrabber        │
│   .config (static)   │◀─── NOT UPDATED
└────────┬────────────────┘
         │
         │ uses
         ▼
┌─────────────────┐
│MotionDetector │
│ (initialized  │
│  once)        │
└─────────────────┘
```

### Problem: Static Config
- `FrameGrabber.config` is a `CameraConfig` dataclass passed during initialization
- `MotionDetector` is initialized once with the threshold from this config
- When database is updated, the config in memory is NOT updated
- `MotionDetector` continues using old threshold

## Proposed Solution

### Approach: Hot-Reload Method

Add an `update_config()` method to `FrameGrabber` that:
1. Accepts a new `CameraConfig` object
2. Updates the internal `self.config`
3. Reinitializes `MotionDetector` if threshold changed
4. Is thread-safe and async-safe

### New Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ adjust_threshold │────▶│ CameraRepository │────▶│   PostgreSQL    │
│     .py        │     │                 │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          │
                                                          ▼
                                                   ┌─────────────────┐
                                                   │   cameras      │
                                                   │   table        │
                                                   └─────────────────┘
                              ┌──────────────────────────────┘
                              │
                              │ calls update_config()
                              ▼
                   ┌─────────────────────────┐
                   │   FrameGrabber        │
                   │   .config (updated)    │◀─── UPDATED!
                   └────────┬────────────────┘
                            │
                            │ reinitializes
                            ▼
                   ┌─────────────────┐
                   │MotionDetector │
                   │ (new threshold)│
                   └─────────────────┘
```

## Implementation Details

### 1. FrameGrabber Changes

```python
class FrameGrabber:
    def update_config(self, new_config: CameraConfig):
        """Update camera configuration at runtime."""
        old_threshold = self.config.motion_threshold
        self.config = new_config

        # Reinitialize motion detector if threshold changed
        if self.config.motion_detection_enabled:
            if (self._motion_detector is None or
                old_threshold != self.config.motion_threshold):
                self._motion_detector = MotionDetector(
                    threshold=self.config.motion_threshold
                )
                logger.info(
                    f"Motion detector reinitialized with new threshold: "
                    f"{self.config.motion_threshold}%"
                )
```

### 2. CameraManager Changes

```python
class CameraManager:
    async def update_camera_config(self, camera_id: uuid.UUID):
        """Update grabber config from database."""
        grabber = self._grabbers.get(camera_id)
        if not grabber:
            return False

        async with AsyncSessionLocal() as session:
            repo = CameraRepository(session)
            camera = await repo.get_by_id(camera_id)
            if not camera:
                return False

            # Convert database Camera to CameraConfig
            config = CameraConfig(
                id=camera.id,
                name=camera.name,
                url=camera.url,
                enabled=camera.enabled,
                frame_interval=camera.frame_interval,
                motion_detection_enabled=camera.motion_detection_enabled,
                motion_threshold=camera.motion_threshold,
            )

            # Update grabber configuration
            grabber.update_config(config)
            return True
```

### 3. adjust_threshold.py Changes

```python
# After updating database (line 119-124)
print("\n🔄 Atualizando câmeras...")
updated = []
for cam in cameras:
    updated_cam = await repo.update(cam.id, motion_threshold=new_threshold)
    if updated_cam:
        updated.append(cam.name)

# NEW: Update running grabbers
for cam in cameras:
    await camera_manager.update_camera_config(cam.id)

print(f"✅ Atualizadas {len(updated)} câmeras (em execução)")
```

## Trade-offs

### Pros
- ✅ Immediate effect, no restart needed
- ✅ Minimal code change
- ✅ Thread-safe implementation
- ✅ Maintains existing architecture
- ✅ Extensible to other settings

### Cons
- ❌ Adds complexity to FrameGrabber
- ❌ Need to handle concurrent config updates
- ❌ MotionDetector state is lost on reinitialization

## Risk Mitigation

### Concurrent Updates
- Use lock in `update_config()` to prevent race conditions
- Only one update at a time per grabber

### MotionDetector State Loss
- Document that motion detector baseline is reset on config update
- This is acceptable as user is explicitly changing threshold
- Alternative: preserve baseline if needed (more complex)

## Backward Compatibility

- Existing code continues to work unchanged
- `update_config()` is optional
- No breaking changes to API
- `CameraConfig` dataclass remains unchanged

## Future Extensibility

This pattern can be extended to support:
- Frame interval changes
- Motion detection enable/disable
- Any other camera setting
- Full hot-reload of camera configuration
