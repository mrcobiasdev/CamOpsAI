# Frame Annotation Design

## Architecture Overview

The frame annotation system will integrate into the existing frame processing pipeline:

```
FrameGrabber → FrameQueue → process_frame() → [LLM Analysis] → Event Creation
                                                      ↓
                                              [FrameAnnotation]
                                                      ↓
                                            Save Annotated Frame
```

## Components

### 1. FrameAnnotation Class
A new class responsible for generating annotated frames:

**Location**: `src/capture/frame_annotation.py`

**Responsibilities**:
- Take original frame (JPEG bytes) and analysis data
- Generate motion visualization (mask, score, threshold, status)
- Generate LLM annotation (keywords, confidence, provider/model)
- Combine original frame with visual overlays
- Return annotated frame as JPEG bytes

**Key Methods**:
```python
class FrameAnnotation:
    def __init__(
        self,
        motion_score: float,
        motion_threshold: float,
        motion_mask: Optional[np.ndarray],
        llm_keywords: List[str],
        llm_confidence: Optional[float],
        llm_provider: Optional[str],
        llm_model: Optional[str],
        motion_status: str = "MOTION" | "NO MOTION"
    )

    def annotate_frame(self, frame_bytes: bytes) -> bytes:
        """Generate annotated frame from original frame bytes."""

    def _add_motion_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Add motion mask and status information."""

    def _add_llm_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Add LLM analysis results overlay."""
```

### 2. Integration with process_frame()

Modify the existing `process_frame()` function in `src/main.py`:

```python
async def process_frame(item: FrameItem):
    """Processa um frame capturado."""
    try:
        # Get camera and motion data
        grabber = camera_manager._grabbers.get(item.camera_id)
        motion_score = grabber.state.last_motion_score if grabber else None
        motion_threshold = grabber.config.motion_threshold if grabber else None

        # LLM analysis
        result = await llm.analyze_frame(item.frame_data)

        # Generate motion mask (if available)
        motion_mask = None
        if grabber and grabber._motion_detector:
            # Need to retrieve motion mask from detector
            motion_mask = grabber._motion_detector.get_last_mask()

        # Create annotation
        annotator = FrameAnnotation(
            motion_score=motion_score,
            motion_threshold=motion_threshold,
            motion_mask=motion_mask,
            llm_keywords=result.keywords,
            llm_confidence=result.confidence,
            llm_provider=result.provider,
            llm_model=result.model,
            motion_status="MOTION" if motion_score >= motion_threshold else "NO MOTION"
        )

        # Generate annotated frame
        annotated_bytes = annotator.annotate_frame(item.frame_data)

        # Save both original and annotated frames
        original_path = save_frame(item.frame_data, item.camera_id, item.timestamp)
        annotated_path = save_annotated_frame(annotated_bytes, item.camera_id, item.timestamp)

        # Save event with both frame paths
        event = await event_repo.create(
            camera_id=item.camera_id,
            description=result.description,
            keywords=result.keywords,
            frame_path=original_path,
            annotated_frame_path=annotated_path,  # NEW FIELD
            confidence=result.confidence,
            ...
        )
```

### 3. Database Schema Update

Add `annotated_frame_path` field to `Event` model in `src/storage/models.py`:

```python
class Event(Base):
    # ... existing fields ...
    annotated_frame_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
```

### 4. MotionDetector Enhancement

Add method to retrieve last motion mask for annotation:

```python
class MotionDetector:
    def __init__(self, ...):
        # ... existing ...
        self._last_mask: Optional[np.ndarray] = None

    def detect_motion(self, frame: np.ndarray) -> Tuple[float, bool]:
        # ... existing logic ...

        # Store mask for annotation
        self._last_mask = self._generate_motion_mask(frame)

        return motion_score, has_motion

    def get_last_mask(self) -> Optional[np.ndarray]:
        """Return the last motion mask generated."""
        return self._last_mask

    def _generate_motion_mask(self, frame: np.ndarray) -> np.ndarray:
        """Generate motion mask visualization."""
        # Combine pixel_diff and bg_sub masks
        # Return upsampled mask matching original frame dimensions
```

### 5. Configuration

Add annotation settings to `src/config/settings.py`:

```python
class Settings(BaseSettings):
    # ... existing ...

    # Frame annotation
    annotation_enabled: bool = True
    annotation_mask_alpha: float = 0.3  # Transparency of motion mask (0.0-1.0)
    annotation_mask_color: Tuple[int, int, int] = (0, 255, 0)  # Green
    annotation_text_color: Tuple[int, int, int] = (255, 255, 255)  # White
    annotation_font_scale: float = 0.6
    annotation_thickness: int = 2
    annotated_frames_storage_path: str = "data/annotated_frames"
```

### 6. API Endpoint

Add endpoint to retrieve annotated frame in `src/api/routes/events.py`:

```python
@router.get("/events/{event_id}/annotated-frame")
async def get_annotated_frame(event_id: uuid.UUID):
    """Return the annotated frame for an event."""
    async with AsyncSessionLocal() as session:
        event_repo = EventRepository(session)
        event = await event_repo.get_by_id(event_id)

        if not event or not event.annotated_frame_path:
            raise HTTPException(status_code=404, detail="Annotated frame not found")

        return FileResponse(event.annotated_frame_path, media_type="image/jpeg")
```

## Visualization Design

### Layout

```
┌─────────────────────────────────────────────────┐
│ [MOTION]  Score: 45.2%  Threshold: 10%       │
│ Keywords: person, walking, entrance            │
│ Confidence: 92%  Provider: OpenAI (GPT-4V)    │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │                                         │    │
│  │         Original Frame                   │    │
│  │         + Motion Mask (green overlay)    │    │
│  │                                         │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│ [Timestamp: 2024-01-27 14:32:15]             │
└─────────────────────────────────────────────────┘
```

### Visual Elements

1. **Motion Mask Overlay**:
   - Colored semi-transparent overlay (green = motion, default)
   - Areas with motion shown with `cv2.applyColorMap()` using COLORMAP_HOT
   - Alpha blending: 70% original, 30% mask

2. **Motion Status Badge**:
   - Top-left corner
   - Green background/text for MOTION
   - Red background/text for NO MOTION

3. **Motion Score & Threshold**:
   - Next to status badge
   - Format: "Score: X.X%  Threshold: Y.Y%"

4. **Keywords**:
   - Below motion info
   - Comma-separated, truncated if too long
   - Yellow text for visibility

5. **Confidence & Provider**:
   - Bottom of text overlay
   - Format: "Confidence: X%  Provider: Y (Z)"

6. **Timestamp**:
   - Bottom of image
   - Gray text, smaller font

## Storage Strategy

### File Naming
- Original: `{camera_id}_{timestamp_ms}.jpg`
- Annotated: `{camera_id}_{timestamp_ms}_annotated.jpg`

### Directory Structure
```
data/
├── frames/                    # Original frames
│   └── {camera_id}_{timestamp}.jpg
└── annotated_frames/          # Annotated frames
    └── {camera_id}_{timestamp}_annotated.jpg
```

### Cleanup Policy
- Use same cleanup as original frames (if exists)
- Add configuration: `annotation_retention_days` (default: 30 days)
- Cleanup runs on application startup and periodically

## Performance Considerations

1. **Annotation Overhead**:
   - Target: <100ms per frame
   - Operations: image decode → overlay generation → image encode
   - Optimization: Reuse color maps, pre-allocate text rendering objects

2. **Async Storage**:
   - Save annotated frame asynchronously to avoid blocking processing
   - Use separate task: `asyncio.create_task(save_annotated_frame(...))`

3. **Conditional Annotation**:
   - Check `settings.annotation_enabled` before generating
   - Skip annotation if disabled

## Error Handling

1. **Annotation Failure**:
   - Log error with details
   - Continue processing without annotation
   - Save original frame normally
   - Set `annotated_frame_path` to None

2. **Missing Motion Data**:
   - If motion score/mask unavailable, show "N/A" in annotation
   - Still process LLM data

3. **Missing LLM Data**:
   - If LLM analysis failed, show only motion data
   - Indicate "LLM Analysis Failed" in annotation

## Testing Strategy

1. **Unit Tests**:
   - Test `FrameAnnotation` class methods
   - Test visualization rendering
   - Test error handling

2. **Integration Tests**:
   - Test full pipeline with real frames
   - Test API endpoint
   - Test database storage

3. **Performance Tests**:
   - Benchmark annotation time
   - Verify overhead <100ms
   - Test with multiple concurrent frames

4. **Visual Tests**:
   - Manual review of annotated frames
   - Verify overlays are readable
   - Test with various motion scenarios
