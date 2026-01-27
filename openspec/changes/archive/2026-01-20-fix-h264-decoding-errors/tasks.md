# Tasks: Fix H.264 RTSP Stream Decoding Errors

## Phase 1: Core RTSP Configuration
- [x] Add `RTSP_TRANSPORT`, `RTSP_ERROR_RECOVERY`, `RTSP_MAX_CONSECUTIVE_ERRORS` to Settings
- [x] Create database migration to add `decoder_error_count`, `decoder_error_rate`, `last_decoder_error` to cameras table
- [x] Update CameraState dataclass to include decoder error fields
- [x] Implement `_create_capture()` with FFmpeg backend options
  - Configure RTSP transport protocol from settings
  - Add `fflags;nobuffer`, `flags;low_delay`, `fflags;genpts`
  - Add `err_detect;ignore_err`, `skip_frame;nokey`
  - Keep `CAP_PROP_BUFFERSIZE` at 1
- [x] Update database models to support decoder error fields
- [x] Write tests for RTSP configuration (mock VideoCapture)

## Phase 2: Frame Validation
- [x] Implement `_validate_frame(frame)` method in FrameGrabber
  - Check frame is not None
  - Check frame size > 0
  - Check frame has reasonable shape (2D or 3D)
  - Check for uniform color (possible corruption)
  - Check minimum resolution (160x120)
- [x] Integrate validation into `_grab_frame()`
  - Return None if validation fails
  - Log validation failures at appropriate level
- [x] Write unit tests for frame validation:
  - Test valid frame passes
  - Test empty frame fails
  - Test uniform color frame fails
  - Test low resolution frame fails
  - Test corrupted shape fails

## Phase 3: Enhanced Error Handling
- [x] Modify `_capture_loop()` to track consecutive errors
  - Add `consecutive_errors` counter
  - Reset counter on successful frame
  - Implement reconnection threshold logic
- [x] Add specific H.264 decoder error detection
  - Detect "no frame" errors
  - Detect "missing picture in access unit" errors
  - Distinguish from other cv2.error types
- [x] Implement error handling flow:
  - Decoder error → increment counter, log DEBUG, skip frame
  - Consecutive errors ≥ threshold → reconnect
  - Connection error → log ERROR, attempt reconnection
- [x] Write integration tests for error handling flow

## Phase 4: Decoder Error Tracking
- [x] Implement `record_decoder_error()` in CameraState
  - Increment `decoder_error_count`
  - Update `decoder_error_rate`
  - Update `last_decoder_error`
- [x] Integrate error tracking into `_capture_loop()`
  - Call `record_decoder_error()` on decoder errors
  - Ensure error rate is accurate
- [x] Update `CameraRepository` to persist decoder stats
- [x] Write tests for error tracking accuracy

## Phase 5: Health Monitoring
- [x] Update StatsResponse schema to include `decoder_health`
  - Add `total_errors` field
  - Add `avg_error_rate` field
- [x] Implement decoder health calculation in `/api/v1/stats` endpoint
  - Aggregate errors across all cameras
  - Calculate average error rate
- [x] Update camera status endpoint to include decoder errors
  - Add decoder fields to status response
- [x] Write tests for health monitoring endpoints

## Phase 6: Testing and Validation
- [x] Create mock RTSP stream with injected errors for testing
  - Simulate H.264 decoder errors
  - Simulate corrupted frames
  - Simulate packet loss
- [x] Write end-to-end test:
  - Connect to test stream
  - Trigger decoder errors
  - Verify error handling
  - Verify motion detection continues
  - Verify health metrics are accurate
- [x] Performance testing:
  - Measure overhead of frame validation
  - Verify < 10ms additional processing time
  - Verify error handling doesn't increase latency
- [ ] Manual testing with real RTSP camera:
  - Test with user's camera that showed errors
  - Verify decoder errors are handled gracefully
  - Verify motion detection works
  - Monitor decoder error rate over time

## Phase 7: Documentation and Monitoring
- [x] Update README.md with RTSP configuration guidance
  - Explain TCP vs UDP transport
  - Explain decoder error recovery
  - Provide tuning recommendations
- [x] Add logging documentation:
  - Explain decoder error logs
  - Explain validation failure logs
  - Explain error rate thresholds
- [ ] Create troubleshooting guide:
  - Common H.264 decoder errors
  - How to adjust RTSP_MAX_CONSECUTIVE_ERRORS
  - When to switch transport protocol
  - Impact of decoder errors on motion detection
- [ ] Add monitoring recommendations:
  - What error rate is acceptable (< 5%)
  - When to investigate high error rates (> 10%)
  - How decoder errors correlate with motion detection

## Dependencies and Sequencing

**Phase 1 must complete before:**
- Phase 2 (validation requires updated CameraState)
- Phase 3 (error handling requires RTSP config)
- All subsequent phases

**Phase 2 must complete before:**
- Phase 3 (error handling uses validation)
- Phase 4 (tracking validated frames)

**Phase 3 must complete before:**
- Phase 4 (error tracking integrated with handling)

**Phase 4 must complete before:**
- Phase 5 (health monitoring uses tracked stats)

**Phase 6 depends on:**
- All previous phases complete
- Test environment setup

**Phase 7 can run in parallel with:**
- Phase 6 (documentation while testing)

## Parallelizable Work
- Phase 7 tasks (documentation) can be done alongside development
- Unit tests for each phase can be written alongside implementation
- Mock RTSP stream setup (Phase 6) can be started early

## Estimated Effort
- Phase 1: 4 hours
- Phase 2: 3 hours
- Phase 3: 5 hours
- Phase 4: 2 hours
- Phase 5: 3 hours
- Phase 6: 6 hours
- Phase 7: 3 hours

**Total: ~26 hours**

## Success Criteria
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] End-to-end test with error injection passes
- [ ] Manual testing with user's camera shows improved reliability
- [ ] Decoder errors are logged but don't trigger reconnections
- [ ] Motion detection continues working with occasional errors
- [ ] Health metrics accurately reflect decoder error rate
- [ ] Performance overhead is minimal (< 10ms per frame)
- [ ] Documentation is complete and clear
