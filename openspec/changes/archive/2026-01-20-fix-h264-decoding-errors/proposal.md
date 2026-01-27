# Proposal: Fix H.264 RTSP Stream Decoding Errors

## Why
Users experience missed motion detection events when RTSP streams send corrupted H.264 packets. The current implementation cannot gracefully handle decoder errors, causing the capture loop to fail and reconnect instead of skipping corrupted frames. This leads to missed detection events and unnecessary camera reconnections, impacting system reliability and increasing costs.

## What Changes
Enhanced RTSP stream configuration with FFmpeg error recovery options, graceful decoder error handling with frame skipping, frame validation before motion detection, decoder error tracking and health monitoring, and extended CameraState with decoder statistics.

## Summary
Improve RTSP stream handling and H.264 decoding reliability to prevent frame loss and motion detection failures when encountering corrupted or incomplete video packets.

## Problem Statement
The user reported walking in front of the camera but no detection occurred. Logs showed H.264 decoder errors:
```
[NULL @ 00000249b325fa40] missing picture in access unit with size 27
[h264 @ 00000249b31f6f00] no frame!
```

This indicates:
1. RTSP stream is sending incomplete/corrupted H.264 packets
2. OpenCV's default FFmpeg backend is not handling these errors gracefully
3. Corrupted frames cause the capture loop to fail and attempt reconnection
4. Motion detection cannot process frames that are being dropped due to decoder errors

## Root Causes
1. **Minimal RTSP Configuration**: Current VideoCapture setup only sets `CAP_PROP_BUFFERSIZE=1`, which is insufficient for handling unstable streams
2. **No Error Recovery**: When FFmpeg returns `ret=False` due to decoder errors, the system immediately tries to reconnect instead of skipping the corrupted frame
3. **No Frame Validation**: No validation of decoded frame quality before processing
4. **Default FFmpeg Options**: Using default FFmpeg options which are not optimized for RTSP streams with potential packet loss
5. **Motion Threshold Too High**: Default threshold of 10% may be too high for subtle movements, combined with frame loss issues

## Solution Overview
1. **Enhanced RTSP Configuration**: Add FFmpeg backend options optimized for RTSP streams with error resilience
2. **Graceful Error Handling**: Implement frame skipping on decoder errors instead of immediate reconnection
3. **Frame Validation**: Add frame quality checks before motion detection
4. **Improved Logging**: Add detailed logging to distinguish between connection issues vs decoder issues
5. **Health Monitoring**: Add RTSP decoder health metrics to monitor error rates
6. **Auto-Tuning**: Provide guidance for adjusting motion thresholds based on decoder health

## Scope
- Modify `FrameGrabber._create_capture()` to add RTSP/FFmpeg options
- Add frame validation in `FrameGrabber._grab_frame()`
- Improve error handling in `FrameGrabber._capture_loop()`
- Add decoder error tracking in `CameraState`
- Add new spec requirements for RTSP stream reliability

## Out of Scope
- Motion detection algorithm changes (already implemented)
- Camera hardware troubleshooting
- Network infrastructure improvements
- Alternative capture backends (DirectShow, GStreamer)

## Alternatives Considered
1. **Switch to DirectShow backend**: Not suitable as it doesn't support RTSP
2. **Use GStreamer backend**: More complex setup, would require additional dependencies
3. **Implement custom RTSP client**: Too complex, reinventing the wheel
4. **Disable motion detection**: Not acceptable as it increases API costs
5. **Ignore decoder errors**: Would result in missing detection events

## Dependencies
- OpenCV 4.11.0 with FFmpeg support (already installed)
- No new external dependencies required

## Risks and Mitigations
- **Risk**: New RTSP options may not work with all camera models
  - **Mitigation**: Make options configurable via environment variables, fall back to minimal config on failure
- **Risk**: Frame validation may be too strict and drop valid frames
  - **Mitigation**: Use lenient validation checks (non-empty, reasonable resolution)
- **Risk**: Skipping corrupted frames may lead to missing detection events
  - **Mitigation**: Log skipped frames, allow threshold adjustment, implement frame gap detection
- **Risk**: Increased CPU usage with additional validation
  - **Mitigation**: Keep validation lightweight, only on frames that pass decoder

## Success Criteria
- [ ] H.264 decoder errors are logged but do not trigger reconnection
- [ ] Corrupted frames are skipped gracefully without disrupting the capture loop
- [ ] Motion detection continues working even with occasional decoder errors
- [ ] RTSP decoder health metrics are available via API
- [ ] User can detect when motion threshold needs adjustment based on decoder error rate
- [ ] Tests verify frame validation and error handling behavior
