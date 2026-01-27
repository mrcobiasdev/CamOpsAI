# Design: RTSP Stream Decoding Error Handling

## Architecture Overview

### Current Flow
```
Camera RTSP Stream → OpenCV VideoCapture → _grab_frame() → Motion Detection → Frame Queue
                         ↓ (error)
                    Immediate Reconnection (disruptive)
```

### Proposed Flow
```
Camera RTSP Stream → OpenCV VideoCapture (enhanced) → Frame Validation → Motion Detection → Frame Queue
                         ↓ (decoder error)                    ↓ (validation fails)
                    Skip Frame (continue loop)               Skip Frame (continue loop)
                         ↓
                    Track Decoder Error Rate
                         ↓
                    Health Monitoring / Alert if high error rate
```

## Components

### 1. Enhanced RTSP Configuration (`FrameGrabber._create_capture`)

Add FFmpeg backend options to improve RTSP stream reliability:

```python
def _create_capture(self) -> cv2.VideoCapture:
    """Create VideoCapture with RTSP-optimized FFmpeg options."""
    rtsp_options = [
        # Transport protocol
        "rtsp_transport;tcp",  # Use TCP instead of UDP for reliability
        # Buffer settings
        "fflags;nobuffer",     # Minimize buffering
        "flags;low_delay",     # Low latency mode
        # Decoder options
        "fflags;genpts",       # Generate presentation timestamps
        # Error resilience
        "err_detect;ignore_err",  # Ignore decoding errors
        # Skip corrupt packets
        "skip_frame;nokey",    # Skip non-keyframes if needed
    ]

    cap = cv2.VideoCapture(self.config.rtsp_url, cv2.CAP_FFMPEG)
    for opt in rtsp_options:
        cap.set(cv2.CAP_PROP_FFMPEG_OPTION_STRING, opt)

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap
```

**Rationale**: Using TCP transport instead of UDP reduces packet loss, which is the primary cause of incomplete H.264 access units. FFmpeg error handling options allow graceful degradation.

### 2. Frame Validation (`FrameGrabber._validate_frame`)

Add lightweight validation to ensure frame quality before processing:

```python
def _validate_frame(self, frame: np.ndarray) -> bool:
    """Validate decoded frame quality."""
    if frame is None:
        return False

    # Check dimensions
    if frame.size == 0 or len(frame.shape) < 2:
        return False

    # Check for uniform color (possible corruption)
    if np.all(frame == frame.flat[0]):
        return False

    # Check resolution is reasonable
    height, width = frame.shape[:2]
    if width < 160 or height < 120:  # Minimum reasonable resolution
        return False

    return True
```

**Rationale**: Corrupted decoder output may produce frames that are uniform, too small, or malformed. Validation prevents processing invalid frames.

### 3. Enhanced Error Handling (`FrameGrabber._capture_loop`)

Modify capture loop to handle decoder errors gracefully:

```python
async def _capture_loop(self):
    consecutive_errors = 0
    max_consecutive_errors = 10

    while self._running:
        frame = await self._grab_frame()

        if frame is not None:
            # Decode and validate
            try:
                decoded = self._decode_frame(frame)
                if not self._validate_frame(decoded):
                    logger.warning(f"Frame validation failed for camera {self.config.name}")
                    consecutive_errors += 1
                    continue

                # Reset error counter on success
                consecutive_errors = 0

                # Process with motion detection
                motion_score, has_motion = self._motion_detector.detect_motion(decoded)
                if has_motion:
                    self.on_frame(self.config.id, frame, time.time())

            except cv2.error as e:
                if "no frame" in str(e).lower() or "missing picture" in str(e).lower():
                    # Decoder error - skip and continue
                    self.state.record_decoder_error()
                    consecutive_errors += 1
                    logger.debug(f"Skipping corrupted frame (decoder error)")
                    continue
                else:
                    raise
        else:
            consecutive_errors += 1

        # Reconnect only if consecutive errors exceed threshold
        if consecutive_errors >= max_consecutive_errors:
            logger.warning(f"Too many consecutive errors ({consecutive_errors}), reconnecting")
            await self._reconnect()
            consecutive_errors = 0

        await asyncio.sleep(0.1)
```

**Rationale**: Distinguishing between decoder errors (skip) vs connection issues (reconnect) prevents unnecessary reconnections that disrupt the stream.

### 4. Decoder Error Tracking (`CameraState`)

Add decoder error statistics to CameraState:

```python
@dataclass
class CameraState:
    # ... existing fields ...

    decoder_error_count: int = 0
    decoder_error_rate: float = 0.0
    last_decoder_error: Optional[str] = None

    def record_decoder_error(self, error_msg: str = "H.264 decoder error"):
        """Record a decoder error."""
        self.decoder_error_count += 1
        self.last_decoder_error = error_msg
        self.decoder_error_rate = (
            self.decoder_error_count / self.frames_captured * 100
            if self.frames_captured > 0
            else 0.0
        )
```

**Rationale**: Tracking decoder error rate allows monitoring stream health and making informed decisions about threshold adjustments.

### 5. Health Monitoring

Add decoder health to the stats endpoint:

```python
@app.get("/api/v1/stats")
async def get_stats():
    # ... existing stats ...

    # Add decoder health
    decoder_health = {
        "total_errors": sum(g.state.decoder_error_count for g in camera_manager._grabbers.values()),
        "avg_error_rate": np.mean([
            g.state.decoder_error_rate
            for g in camera_manager._grabbers.values()
            if g.state.decoder_error_rate > 0
        ]) or 0.0,
    }

    return StatsResponse(..., decoder_health=decoder_health)
```

**Rationale**: Users can monitor decoder health and adjust camera settings if error rate is consistently high.

## Configuration

Add environment variables for RTSP tuning:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # RTSP Configuration
    rtsp_transport: str = Field(default="tcp", description="RTSP transport protocol (tcp/udp)")
    rtsp_error_recovery: bool = Field(default=True, description="Enable error recovery for RTSP streams")
    rtsp_max_consecutive_errors: int = Field(default=10, description="Max consecutive errors before reconnect")
```

## Trade-offs

### TCP vs UDP Transport
- **TCP**: More reliable, handles packet loss, but higher latency
- **UDP**: Lower latency, but more susceptible to packet loss
- **Decision**: Default to TCP for reliability, make configurable

### Skip vs Retry Corrupted Frames
- **Skip**: Faster, maintains stream continuity
- **Retry**: May recover frame, but adds latency
- **Decision**: Skip corrupted frames to maintain real-time performance

### Strict vs Lenient Frame Validation
- **Strict**: Catches all corruption, may drop valid frames
- **Lenient**: Allows some borderline frames through
- **Decision**: Lenient validation (check size and uniform color, not quality metrics)

## Migration Plan

1. Add new fields to `CameraState` with database migration
2. Modify `FrameGrabber` to use new RTSP options
3. Add frame validation and enhanced error handling
4. Update stats endpoint to include decoder health
5. Add tests for new functionality
6. Monitor decoder error rates in production
7. Provide guidance for threshold adjustment based on error rates
