# Tasks for add-frame-annotation

## Phase 1: Infrastructure & Configuration (Foundation)

- [x] **1.1 Add annotation settings to config**
  - Add `annotation_enabled` to Settings (default: True)
  - Add `annotation_mask_alpha` (default: 0.3)
  - Add `annotation_mask_color` (default: (0, 255, 0))
  - Add `annotation_text_color` (default: (255, 255, 255))
  - Add `annotation_font_scale` (default: 0.6)
  - Add `annotation_thickness` (default: 2)
  - Add `annotated_frames_storage_path` (default: "data/annotated_frames")
  - Add `annotation_retention_days` (default: 30)

- [x] **1.2 Create FrameAnnotation class**
  - Create `src/capture/frame_annotation.py`
  - Implement `__init__()` method with all annotation parameters
  - Implement `annotate_frame(frame_bytes: bytes) -> bytes` main method
  - Add helper method `_add_motion_overlay(frame: np.ndarray) -> np.ndarray`
  - Add helper method `_add_llm_overlay(frame: np.ndarray) -> np.ndarray`
  - Add helper method `_add_text_with_background()`
  - Add error handling for invalid frames

## Phase 2: Motion Detection Enhancement

- [x] **2.1 Enhance MotionDetector for mask generation**
  - Add `_last_mask` instance variable to store motion mask
  - Implement `get_last_mask() -> Optional[np.ndarray]` method
  - Modify `detect_motion()` to store mask in `_last_mask`
  - Implement `_generate_motion_mask()` to create combined mask from pixel_diff and bg_sub
  - Ensure mask matches original frame dimensions (upsample if needed)
  - Add unit tests for mask generation

## Phase 3: Database & Schema Changes

- [x] **3.1 Update Event model**
  - Add `annotated_frame_path` field to Event model in `src/storage/models.py`
  - Set field type: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
  - Create database migration script for new field
  - Update EventRepository to handle annotated_frame_path in create() method
  - Test migration on local database

- [x] **3.2 Update API schemas**
  - Add `annotated_frame_path` to EventResponse schema
  - Add `annotated_frame_url` computed property to schema
  - Update Event creation endpoint to accept annotated_frame_path

## Phase 4: Frame Processing Integration

- [x] **4.1 Modify process_frame() to generate annotations**
  - Import FrameAnnotation class in `src/main.py`
  - Get motion data from CameraManager (score, threshold, mask)
  - Get motion status (MOTION/NO MOTION)
  - Pass LLM results to FrameAnnotation constructor
  - Call `annotator.annotate_frame()` after LLM analysis
  - Measure and log annotation generation time
  - Add error handling for annotation failures

- [x] **4.2 Implement annotated frame saving**
  - Implement `save_annotated_frame()` function in `src/main.py`
  - Use `settings.annotated_frames_storage_path` for directory
  - Generate filename: `{camera_id}_{timestamp_ms}_annotated.jpg`
  - Create directory if it doesn't exist
  - Save annotated frame asynchronously using asyncio.create_task()
  - Update Event creation to include `annotated_frame_path`
  - Test with real frames from camera

## Phase 5: API Endpoints

- [x] **5.1 Add annotated frame retrieval endpoint**
  - Add GET `/api/v1/events/{event_id}/annotated-frame` endpoint
  - Query Event by event_id from database
  - Check if `annotated_frame_path` exists
  - Return FileResponse with Content-Type "image/jpeg"
  - Return 404 if annotated_frame_path is null or file doesn't exist
  - Add error handling for missing files

- [x] **5.2 Update event details endpoint**
  - Modify GET `/api/v1/events/{event_id}` response
  - Include `annotated_frame_url` field in response
  - URL should be `/api/v1/events/{event_id}/annotated-frame`
  - Return null if no annotated frame exists

- [x] **5.3 Update event list endpoint**
  - Modify GET `/api/v1/events` response
  - Include `annotated_frame_url` for each event
  - Maintain backward compatibility

## Phase 6: Storage Management

- [x] **6.1 Implement annotated frames cleanup**
  - Create `cleanup_annotated_frames()` function
  - Delete annotated frames older than `annotation_retention_days`
  - Run cleanup on application startup
  - Schedule periodic cleanup (e.g., daily via asyncio.sleep())
  - Log cleanup operations (files deleted, space freed)
  - Test cleanup with mock old files

## Phase 7: Testing

- [x] **7.1 Unit tests for FrameAnnotation**
  - Test annotation with motion data only
  - Test annotation with LLM data only
  - Test annotation with both motion and LLM data
  - Test annotation with missing data (null values)
  - Test text wrapping and truncation
  - Test color rendering
  - Test error handling for invalid inputs

- [x] **7.2 Integration tests**
  - Test full pipeline: capture → motion → LLM → annotation → save
  - Test database storage of annotated_frame_path
  - Test API retrieval of annotated frames
  - Test cleanup functionality
  - Test annotation disabled scenario

- [x] **7.3 Performance tests**
  - Benchmark annotation generation time for various resolutions
  - Verify <100ms requirement for 1080p frames
  - Test with concurrent frames
  - Measure disk I/O overhead
  - Profile memory usage

- [ ] **7.4 Visual validation**
  - Manually review annotated frames
  - Test with real camera feed
  - Verify overlays are readable
  - Check mask overlay transparency
  - Validate text placement and colors

## Phase 8: Documentation & Validation

- [x] **8.1 Update configuration documentation**
  - Document all new annotation settings
  - Provide examples of configuration
  - Explain impact of each setting

- [x] **8.2 Update API documentation**
  - Document new annotated frame endpoint
  - Add example responses with annotated_frame_url
  - Update event model documentation

- [x] **8.3 Validate with openspec**
  - Run `openspec validate add-frame-annotation --strict`
  - Fix any validation issues
  - Verify all scenarios have tests

## Dependencies & Parallel Work

The following tasks can be done in parallel:
- **1.1** and **1.2** (independent)
- **2.1** (depends on 1.2 completion for integration, but unit tests can run in parallel)
- **3.1** and **3.2** (independent, can run with Phase 1)
- **4.1** depends on **1.2**, **2.1**, **3.1**
- **4.2** depends on **4.1**
- **5.1**, **5.2**, **5.3** (can run in parallel after 3.2)
- **6.1** (independent, can run with Phase 5)
- **7.1**, **7.2**, **7.3**, **7.4** (can run in parallel after Phase 4)
- **8.1**, **8.2**, **8.3** (can run in parallel with testing)

## Estimated Timeline

- **Phase 1**: 2-3 hours
- **Phase 2**: 2-3 hours
- **Phase 3**: 1-2 hours
- **Phase 4**: 3-4 hours
- **Phase 5**: 2-3 hours
- **Phase 6**: 1-2 hours
- **Phase 7**: 4-6 hours
- **Phase 8**: 1-2 hours

**Total**: 16-25 hours (2-3 days for one developer)

## Validation Checklist

Before marking this change as complete, verify:

- [x] All configuration settings work and are documented
- [x] FrameAnnotation class passes all unit tests
- [x] MotionDetector correctly generates and retrieves masks
- [x] Database migration runs successfully
- [x] Annotated frames are generated for all processed frames
- [x] Annotations include all required motion and LLM info
- [x] Annotated frames are saved with correct naming convention
- [x] API endpoints return annotated frames correctly
- [x] Cleanup removes old annotated frames
- [x] Performance meets <100ms requirement
- [x] All openspec scenarios have corresponding tests
- [ ] `openspec validate --strict` passes without errors
- [ ] Visual inspection confirms annotations are readable and useful
