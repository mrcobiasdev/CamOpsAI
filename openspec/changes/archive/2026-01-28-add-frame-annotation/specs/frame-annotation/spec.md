# frame-annotation Specification

## Purpose
Generate visual annotations on captured frames to assist in human auditing and verification of detection events. Annotated frames display motion detection results and LLM analysis overlays.

## ADDED Requirements

### Requirement: Frame Annotation Configuration
The system SHALL support configurable frame annotation with enable/disable control and visual customization options.

#### Scenario: Enable frame annotation
- **GIVEN** annotation is disabled in settings
- **WHEN** `annotation_enabled` is set to true
- **THEN** all processed frames shall have annotated versions generated
- **AND** annotated frames shall be stored in separate directory

#### Scenario: Disable frame annotation
- **GIVEN** annotation is enabled in settings
- **WHEN** `annotation_enabled` is set to false
- **THEN** no annotated frames shall be generated
- **AND** only original frames shall be stored
- **AND** `annotated_frame_path` shall be null in Event records

#### Scenario: Configure annotation visual style
- **GIVEN** annotation is enabled
- **WHEN** visual settings are configured (mask_alpha, mask_color, text_color)
- **THEN** annotated frames shall use the configured visual style
- **AND** settings shall apply immediately without restart

#### Scenario: Configure storage path
- **GIVEN** annotation is enabled
- **WHEN** `annotated_frames_storage_path` is set to a custom directory
- **THEN** annotated frames shall be stored in the configured directory
- **AND** directory shall be created automatically if it doesn't exist

### Requirement: Motion Information Overlay
The system SHALL overlay motion detection information on annotated frames including score, threshold, status, and visual mask.

#### Scenario: Display motion score and threshold
- **GIVEN** a frame has motion_score = 45.2% and motion_threshold = 10.0%
- **WHEN** annotation is generated
- **THEN** annotated frame shall display "Score: 45.2%  Threshold: 10.0%"
- **AND** text shall be in white color at top of image
- **AND** score shall be highlighted if >= threshold

#### Scenario: Display motion status indicator
- **GIVEN** motion_score >= motion_threshold
- **WHEN** annotation is generated
- **THEN** annotated frame shall display "MOTION" badge in green
- **AND** badge shall be located at top-left corner

#### Scenario: Display no motion status
- **GIVEN** motion_score < motion_threshold
- **WHEN** annotation is generated
- **THEN** annotated frame shall display "NO MOTION" badge in red
- **AND** badge shall be located at top-left corner

#### Scenario: Overlay motion mask on frame
- **GIVEN** motion detection detected activity in specific regions
- **WHEN** annotation is generated
- **THEN** annotated frame shall display colored mask overlay on detected regions
- **AND** mask shall use COLORMAP_HOT or similar colormap for visibility
- **AND** mask shall have transparency (alpha = 0.3)
- **AND** mask shall be blended with original frame (70% original, 30% mask)

#### Scenario: Missing motion data
- **GIVEN** motion detection data is unavailable
- **WHEN** annotation is generated
- **THEN** annotated frame shall display "Motion Score: N/A"
- **AND** motion status shall show "UNKNOWN"
- **AND** no motion mask shall be displayed
- **AND** LLM data shall still be displayed if available

### Requirement: LLM Information Overlay
The system SHALL overlay LLM analysis results on annotated frames including keywords, confidence, provider, and model.

#### Scenario: Display detected keywords
- **GIVEN** LLM analysis returned keywords ["person", "walking", "entrance"]
- **WHEN** annotation is generated
- **THEN** annotated frame shall display "Keywords: person, walking, entrance"
- **AND** text shall be in yellow for visibility
- **AND** keywords shall be truncated if too long (max 100 chars)

#### Scenario: Display confidence score
- **GIVEN** LLM analysis returned confidence = 0.92
- **WHEN** annotation is generated
- **THEN** annotated frame shall display "Confidence: 92%"
- **AND** confidence shall be displayed as percentage
- **AND** confidence shall be shown in green if >= 80%, yellow if >= 50%, red otherwise

#### Scenario: Display provider and model information
- **GIVEN** LLM analysis used provider="openai" and model="gpt-4-vision-preview"
- **WHEN** annotation is generated
- **THEN** annotated frame shall display "Provider: OpenAI (GPT-4V)"
- **AND** display name shall be formatted for readability

#### Scenario: Missing LLM data
- **GIVEN** LLM analysis failed or returned no results
- **WHEN** annotation is generated
- **THEN** annotated frame shall display "LLM Analysis: Failed"
- **AND** no keywords or confidence shall be displayed
- **AND** motion data shall still be displayed if available

### Requirement: Frame Annotation Generation
The system SHALL generate annotated versions of all processed frames with both motion and LLM information overlays.

#### Scenario: Annotate processed frame
- **GIVEN** a frame passes motion detection and LLM analysis completes
- **WHEN** `process_frame()` finishes
- **THEN** annotated version shall be generated from original frame
- **AND** annotated frame shall include motion information overlay
- **AND** annotated frame shall include LLM information overlay
- **AND** annotated frame shall be saved as separate file

#### Scenario: Annotation performance requirement
- **GIVEN** a 1920x1080 JPEG frame
- **WHEN** annotation is generated
- **THEN** annotation generation time shall be < 100ms
- **AND** generation shall not block frame processing queue
- **AND** performance shall be logged if > 100ms

#### Scenario: Annotation error handling
- **GIVEN** annotation generation fails (e.g., invalid frame data)
- **WHEN** error occurs
- **THEN** error shall be logged with details
- **AND** original frame shall still be saved
- **AND** Event shall be created with `annotated_frame_path` = null
- **AND** frame processing shall continue normally

#### Scenario: Asynchronous saving
- **GIVEN** annotated frame is generated
- **WHEN** save operation starts
- **THEN** save shall be performed asynchronously
- **AND** save operation shall not block frame processing
- **AND** save failure shall be logged but not interrupt processing

### Requirement: Annotated Frame Storage
The system SHALL store annotated frames as separate files with a consistent naming convention and automatic cleanup.

#### Scenario: Store annotated frame with suffix
- **GIVEN** original frame is saved as "abc123_1706353935000.jpg"
- **WHEN** annotated frame is saved
- **THEN** annotated frame shall be saved as "abc123_1706353935000_annotated.jpg"
- **AND** both files shall exist in storage

#### Scenario: Separate storage directory
- **GIVEN** `annotated_frames_storage_path` = "data/annotated_frames"
- **WHEN** annotated frame is saved
- **THEN** annotated frame shall be stored in "data/annotated_frames/"
- **AND** original frames shall remain in "data/frames/"
- **AND** both directories shall be created automatically

#### Scenario: Event record includes annotated path
- **GIVEN** annotated frame is saved at "data/annotated_frames/abc123_1706353935000_annotated.jpg"
- **WHEN** Event is created in database
- **THEN** `annotated_frame_path` shall contain full path to annotated frame
- **AND** `frame_path` shall still contain path to original frame
- **AND** both paths shall be included in Event record

#### Scenario: Cleanup old annotated frames
- **GIVEN** `annotation_retention_days` = 30
- **AND** annotated frames older than 30 days exist
- **WHEN** cleanup runs (on startup or periodically)
- **THEN** annotated frames older than 30 days shall be deleted
- **AND** cleanup shall be logged
- **AND** original frames shall not be affected by annotation cleanup

#### Scenario: Handle missing annotated file
- **GIVEN** Event has `annotated_frame_path` but file doesn't exist
- **WHEN** API request tries to retrieve annotated frame
- **THEN** system shall return 404 error
- **AND** error message shall indicate "Annotated frame not found"
- **AND** original frame shall still be retrievable

### Requirement: Annotated Frame Retrieval
The system SHALL provide API endpoints to retrieve annotated frames for events.

#### Scenario: Retrieve annotated frame via API
- **GIVEN** an Event exists with `annotated_frame_path`
- **WHEN** GET `/api/v1/events/{event_id}/annotated-frame` is called
- **THEN** system shall return annotated frame as JPEG
- **AND** Content-Type shall be "image/jpeg"
- **AND** response shall return 200 OK

#### Scenario: Return 404 for missing annotated frame
- **GIVEN** an Event exists without `annotated_frame_path`
- **WHEN** GET `/api/v1/events/{event_id}/annotated-frame` is called
- **THEN** system shall return 404 Not Found
- **AND** error message shall be "Annotated frame not found"

#### Scenario: Retrieve annotated frame with event details
- **GIVEN** an Event exists with annotated frame
- **WHEN** GET `/api/v1/events/{event_id}` is called
- **THEN** response shall include `annotated_frame_url` field
- **AND** URL shall point to `/api/v1/events/{event_id}/annotated-frame`
- **AND** URL shall be null if no annotated frame exists

### Requirement: Database Schema Update
The system SHALL extend the Event model to include annotated frame path.

#### Scenario: Add annotated_frame_path column
- **GIVEN** the Event model exists
- **WHEN** database migration runs
- **THEN** `annotated_frame_path` column shall be added to events table
- **AND** column type shall be String(512)
- **AND** column shall be nullable
- **AND** existing events shall have null values for new column

#### Scenario: Create Event with annotated path
- **GIVEN** annotated frame is saved successfully
- **WHEN** Event is created
- **THEN** `annotated_frame_path` shall contain the file path
- **AND** field shall be persisted to database
- **AND** field shall be retrievable in future queries

#### Scenario: Create Event without annotated path
- **GIVEN** annotation is disabled or failed
- **WHEN** Event is created
- **THEN** `annotated_frame_path` shall be null
- **AND** Event shall be created successfully
- **AND** original `frame_path` shall still be populated

### Requirement: MotionDetector Enhancement
The system SHALL extend MotionDetector to provide motion mask data for annotation.

#### Scenario: Store last motion mask
- **GIVEN** MotionDetector is processing frames
- **WHEN** `detect_motion()` is called
- **THEN** method shall store generated motion mask in `_last_mask`
- **AND** mask shall represent detected motion regions
- **AND** mask shall be available for annotation

#### Scenario: Retrieve last motion mask
- **GIVEN** MotionDetector has processed a frame
- **WHEN** `get_last_mask()` is called
- **THEN** method shall return the stored motion mask
- **AND** mask shall be in original frame dimensions
- **AND** mask shall be None if no frame processed yet

#### Scenario: Generate motion mask for annotation
- **GIVEN** pixel_diff and bg_sub masks are calculated
- **WHEN** motion mask is generated
- **THEN** mask shall combine pixel_diff and bg_sub results
- **AND** mask shall use same coordinate system as original frame
- **AND** mask shall be suitable for overlay visualization
