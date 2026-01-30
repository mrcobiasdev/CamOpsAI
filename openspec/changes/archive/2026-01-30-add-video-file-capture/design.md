## Context

The CamOpsAI system currently supports only RTSP camera streams. Users need the ability to test and validate the complete motion capture and LLM analysis pipeline using recorded video files. This enables:
- Testing without requiring active camera hardware
- Reproducible testing with specific video content
- Development and debugging without live streams
- Validation of motion detection parameters on real-world scenarios

The OpenCV VideoCapture class already supports both RTSP streams and video files, so the integration can leverage existing infrastructure with minimal changes.

### Constraints
- Must maintain backward compatibility with existing RTSP cameras
- Video files should process through the full pipeline (motion detection → LLM analysis → storage → alerts)
- Cannot break existing camera management and hot-reload functionality
- Database schema changes require migration path
- Must handle video file end-of-stream gracefully (no reconnection)

### Stakeholders
- Development team: Needs testing capability without camera hardware
- QA/Testing: Wants reproducible test cases with specific video content
- Production users: May use video files for validating motion detection settings before deployment

## Goals / Non-Goals

### Goals
- Add support for video file camera sources alongside RTSP streams
- Maintain full pipeline support for video files (motion detection, LLM analysis, alerts)
- Provide video file validation (exists, readable, format support)
- Handle video file end-of-stream gracefully
- Enable pause/resume functionality for video file cameras
- Track video file playback position in camera state

### Non-Goals
- Live video stream injection or recording
- Video file transcoding or conversion
- Video editing or manipulation capabilities
- Multiple video file concatenation
- Video streaming over network
- Real-time video file monitoring for changes

## Decisions

### Decision 1: Use `source_type` field to distinguish camera inputs

**What**: Add a `source_type` enum field to cameras table with values ["rtsp", "video_file"]

**Why**:
- Clear separation of concerns in configuration
- Enables different behavior based on source (reconnection vs stop on EOF)
- Extensible for future source types (HTTP streams, USB cameras, etc.)
- Simple query: `WHERE source_type = 'video_file'`

**Alternatives considered**:
1. **Detect from URL automatically**: Ambiguous for edge cases, harder to maintain
2. **Separate tables for video files**: Over-complication, breaks existing camera queries
3. **Use existing `url` field with type inference**: Brittle, magic strings in URLs

**Trade-offs**: Added database field requires migration, but provides clean separation.

### Decision 2: OpenCV VideoCapture handles both sources

**What**: Use existing `cv2.VideoCapture()` for both RTSP and video files. OpenCV already abstracts the difference.

**Why**:
- No additional dependencies required
- Minimal code changes in capture layer
- Leverages battle-tested OpenCV abstraction
- Maintains consistent frame capture interface

**Alternatives considered**:
1. **Separate VideoFileGrabber class**: Duplicates code, harder to maintain
2. **Use moviepy or other video libraries**: Unnecessary dependency, more complex

**Trade-offs**: Must handle end-of-stream detection differently based on `source_type`.

### Decision 3: Video files stop on end, no reconnection

**What**: Video file cameras stop when reaching end-of-file, no retry logic.

**Why**:
- Video files have finite duration, reconnection makes no sense
- Clear user expectation: video ends when file ends
- Avoids infinite loops seeking back to start
- Enables one-time validation scenarios

**Alternatives considered**:
1. **Loop videos automatically**: Useful for some tests, but unexpected for others
2. **Reconnect to restart video**: Confusing, users expect "video ended" not "reconnecting"

**Trade-offs**: Requires explicit restart for repeated testing (good for reproducibility).

### Decision 4: Track video file position in CameraState

**What**: Add `current_frame_number` to CameraState for video file cameras.

**Why**:
- Enables progress reporting to users
- Supports pause/resume functionality
- Helps with debugging (which frame caused issue?)
- Useful for statistics and logging

**Alternatives considered**:
1. **Track only total frames processed**: No position context
2. **Store position in FrameGrabber only**: Not accessible via status API

**Trade-offs**: Extra field in state, minimal memory impact.

### Decision 5: Database migration adds `source_type` with default "rtsp"

**What**: Create migration to add `source_type VARCHAR(20) DEFAULT 'rtsp'` to cameras table.

**Why**:
- Maintains backward compatibility (existing cameras default to RTSP)
- Allows existing code to work without changes
- Zero-downtime deployment possible

**Alternatives considered**:
1. **Make `source_type` required**: Breaking change, requires manual updates to all cameras
2. **Infer from URL on read**: Brittle, no explicit type

**Trade-offs**: Default may be wrong for non-RTSP URLs, but can be corrected manually.

### Decision 6: Validate video files on creation, not runtime

**What**: Check file exists, is readable, and has valid format when camera is created via API.

**Why**:
- Fail fast, provide clear error messages
- Prevents bad configuration in database
- Better user experience (know immediately if file is invalid)
- Avoids runtime crashes

**Alternatives considered**:
1. **Validate on first capture start**: Delayed error, worse UX
2. **No validation, fail on read**: Confusing, hard to debug

**Trade-offs**: Slight delay on camera creation, but prevents runtime failures.

## Risks / Trade-offs

### Risk 1: Large video files consume memory

**Risk**: If user points camera at 10GB video file, system may load entire file into memory.

**Mitigation**:
- Add warning in logs for files > 1GB
- Document recommended file sizes (< 100MB for testing)
- Consider adding max_file_size configuration
- Use streaming frame-by-frame (current implementation avoids loading entire file)

### Risk 2: Video file paths become invalid after deployment

**Risk**: User adds video file with local path `/home/user/test.mp4`, but later moves file.

**Mitigation**:
- Validate on camera start (not just creation)
- Clear error message if file not found
- Recommend using dedicated directory like `/test_videos/`
- Consider supporting environment variables in paths

### Risk 3: Video file frame rate conflicts with frame_interval

**Risk**: 30fps video with 10 second interval only processes 1 frame per 10 seconds, not real-time.

**Mitigation**:
- Document that interval is between captures, not per video frame
- Log warning if interval > video_duration (makes no sense)
- Default interval respects video frame rate? (No, use configured interval)

**Trade-off**: Frame interval is user choice, system respects it even if suboptimal.

### Risk 4: Database migration fails in production

**Risk**: Adding `source_type` column to cameras table fails during migration.

**Mitigation**:
- Test migration on staging database first
- Provide rollback migration script
- Use DEFAULT 'rtsp' for backward compatibility
- Make field nullable initially, then populate, then make required if needed

### Risk 5: Motion detector not reset on video restart

**Risk**: If video file is paused at frame 500 and restarted, detector still has old baseline.

**Mitigation**:
- Option A: Reset motion detector on restart (clean slate)
- Option B: Keep baseline (detects motion from previous session)
- **Decision**: Keep baseline (consistent with RTSP reconnection behavior)

**Trade-off**: May miss motion at restart if baseline is stale, but more consistent.

## Migration Plan

### Phase 1: Database Schema Update
1. Create Alembic migration `004_add_video_file_support.py`
2. Add column: `source_type VARCHAR(20) DEFAULT 'rtsp'`
3. Backfill existing cameras with `source_type = 'rtsp'` (default handles this)
4. Test migration on development database
5. Review and approve migration script

### Phase 2: Code Changes
1. Update `Camera` model to include `source_type` field
2. Update `CameraConfig` with `source_type` parameter
3. Add source type detection based on URL pattern
4. Modify `FrameGrabber` to check `source_type` before reconnection logic
5. Add end-of-stream detection in capture loop
6. Add video file validation in camera creation API
7. Update `CameraState` with `current_frame_number` for video files
8. Update camera status API to return video progress

### Phase 3: API and Testing
1. Update `CameraCreate` and `CameraUpdate` schemas with `source_type`
2. Add validation logic for video file paths
3. Create integration tests for video file camera lifecycle
4. Test motion detection with video files
5. Test full pipeline (LLM analysis, storage, alerts)
6. Document new functionality in README

### Rollback Plan
If issues arise after deployment:

1. **Rollback migration**: Downgrade database schema, drop `source_type` column
2. **Revert code**: Use feature flag to disable video file support
3. **Notify users**: Document that video file cameras will be disabled
4. **Fix issues**: Address bugs in development environment
5. **Re-deploy**: Once fixed, re-apply migration

**Data loss risk**: Cameras with `source_type = 'video_file'` would lose type information on rollback.
- **Mitigation**: Backup cameras table before migration
- **Recovery**: Manually update camera URLs to re-add type information

## Open Questions

1. Should video files support seeking to specific frame position via API?
   - **Impact**: Adds complexity to FrameGrabber, useful for debugging
   - **Decision**: **Out of scope** for initial implementation, can be added later if requested

2. Should system support multiple video files as sequential playlist?
   - **Impact**: Changes capture loop logic, useful for batch testing
   - **Decision**: **Out of scope** for initial implementation, single video per camera

3. Should video file cameras have a "loop" option to restart automatically?
   - **Impact**: Conflicts with "stop on EOF" decision
   - **Decision**: **Out of scope** for initial implementation, can be added as feature flag

4. How should system handle video files that are deleted while camera is active?
   - **Impact**: Runtime error handling
   - **Decision**: Log error and stop camera gracefully, no reconnection (consistent with behavior)
