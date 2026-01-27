# Design: Improve Motion Detection Sensitivity

## Problem Analysis

The current motion detection algorithm uses a hybrid approach combining pixel difference and background subtraction. Real-world testing reveals it's too conservative for outdoor scenarios:

### Current Algorithm Flow
```
1. Preprocess: BGR → Grayscale → Resize(320x240) → GaussianBlur(3x3)
2. Pixel Diff: absdiff → threshold(15) → count pixels → scale(10x)
3. Background Sub: MOG2.apply → threshold(127) → count pixels → scale(3x)
4. Combine: 50% pixel_diff + 50% bg_sub → compare to threshold
```

### Identified Issues

1. **Over-smoothing**: GaussianBlur(3x3) removes fine details that indicate motion
2. **Threshold too high**: Binary threshold of 15 filters out subtle but real changes
3. **Under-amplification**: Scale factor of 10x insufficient for typical outdoor motion
4. **MOG2 too strict**: varThreshold=16 is conservative for variable outdoor lighting

### Why Current Parameters Fail for Street Cameras

- Vehicles moving laterally create pixel changes in the 5-15 range (grayscale diff)
- With threshold=15, only pixels with diff >= 15 are counted as "changed"
- A car might change 5-10% of pixels by 10-14 units → all filtered out
- Result: motion_score = 0-3% even when car passes

## Proposed Solution

### Algorithm Parameter Adjustments

| Parameter | Current | Proposed | Rationale |
|-----------|---------|----------|-----------|
| GaussianBlur kernel | (3,3) | (2,2) | Preserve more detail, less smoothing |
| Pixel diff threshold | 15 | 10 | Detect subtler changes (10-15 range) |
| Pixel diff scale | 10x | 15x | Amplify outdoor motion scores |
| MOG2 varThreshold | 16 | 10 | More sensitive to foreground changes |
| MOG2 history | 200 | 500 | Better adapt to outdoor lighting |

### Sensitivity Presets

Instead of manual parameter tuning, provide presets:

```python
SENSITIVITY_PRESETS = {
    "low": {
        "blur_kernel": (3, 3),
        "pixel_threshold": 20,
        "pixel_scale": 8,
        "bg_var_threshold": 20,
        "bg_history": 300,
    },
    "medium": {  # DEFAULT
        "blur_kernel": (2, 2),
        "pixel_threshold": 10,
        "pixel_scale": 15,
        "bg_var_threshold": 10,
        "bg_history": 500,
    },
    "high": {
        "blur_kernel": (1, 1),  # Minimal blur
        "pixel_threshold": 5,
        "pixel_scale": 20,
        "bg_var_threshold": 8,
        "bg_history": 700,
    },
}
```

### Expected Score Ranges (with "medium" preset)

| Scenario | Expected Score | Current Score | Status |
|----------|---------------|---------------|---------|
| Static scene | 0-5% | 0-2% | OK |
| Person walking | 15-30% | 5-10% | Too low ❌ |
| Vehicle passing (lateral) | 20-50% | 0-3% | Too low ❌ |
| Vehicle passing (frontal) | 10-25% | 0-5% | Too low ❌ |
| Lighting change | 5-15% | 10-20% | OK |

## Architecture Changes

### Database Schema

Add `motion_sensitivity` field to `cameras` table:

```sql
ALTER TABLE cameras ADD COLUMN motion_sensitivity VARCHAR(10) DEFAULT 'medium';
```

Valid values: `low`, `medium`, `high`, `custom`

### CameraConfig Updates

```python
@dataclass
class CameraConfig:
    # ... existing fields ...
    motion_sensitivity: str = "medium"  # New field
```

### MotionDetector API

```python
class MotionDetector:
    @classmethod
    def from_sensitivity(cls, sensitivity: str, threshold: float = 10.0):
        """Create detector with sensitivity preset."""
        params = SENSITIVITY_PRESETS[sensitivity]
        return cls(threshold=threshold, **params)
    
    def __init__(
        self,
        threshold: float = 10.0,
        blur_kernel: Tuple[int, int] = (2, 2),
        pixel_threshold: int = 10,
        pixel_scale: float = 15.0,
        bg_var_threshold: int = 10,
        bg_history: int = 500,
    ):
        # Store all parameters
        # Apply in preprocessing and detection methods
```

### Backward Compatibility

- Existing cameras without `motion_sensitivity` field → default to "medium"
- Existing `motion_threshold` values still work
- Algorithm improvements benefit all users automatically
- "custom" sensitivity allows manual parameter override

## Debugging & Calibration

### Motion Visualization Tool

```bash
python tools/visualize_motion.py --video path/to/test.mp4 --sensitivity medium
```

Outputs:
- Video with motion mask overlay
- Frame-by-frame motion scores
- Histogram of score distribution

### Calibration Tool

```bash
python tools/calibrate_motion.py --camera <camera-id>
```

Interactive UI:
1. Shows live camera feed
2. Overlays motion mask
3. Displays current motion score
4. Sliders to adjust parameters in real-time
5. "Save" button to persist to database

### Debug Mode

```python
detector = MotionDetector(threshold=10.0, debug=True)
```

When enabled:
- Saves preprocessed frames to `/tmp/motion_debug/`
- Saves pixel diff masks
- Saves background subtraction masks
- Detailed logging of each step

## Testing Strategy

### Unit Tests
- Test each sensitivity preset with synthetic data
- Validate parameter ranges
- Ensure backward compatibility

### Integration Tests
- Use benchmark videos (vehicles, people, static)
- Measure true positive / false positive rates
- Validate performance < 50ms per frame

### Manual Testing
- Test with user's actual street camera
- Verify vehicles consistently score 20%+
- Ensure static scenes still filter correctly

## Rollout Plan

1. **Phase 1**: Algorithm improvements (tasks 1-5)
   - Deploy improved parameters as default
   - Monitor production metrics
   - Gather user feedback

2. **Phase 2**: Sensitivity presets (tasks 6-9)
   - Add database field
   - Implement presets
   - Update CLI tools

3. **Phase 3**: Debug tools (tasks 10-12)
   - Build visualization tool
   - Build calibration tool
   - Document usage

4. **Phase 4**: Validation (tasks 13-15)
   - Create benchmark dataset
   - Comprehensive testing
   - Update documentation

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Too sensitive → false positives | High LLM costs | Provide sensitivity levels, default to "medium" |
| Breaking existing setups | User complaints | Backward compatible, can revert to "low" |
| Performance degradation | Slow frame processing | Benchmark required, optimize if > 50ms |
| Difficult to tune | Poor UX | Provide presets + calibration tool |

## Open Questions

1. Should we expose individual parameters in the UI or only sensitivity levels?
   - **Recommendation**: Only presets in UI, allow manual override via database for advanced users

2. Should we auto-detect optimal sensitivity based on scene analysis?
   - **Recommendation**: Future enhancement, not in initial scope

3. Should we support different sensitivity for day/night?
   - **Recommendation**: Interesting but complex, defer to future work
