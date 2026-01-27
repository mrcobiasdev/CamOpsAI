# Implementation Tasks

## Phase 1: Database Schema
- [x] 1. Add `motion_threshold` column to `cameras` table (default: 10.0)
- [x] 2. Add `motion_detection_enabled` column to `cameras` table (default: true)
- [x] 3. Create migration script for new columns
- [x] 4. Update CameraConfig model to include motion detection settings
- [x] 5. Update API schemas to expose new fields

## Phase 2: Motion Detection Module
- [x] 6. Create `src/capture/motion_detector.py` module
- [x] 7. Implement `MotionDetector` class with hybrid detection algorithm
- [x] 8. Implement pixel difference method (baseline comparison)
- [x] 9. Implement background subtraction method (MOG2 from OpenCV)
- [x] 10. Combine both methods with configurable weights
- [x] 11. Add performance optimization (frame downsampling, region of interest)

## Phase 3: Integration with FrameGrabber
- [x] 12. Store previous frame in FrameGrabber state
- [x] 13. Add MotionDetector instance to FrameGrabber
- [x] 14. Check motion before calling `on_frame` callback
- [x] 15. Log motion detection results (threshold, detected motion, filtered)
- [x] 16. Add statistics tracking (frames captured, frames sent, frames filtered)

## Phase 4: Configuration & API
- [x] 17. Update camera creation/update API endpoints to accept motion settings
- [x] 18. Update camera response to include motion detection stats
- [x] 19. Add environment variables for global defaults
- [x] 20. Test motion detection with static scene
- [x] 21. Test motion detection with moving objects
- [x] 22. Test threshold sensitivity with various values

## Phase 5: Monitoring & Logging
- [x] 23. Add logging for motion detection events
- [x] 24. Add stats endpoint for motion detection metrics
- [x] 25. Add alert when motion detection is failing (0% or 100% detection)
- [x] 26. Document motion detection behavior in API docs

## Phase 6: Validation & Testing
- [x] 27. Write unit tests for MotionDetector
- [x] 28. Write integration tests with FrameGrabber
- [x] 29. Performance test overhead (< 50ms per frame)
- [x] 30. Edge case testing (low light, noise, camera reconnection)
- [x] 31. Validate API call reduction in test environment

## Dependencies
- Phase 1: None (can start immediately)
- Phase 2: Depends on Phase 1 (for CameraConfig)
- Phase 3: Depends on Phase 2
- Phase 4: Depends on Phase 3
- Phase 5: Depends on Phase 3
- Phase 6: Depends on Phase 3

## Parallelizable Work
- Phase 2 tasks 7-11 can be done in parallel with database work
- Phase 4 tasks 20-22 can be done independently
- Phase 6 unit tests can be written during Phase 2
