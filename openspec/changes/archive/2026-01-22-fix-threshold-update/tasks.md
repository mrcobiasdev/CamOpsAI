# Tasks: Fix Threshold Update Not Working

## Task 1: Add update_config() method to FrameGrabber - [x]
**File**: `src/capture/frame_grabber.py`
**Description**: Add a method to update camera configuration at runtime
**Steps**:
1. Add `update_config(new_config: CameraConfig)` method to `FrameGrabber` class
2. Store old threshold value before updating
3. Update `self.config` with new configuration
4. Compare old vs new threshold
5. Reinitialize `MotionDetector` if threshold changed and motion detection is enabled
6. Add log message for successful update
**Dependencies**: None
**Estimated time**: 15 minutes
**Acceptance criteria**:
- Method accepts `CameraConfig` object
- Updates `self.config`
- Reinitializes `MotionDetector` when threshold changes
- Thread-safe implementation

## Task 2: Add update_camera_config() to CameraManager - [x]
**File**: `src/main.py`
**Description**: Add method to update running grabber configurations
**Steps**:
1. Add `update_camera_config(camera_id: uuid.UUID)` method to `CameraManager` class
2. Retrieve grabber from `_grabbers` dictionary
3. Fetch fresh camera data from database
4. Convert database `Camera` to `CameraConfig` dataclass
5. Call `grabber.update_config(config)`
6. Return True on success, False on failure
**Dependencies**: Task 1
**Estimated time**: 20 minutes
**Acceptance criteria**:
- Method retrieves running grabber
- Fetches latest camera data from database
- Creates `CameraConfig` object correctly
- Calls `grabber.update_config()`
- Handles missing grabber gracefully

## Task 3: Update adjust_threshold.py to call update_camera_config() - [x]
## Task 3.5: Fix SQLAlchemy flush() bug in repository - [x]
## Task 3.5: Fix SQLAlchemy flush() bug in repository - [x]
**File**: `src/storage/repository.py`
**Description**: Replace all `flush()` calls with `commit()` to ensure database writes are persisted
**Steps**:
1. Search for all occurrences of `await self.session.flush()`
2. Replace with `await self.session.commit()` (9 occurrences)
3. Verify all create/update/delete operations use commit()
**Dependencies**: None
**Estimated time**: 5 minutes
**Acceptance criteria**:
- All `flush()` replaced with `commit()`
- Database writes are persisted immediately
- Changes reflect in subsequent queries
**File**: `adjust_threshold.py`
**Description**: Update script to call camera manager after database update
**Steps**:
1. Import `camera_manager` from `src.main` (or make it accessible)
2. After database update loop, add new loop to update grabbers
3. Call `await camera_manager.update_camera_config(cam.id)` for each camera
4. Update success message to mention "em execução" (in execution)
**Dependencies**: Task 2
**Estimated time**: 10 minutes
**Acceptance criteria**:
- Calls `update_camera_config()` after database update
- Running grabbers reflect new threshold
- Success message indicates change took effect immediately

## Task 4: Add thread-safety to update_config() - [x]
**File**: `src/capture/frame_grabber.py`
**Description**: Ensure config updates are thread-safe
**Steps**:
1. Add `asyncio.Lock()` to `FrameGrabber.__init__()`
2. Use lock in `update_config()` method
3. Acquire lock before updating config and reinitializing detector
4. Release lock after update completes
**Dependencies**: Task 1
**Estimated time**: 10 minutes
**Acceptance criteria**:
- Lock prevents race conditions
- Multiple simultaneous updates don't cause crashes
- Logs warning if concurrent update attempted

## Task 5: Test threshold update with running camera
**File**: Manual testing
**Description**: Verify threshold changes take effect immediately
**Steps**:
1. Start application and begin capturing a camera
2. Run `python adjust_threshold.py`
3. Select option 4 (threshold 10.0)
4. Check logs for "Motion detector reinitialized" message
5. Verify motion detection uses new threshold (check log "threshold=10.0%")
6. Repeat with option 3 (threshold 5.0)
7. Confirm logs show "threshold=5.0%"
**Dependencies**: Task 3
**Estimated time**: 15 minutes
**Acceptance criteria**:
- Threshold changes immediately affect motion detection
- No application restart required
- Logs show correct threshold value
- Motion detector uses new threshold

## Task 6: Test all threshold options
**File**: Manual testing
**Description**: Test all preset threshold options
**Steps**:
1. Test option 1 (1.0% - very sensitive)
2. Test option 2 (3.0% - sensitive)
3. Test option 3 (5.0% - normal)
4. Test option 4 (10.0% - conservative)
5. Test option 6 (custom value, e.g., 15.0%)
6. Test option 5 (disable motion detection)
7. Re-enable and verify it works
**Dependencies**: Task 5
**Estimated time**: 20 minutes
**Acceptance criteria**:
- All options apply correctly
- Custom values work
- Disable/enable toggle works
- No errors in logs

## Task 7: Update documentation
**File**: `README.md` (if needed)
**Description**: Document the hot-reload feature
**Steps**:
1. Check if threshold adjustment is documented
2. Add note about immediate effect without restart
3. Update troubleshooting section if needed
**Dependencies**: Task 6
**Estimated time**: 10 minutes
**Acceptance criteria**:
- Documentation reflects new behavior
- Users know no restart is needed
- Troubleshooting includes threshold update issues

## Task 8: Create automated test (optional)
**File**: `tests/test_threshold_update.py` (new file)
**Description**: Create automated test for threshold update
**Steps**:
1. Create test that starts a grabber
2. Update camera config in database
3. Call `update_camera_config()`
4. Verify grabber uses new threshold
5. Mock database and motion detector
**Dependencies**: Task 2
**Estimated time**: 30 minutes
**Acceptance criteria**:
- Test passes with mock objects
- Threshold value is verified
- Test can be run with pytest

## Order of Execution

1. **Task 1** - Core method implementation
2. **Task 2** - Manager integration
3. **Task 4** - Thread safety
4. **Task 3** - Script update
5. **Task 5** - Manual verification
6. **Task 6** - Comprehensive testing
7. **Task 7** - Documentation
8. **Task 8** - Automated tests (optional)

## Parallelizable Work

- Tasks 1, 2, 3, 4 can be done sequentially (dependencies)
- Task 5 and 6 can be done in parallel (both manual testing)
- Task 7 can be done after Task 6
- Task 8 can be done independently after Task 2

## Total Estimated Time

- **MVP (Tasks 1-6)**: 90 minutes (1.5 hours)
- **Complete (Tasks 1-7)**: 100 minutes (1.7 hours)
- **With Tests (Tasks 1-8)**: 130 minutes (2.2 hours)
