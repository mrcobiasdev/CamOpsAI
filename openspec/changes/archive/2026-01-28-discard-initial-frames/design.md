# Design: Discard Initial Frames on Camera Connection

## Architecture Overview

This design describes how to implement frame discarding during camera connection establishment to improve frame quality and reduce false positives in motion detection.

## Current State

The camera connection flow in `FrameGrabber`:
1. `connect()` establishes RTSP connection
2. Resets statistics and motion detector
3. Immediately begins capturing frames in `_capture_loop()`
4. First frames are processed without any warm-up period
5. Motion detector may have unstable baseline during first frames

## Proposed Flow

### Connection with Frame Discarding

```
┌─────────────────┐
│  connect()      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Establish RTSP │
│  connection     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Reset stats &  │
│  motion detector│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Discard N      │
│  initial frames │  ← NEW
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stabilize     │  ← NEW
│  motion detector│
│  baseline       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Begin normal   │
│  frame capture  │
└─────────────────┘
```

### Reconnection Flow

The reconnection flow in `_reconnect()`:
1. Release existing capture
2. Wait 2 seconds
3. Call `connect()` (which now includes discarding)

## Implementation Details

### 1. Configuration (settings.py)

```python
class Settings(BaseSettings):
    # Existing settings...
    initial_frames_to_discard: int = 5  # NEW: Frames to discard after connection
```

Environment variable: `INITIAL_FRAMES_TO_DISCARD` (default: 5)

### 2. Camera State Tracking (camera.py)

Add to `CameraState`:
```python
@dataclass
class CameraState:
    # Existing fields...
    initial_frames_discarded: int = 0  # NEW: Count of frames discarded during connection
```

Update `reset_stats()` to reset this counter:
```python
def reset_stats(self):
    # Existing resets...
    self.initial_frames_discarded = 0  # NEW
```

### 3. Frame Discarding Logic (frame_grabber.py)

Add method to discard initial frames:
```python
async def _discard_initial_frames(self) -> None:
    """Discards N initial frames after connection to allow stream to stabilize.

    These frames are used to establish a stable baseline for motion detection
    but are not processed for motion detection or sent to LLM.
    """
    discard_count = settings.initial_frames_to_discard

    if discard_count <= 0:
        return

    logger.info(
        f"Discarding {discard_count} initial frames for camera {self.config.name} "
        f"(stream stabilization + motion detector baseline)"
    )

    for i in range(discard_count):
        frame = await self._grab_frame()
        if frame is not None:
            self.state.initial_frames_discarded += 1
            logger.debug(
                f"Discarded initial frame {i+1}/{discard_count} for camera {self.config.name}"
            )

            if self._motion_detector:
                try:
                    loop = asyncio.get_event_loop()
                    decoded_frame = await loop.run_in_executor(
                        None,
                        lambda: cv2.imdecode(
                            np.frombuffer(frame, dtype=np.uint8), cv2.IMREAD_COLOR
                        ),
                    )

                    if decoded_frame is not None:
                        self._motion_detector.detect_motion(decoded_frame)
                        logger.debug(
                            f"Stabilized motion detector with frame {i+1}/{discard_count} "
                            f"for camera {self.config.name}"
                        )
                except Exception as e:
                    logger.debug(
                        f"Failed to stabilize motion detector from discarded frame {i+1}/{discard_count}: {e}"
                    )
        else:
            logger.debug(
                f"Failed to capture initial frame {i+1}/{discard_count} "
                f"for camera {self.config.name} (will continue)"
            )
```

Modify `connect()` to call discarding:
```python
async def connect(self) -> bool:
    # Existing connection logic...
    self.state.status = CameraStatus.CONNECTED
    self.state.reset_stats()

    # Reset motion detector on connection
    if self._motion_detector:
        self._motion_detector.reset()

    # NEW: Discard initial frames
    await self._discard_initial_frames()

    logger.info(f"Câmera {self.config.name} conectada")
    return True
```

### 4. API Schema Updates (schemas.py)

Add to `CameraStatusResponse`:
```python
class CameraStatusResponse(BaseModel):
    # Existing fields...
    initial_frames_discarded: int  # NEW
```

### 5. Database Schema (Optional)

The `initial_frames_discarded` counter is session-only and doesn't need to persist to the database. It's reset on each connection/reconnection.

## Trade-offs

### Pros
- Reduces false positives during connection establishment
- Establishes stable baseline for motion detector
- Simple global configuration
- Minimal performance impact (only on connection)
- Debug logging provides visibility

### Cons
- Adds delay to first frame processing (N frames * capture time)
- Global setting means all cameras have same behavior
- Discarded frames consume network bandwidth but aren't processed for motion detection

## Edge Cases

1. **Frame read fails during discard**: Continue to next frame, don't block connection
2. **Discard count set to 0**: Skip discarding, immediate processing
3. **Discard count negative**: Treat as 0 (no discarding)
4. **Camera already connected (reconnection)**: Discarding happens in `connect()` so reconnections also benefit
5. **Motion detector not available**: Frames are still discarded but baseline stabilization is skipped

## Dependencies

- Depends on `rtsp-stream-reliability` connection flow
- Enhances `camera-config` with new environment variable
- Extends `frame-processing-queue` statistics tracking

## Migration

No database migration required. This is a runtime-only enhancement.

## Testing Considerations

1. Test with discard count = 0 (no discarding)
2. Test with discard count = 5 (default)
3. Test with high discard count to ensure no blocking
4. Test reconnection scenario
5. Verify discarded frame counter increments
6. Verify debug logs are generated
7. Verify motion detector baseline is established with discarded frames
8. Verify first processed frame after discard is valid
9. Verify motion detection works normally after discard period
