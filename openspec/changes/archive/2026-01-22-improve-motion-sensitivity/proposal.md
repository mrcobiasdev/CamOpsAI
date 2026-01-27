# Proposal: Improve Motion Detection Sensitivity

## Why

The current motion detection algorithm is not detecting vehicles passing on the street despite:
- Camera positioned with lateral view (ideal for motion detection)
- Multiple threshold adjustments (tested various values)
- Frames being captured normally with good quality
- Motion scores consistently low (0-3%) when cars pass

Real-world testing shows the algorithm is too conservative, likely due to:
1. **Aggressive preprocessing**: GaussianBlur (3x3) + downsampling may be smoothing out important details
2. **High threshold for pixel difference**: Current threshold of 15 in binary thresholding may be missing subtle but significant changes
3. **Conservative scaling factors**: Scale factor of 10x for pixel diff may not be enough for typical outdoor scenes
4. **Background subtraction tuning**: MOG2 parameters may not be optimized for street/vehicle detection

This is a critical usability issue because motion detection is the primary filter to reduce LLM API costs, and if it fails to detect real motion, the system becomes unreliable.

## What Changes

### Core Algorithm Improvements
1. **Reduce preprocessing blur** - Change GaussianBlur from (3,3) to (2,2) or remove entirely to preserve motion details
2. **Lower pixel difference threshold** - Reduce binary threshold from 15 to 8-10 for better sensitivity
3. **Increase pixel diff scale factor** - Increase from 10x to 15-20x to amplify small movements
4. **Tune MOG2 background subtractor** - Adjust `varThreshold` from 16 to 8-12 and increase `history` for outdoor scenes
5. **Add region-based analysis** - Optionally divide frame into regions and detect motion in any region

### Testing & Validation Improvements
1. **Add motion visualization tool** - Script to show motion masks and scores on test videos
2. **Add benchmark dataset** - Sample videos with expected motion events (cars, people, etc.)
3. **Add sensitivity presets** - Predefined algorithm profiles (indoor, outdoor-day, outdoor-night, street)

### Configuration Enhancements
1. **Add sensitivity level** - New `motion_sensitivity` field (low/medium/high) to auto-tune parameters
2. **Add debug mode** - Optional flag to save motion masks and diff frames for troubleshooting
3. **Add calibration tool** - Interactive tool to test and tune motion detection on live camera

## Impact

### User-Facing
- Motion detection will properly detect vehicles and people in outdoor scenarios
- Reduced false negatives (missed detections)
- May increase false positives initially (can be tuned with sensitivity levels)
- Better out-of-the-box experience with less manual tuning required

### Technical
- Algorithm parameter changes in `MotionDetector` class
- New configuration fields in database and `CameraConfig`
- New CLI tools for calibration and testing
- Backward compatible (existing thresholds still work)

## Success Criteria

1. Camera pointed at street with lateral view detects 90%+ of passing vehicles (motion_score >= threshold)
2. Motion scores for vehicle passages are consistently >= 10% (detectable with default threshold)
3. Static scenes (no movement) still score < 5% to avoid false positives
4. New sensitivity presets work out-of-the-box for common scenarios (indoor, outdoor, street)
5. Calibration tool allows users to visually tune detection parameters in < 5 minutes
