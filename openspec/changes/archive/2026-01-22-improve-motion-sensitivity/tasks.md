# Tasks: Improve Motion Detection Sensitivity

## Phase 1: Algorithm Tuning (High Priority)

- [x] 1. **Reduce preprocessing blur in MotionDetector**
  - Made blur configurable via parameters
  - LOW: (5,5), MEDIUM: (3,3), HIGH: (3,3) with lower threshold
  - Note: GaussianBlur requires odd kernel sizes
  - Updated to preserve more detail for better outdoor detection

- [x] 2. **Lower binary threshold for pixel difference**
  - Reduced threshold from 15 to 10 in `_calculate_pixel_difference`
  - Made threshold configurable via parameters
  - Improved sensitivity to subtle changes

- [x] 3. **Increase pixel difference scale factor**
  - Changed scale factor from 10 to 15 in `_calculate_pixel_difference`
  - Made scale factor configurable via parameters
  - Better amplification of outdoor motion scores

- [x] 4. **Tune MOG2 background subtractor parameters**
  - Reduced `varThreshold` from 16 to 10
  - Increased `history` from 200 to 500
  - Made both parameters configurable

- [x] 5. **Add unit tests for improved sensitivity**
  - Added test for vehicle lateral movement detection
  - Added test for person walking detection
  - Added test for static outdoor scene filtering
  - Added test for expected score ranges

## Phase 2: Configuration & Presets (Medium Priority)

- [x] 6. **Add motion_sensitivity field to Camera table**
  - Added motion_sensitivity field to Camera model (String(20), default="medium")
  - Created database migration (003_add_motion_sensitivity.py)
  - Updated CameraConfig dataclass with motion_sensitivity field

- [x] 7. **Add motion_sensitivity to CameraRepository**
  - Added motion_sensitivity parameter to create() method
  - Added motion_sensitivity parameter to update() method
  - Default value set to "medium"

- [x] 8. **Implement sensitivity presets in MotionDetector**
  - Defined SENSITIVITY_PRESETS dict with low/medium/high parameters
  - Refactored __init__ to accept all configurable parameters
  - Added from_sensitivity() classmethod factory
  - Updated reset() to use configured parameters

- [x] 9. **Update adjust_threshold.py to support sensitivity**
  - Added sensitivity preset options (LOW/MEDIUM/HIGH)
  - Shows current sensitivity level for each camera
  - Updated UI to display expected detection results
  - Supports updating both sensitivity and threshold

## Phase 3: Debugging & Visualization (Low Priority)

- [x] 10. **Create motion visualization tool**
  - Created `tools/visualize_motion.py`
  - Processes video and shows motion masks overlay
  - Displays motion scores on each frame
  - Saves visualization video + histogram
  - Supports comparison of all sensitivities with `--all-sensitivities`

- [x] 11. **Add debug mode to MotionDetector**
  - Added `debug=True` parameter to __init__
  - Added `debug_dir` parameter for custom debug location
  - Saves 5 types of debug frames: preprocessed, pixel_diff, pixel_thresh, bg_sub_raw, bg_sub_thresh
  - Detailed debug logging with all parameters
  - Auto-cleanup of old files (> 24h or > 100MB)

- [x] 12. **Create calibration CLI tool**
  - Created `tools/calibrate_motion.py`
  - Interactive OpenCV window with live camera feed
  - Real-time adjustment of sensitivity (1/2/3 keys)
  - Toggle masks visualization (m/p/b keys)
  - Save configuration to database with hot-reload (s key)
  - Works with camera ID or direct RTSP URL

## Phase 4: Testing & Validation (Continuous)

- [x] 13. **Create benchmark test dataset**
  - Created structure in `tests/fixtures/videos/`
  - Created `ground_truth.json` with expected metrics per video
  - Documented expected detection rates per sensitivity
  - Added README with instructions for adding test videos
  - Defined 5 test scenarios: vehicle_lateral, vehicle_frontal, person_walking, static_outdoor, false_positives

- [x] 14. **Add integration test with benchmark data**
  - Created `tests/test_motion_benchmark.py`
  - Tests for vehicle detection, false positives, sensitivity comparison
  - Performance benchmark test (< 50ms per frame)
  - Parametrized test for all videos × all sensitivities
  - Validates against ground truth expectations

- [x] 15. **Update documentation**
  - Created comprehensive `docs/MOTION_DETECTION.md`
  - Documented all sensitivity levels and parameters
  - Added troubleshooting section with common problems
  - Documented all CLI tools (visualize, calibrate, adjust_threshold)
  - API reference for MotionDetector
  - Expected scores table for different scenarios
  - Best practices guide

## Dependencies

- Tasks 1-5 can run in parallel
- Task 6 must complete before task 7
- Task 8 depends on task 6-7
- Task 9 depends on task 8
- Tasks 10-12 are independent and can run in parallel
- Task 13 should start early and can run in parallel with Phase 1
- Task 14 depends on task 13
