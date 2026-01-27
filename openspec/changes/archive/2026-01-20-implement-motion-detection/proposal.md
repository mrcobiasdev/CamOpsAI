# Implement Motion Detection

## Why
The current system sends all captured frames to the LLM for analysis, regardless of whether there are meaningful changes in the scene. This results in:

- **Inefficient API usage**: Processing similar frames wastes LLM quota
- **Increased latency**: More frames in the queue means longer processing times
- **Reduced relevance**: Most frames show static scenes with minimal value

Motion detection will filter frames with significant changes, ensuring only relevant content is analyzed.

## What Changes
- Add motion detection module with hybrid algorithm (pixel difference + background subtraction)
- Extend camera database schema with motion detection settings (motion_detection_enabled, motion_threshold)
- Integrate motion detection into FrameGrabber to filter frames before queuing
- Add motion detection statistics to CameraState and API responses
- Add logging and monitoring for motion detection events

## Impact
- **Affected specs**: camera-config (extend with motion detection), new spec: motion-detection
- **Affected code**: src/capture/frame_grabber.py (add motion filtering), src/capture/motion_detector.py (new), src/capture/camera.py (extend models), src/api/schemas.py (add motion fields), alembic migrations (add database columns)
