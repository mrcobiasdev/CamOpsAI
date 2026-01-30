## 1. Database Schema and Models
- [x] 1.1 Create Alembic migration `004_add_video_file_support.py`
- [x] 1.2 Add `source_type VARCHAR(20) DEFAULT 'rtsp'` column to cameras table
- [x] 1.3 Update `Camera` model in `src/storage/models.py` with `source_type` field
- [x] 1.4 Update `CameraConfig` in `src/capture/camera.py` with `source_type` parameter
- [x] 1.5 Test migration on development database
- [x] 1.6 Verify existing cameras default to 'rtsp' after migration

## 2. Camera Configuration and API
- [x] 2.1 Add `source_type` field to `CameraCreate` schema in `src/api/schemas.py`
- [x] 2.2 Add `source_type` field to `CameraUpdate` schema in `src/api/schemas.py`
- [x] 2.3 Add `source_type` field to `CameraResponse` schema
- [x] 2.4 Implement source type auto-detection based on URL pattern (rtsp:// vs file extension)
- [x] 2.5 Update camera creation endpoint to accept `source_type`
- [x] 2.6 Update camera update endpoint to handle `source_type` changes
- [x] 2.7 Add validation for video file extensions (.mp4, .avi, .mov, .mkv, .webm, .flv, .m4v)
- [x] 2.8 Add validation to check video file exists on filesystem

## 3. Video File Validation
- [x] 3.1 Implement video file path validation function
- [x] 3.2 Add check for file existence (os.path.exists)
- [x] 3.3 Add check for file readability (try OpenCV open)
- [x] 3.4 Convert relative paths to absolute paths
- [x] 3.5 Expand environment variables in file paths
- [x] 3.6 Return clear error messages for validation failures
- [x] 3.7 Add validation tests for invalid files, non-existent files, and valid files

## 4. FrameGrabber Enhancements
- [x] 4.1 Modify `FrameGrabber._create_capture()` to handle video files
- [x] 4.2 Add `source_type` attribute to FrameGrabber class
- [x] 4.3 Modify `_discard_initial_frames()` to work with video files (no reconnection needed)
- [x] 4.4 Modify capture loop to detect end-of-stream (ret == False from cv2.read())
- [x] 4.5 Add logic to stop capture gracefully on end-of-stream for video files
- [x] 4.6 Skip reconnection attempts for video file sources
- [x] 4.7 Update error handling to log video file position on errors
- [x] 4.8 Test FrameGrabber with video file (start, capture frames, end-of-stream)

## 5. Camera State and Tracking
- [x] 5.1 Add `current_frame_number` field to `CameraState` class
- [x] 5.2 Update `CameraState` to track video file metadata (total_frames, duration)
- [x] 5.3 Update frame capture to increment `current_frame_number`
- [x] 5.4 Update camera status API to include video file progress information
- [x] 5.5 Add `progress_percentage` calculation for video file cameras
- [x] 6.6 Test status endpoint returns correct frame position

## 6. Camera Manager Integration
- [x] 6.1 Update `CameraManager` to handle video file camera lifecycle
- [x] 6.2 Ensure video file cameras start correctly with `source_type = 'video_file'`
- [x] 6.3 Update camera stop logic to handle video file cameras (save position if needed)
- [ ] 6.4 Verify hot-reload works with video file cameras
- [ ] 6.5 Test multiple cameras (mix of RTSP and video files) simultaneously

## 7. Frame Queue Processing
- [x] 7.1 Verify queue accepts frames from video file cameras
- [x] 7.2 Ensure motion detection works identically for video file frames
- [x] 7.3 Verify LLM analysis processes video file frames correctly
- [x] 7.4 Test event storage for video file cameras
- [x] 7.5 Verify alert system triggers for video file camera events
- [x] 7.6 Test queue handles video file camera stop gracefully

## 8. End-of-Stream Handling
- [x] 8.1 Detect when cv2.VideoCapture.read() returns False (end of file)
- [x] 8.2 Set camera status to "disconnected" on end-of-stream
- [x] 8.3 Log final statistics (total_frames, frames_sent, frames_filtered, duration)
- [x] 8.4 Remove camera from active cameras list
- [x] 8.5 Ensure no reconnection attempts for video files
- [x] 8.6 Test with short videos (< 5 seconds) and long videos (> 1 minute)

## 9. Integration Testing
- [x] 9.1 Create test video file with known motion events
- [x] 9.2 Create video file camera via API
- [x] 9.3 Start capture and verify frames are processed
- [x] 9.4 Verify motion detection filters correctly
- [x] 9.5 Verify LLM analysis completes and stores events
- [x] 9.6 Verify alerts are triggered if keywords match
- [x] 9.7 Verify camera stops when video ends
- [x] 9.8 Verify statistics are reported correctly
- [x] 9.9 Test pause/resume functionality for video file cameras
- [x] 9.10 Test with multiple video file cameras simultaneously

## 10. Documentation
- [x] 10.1 Update README.md with video file camera support
- [x] 10.2 Document supported video file formats
- [x] 10.3 Document video file camera lifecycle (no reconnection, stop on EOF)
- [x] 10.4 Add API documentation examples for video file cameras
- [x] 10.5 Document recommended video file sizes and locations
- [x] 10.6 Add troubleshooting section for video file issues

## 11. Error Handling Edge Cases
- [ ] 11.1 Test with non-existent video file (should fail creation)
- [ ] 11.2 Test with invalid video format (should fail creation)
- [ ] 11.3 Test with corrupted video file (should stop gracefully with error)
- [ ] 11.4 Test with file deleted while camera is active (should stop with error)
- [ ] 11.5 Test with frame_interval longer than video duration (log warning)
- [ ] 11.6 Test with extremely large video files (> 1GB, log warning)
- [ ] 11.7 Test with empty video files (should handle gracefully)

## 12. Validation and Linting
- [x] 12.1 Run existing test suite and ensure no regressions
- [x] 12.2 Run `openspec validate add-video-file-capture --strict --no-interactive`
- [x] 12.3 Run Python linter (ruff or flake8) on new code
- [x] 12.4 Run type checker (mypy) if configured
- [x] 12.5 Fix all linting and type errors before proceeding
