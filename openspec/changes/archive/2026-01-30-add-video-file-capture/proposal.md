# Change: Add Video File Capture as Camera Source

## Why
Users need a way to test and validate the complete motion capture and LLM analysis pipeline using recorded video files instead of requiring live RTSP camera streams. This enables:
- Testing motion detection parameters on real-world scenarios without needing active cameras
- Validating LLM analysis quality with known video content
- Debugging and development without camera hardware dependencies
- Reproducing issues with specific video content

## What Changes
- Add camera source type support (`source_type` field) to distinguish between RTSP streams and video files
- Modify FrameGrabber to handle video file inputs (cv2.VideoCapture works with both)
- Add database migration for `source_type` field in cameras table
- Update camera configuration APIs to support video file URLs
- Handle video file end-of-stream gracefully (stop processing, not reconnect)
- Maintain full pipeline support: motion detection → LLM analysis → event storage → alerts
- Add validation to ensure video files exist and are readable
- Update camera manager to handle video source lifecycle

## Impact
- Affected specs:
  - `camera-config` - ADD: source_type field and video file support
  - `motion-detection` - MODIFIED: video file frame processing (algorithm unchanged)
  - `frame-processing-queue` - MODIFIED: end-of-stream handling for video files
- Affected code:
  - `src/storage/models.py` - add source_type field
  - `src/capture/camera.py` - update CameraConfig with source_type
  - `src/capture/frame_grabber.py` - handle video file end-of-stream
  - `src/api/routes/cameras.py` - update create/update endpoints
  - `src/api/schemas.py` - add source_type to schemas
  - Alembic migration for database schema update
