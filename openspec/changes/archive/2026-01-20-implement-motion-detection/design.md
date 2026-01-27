# Motion Detection Design

## Architecture Overview

Motion detection will be implemented at the **FrameGrabber** level, immediately after frame capture and before queuing for LLM analysis:

```
RTSP Stream → FrameGrabber → MotionDetector → [Motion?] → FrameQueue → LLM
                                        ↓
                                    [No Motion] → Log → Drop
```

This placement ensures:
- Frames are filtered before entering the processing pipeline
- Minimal impact on existing queue and worker infrastructure
- Early filtering reduces memory and CPU usage

## Detection Algorithm

### Hybrid Approach

We will combine two complementary techniques:

1. **Pixel Difference (Simple Baseline)**
   - Compare current frame with previous frame
   - Calculate percentage of changed pixels
   - Fast and computationally inexpensive
   - Good for detecting sudden changes

2. **Background Subtraction (MOG2)**
   - Use OpenCV's `cv2.createBackgroundSubtractorMOG2()`
   - Maintains adaptive background model
   - Handles gradual lighting changes better
   - More robust for continuous motion

### Combining Methods

```
motion_score = (pixel_diff_score * 0.4) + (background_subtract_score * 0.6)
```

Weights can be tuned, but background subtraction gets higher priority for better accuracy in security scenarios.

### Optimization Techniques

- **Downsampling**: Reduce frame to 320x240 for motion calculation
- **ROI Support**: Allow configurable region-of-interest (future enhancement)
- **Grayscale Conversion**: Skip color channels for motion detection
- **Threshold Cache**: Pre-compute threshold values

## Trade-offs

### Why FrameGrabber-level?

| Approach | Pros | Cons |
|----------|------|------|
| FrameGrabber | Early filtering, minimal impact | Tightly coupled to capture logic |
| Queue Worker | Separated concerns | All frames enter queue (more memory) |
| Separate Service | Highly decoupled | Network overhead, more complexity |

**Decision**: FrameGrabber-level provides best balance of performance and simplicity.

### Why Hybrid Algorithm?

| Method | Accuracy | Performance | Use Case |
|--------|----------|-------------|----------|
| Pixel Diff | Low | Excellent | Sudden changes, fast movement |
| Background Sub | High | Good | Gradual movement, lighting |
| Hybrid | High | Good | All scenarios |

**Decision**: Hybrid balances accuracy and performance for security use cases.

### Per-Camera vs Global Threshold

| Option | Flexibility | Complexity | Use Case |
|--------|-------------|------------|----------|
| Global | Low | Low | Uniform environment |
| Per-Camera | High | Medium | Varied environments |
| Per-ROI | Very High | High | Advanced users |

**Decision**: Per-camera threshold allows customization without excessive complexity.

## Performance Considerations

### Expected Overhead

- Motion detection: ~10-30ms per frame (downsampled)
- Comparison: ~5-10ms per frame
- **Total**: < 50ms per frame (within goal)

### Memory Usage

- Previous frame buffer: ~100KB (320x240 grayscale)
- Background model: ~50KB (MOG2 internal)
- **Total**: < 1MB per camera

### LLM Reduction

Expected reduction scenarios:
- Static indoor scene: 80-90% reduction
- Low-traffic outdoor: 60-70% reduction
- High-traffic area: 30-50% reduction
- Average: 50-70% reduction

## Edge Cases & Mitigations

### Camera Reconnection
- **Issue**: Previous frame buffer becomes invalid
- **Solution**: Clear buffer on reconnect, skip first frame

### Lighting Changes
- **Issue**: Sudden lighting triggers false positives
- **Solution**: Background subtraction adaptive model handles gradual changes; tune threshold for environment

### Noise/Interference
- **Issue**: Low-light noise causes false motion
- **Solution**: Apply Gaussian blur before detection; increase threshold

### All Frames Filtered
- **Issue**: Threshold too high, no events detected
- **Solution**: Alert if 100 consecutive frames filtered; auto-adjust threshold or log warning

### No Frames Filtered
- **Issue**: Threshold too low, no reduction
- **Solution**: Log warning if > 90% frames sent; suggest threshold adjustment

## Future Enhancements (Out of Scope)

1. **Region of Interest**: Detect motion in specific areas only
2. **Time-based Thresholding**: Different thresholds for day/night
3. **Motion Classification**: Distinguish person/vehicle vs other motion
4. **Learning Threshold**: Auto-tune based on historical data
5. **Visual Debugging**: Overlay motion heatmap on frames

## Security Considerations

Motion detection is a **pre-processing filter** and does not replace LLM analysis:
- Any motion detected still goes through LLM
- Keywords and alerts are not affected
- No security events are lost due to motion filtering
- False negatives (missed events) are the main risk, mitigated by conservative thresholds

## Monitoring Requirements

Key metrics to track:
- `motion_frames_total`: Total frames captured
- `motion_frames_sent`: Frames sent to LLM
- `motion_frames_filtered`: Frames dropped
- `motion_detection_rate`: sent/total ratio
- `motion_avg_score`: Average motion score

Alert thresholds (configurable):
- Alert if detection_rate < 5% (possibly too aggressive)
- Alert if detection_rate > 95% (possibly too lenient)
