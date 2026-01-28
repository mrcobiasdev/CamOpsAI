"""Motion detection using hybrid algorithm (pixel difference + background subtraction)."""

import logging
import os
import shutil
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# Sensitivity presets for different scenarios
SENSITIVITY_PRESETS: Dict[str, Dict[str, Any]] = {
    "low": {
        "blur_kernel": (5, 5),  # More blur, less sensitivity
        "pixel_threshold": 20,
        "pixel_scale": 8.0,
        "bg_var_threshold": 20,
        "bg_history": 300,
    },
    "medium": {
        "blur_kernel": (3, 3),  # Balanced blur (must be odd number)
        "pixel_threshold": 10,
        "pixel_scale": 15.0,
        "bg_var_threshold": 10,
        "bg_history": 500,
    },
    "high": {
        "blur_kernel": (3, 3),  # Keep (3,3) for stability, reduce threshold instead
        "pixel_threshold": 5,  # Lower threshold = more sensitive
        "pixel_scale": 20.0,
        "bg_var_threshold": 8,
        "bg_history": 700,
    },
}


class MotionDetector:
    """Detects motion in video frames using hybrid algorithm with configurable sensitivity."""

    PIXEL_DIFF_WEIGHT = 0.5
    BACKGROUND_SUB_WEIGHT = 0.5
    PROCESS_SIZE = (320, 240)

    def __init__(
        self,
        threshold: float = 10.0,
        blur_kernel: Tuple[int, int] = (3, 3),  # Must be odd number for GaussianBlur
        pixel_threshold: int = 10,
        pixel_scale: float = 15.0,
        bg_var_threshold: int = 10,
        bg_history: int = 500,
        debug: bool = False,
        debug_dir: Optional[str] = None,
    ):
        """Initialize motion detector.

        Args:
            threshold: Motion threshold percentage (0-100). Frames below this are filtered out.
            blur_kernel: GaussianBlur kernel size for preprocessing.
            pixel_threshold: Binary threshold for pixel difference detection.
            pixel_scale: Scale factor to amplify pixel difference scores.
            bg_var_threshold: Variance threshold for MOG2 background subtraction.
            bg_history: Number of frames for MOG2 background model history.
            debug: Enable debug mode (saves frames and detailed logs).
            debug_dir: Directory for debug files (default: /tmp/motion_debug/).
        """
        self.threshold = threshold
        self.blur_kernel = blur_kernel
        self.pixel_threshold = pixel_threshold
        self.pixel_scale = pixel_scale
        self.bg_var_threshold = bg_var_threshold
        self.bg_history = bg_history
        self.debug = debug
        self.debug_dir = Path(debug_dir or "/tmp/motion_debug")
        self._frame_count = 0
        self._previous_frame: Optional[np.ndarray] = None
        self._last_mask: Optional[np.ndarray] = None

        # Create background subtractor with configured parameters
        self._background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=bg_history, varThreshold=bg_var_threshold, detectShadows=True
        )

        # Setup debug directory if debug mode enabled
        if self.debug:
            self._setup_debug_dir()

    def _setup_debug_dir(self):
        """Setup debug directory with cleanup for old files."""
        try:
            # Create debug directory
            self.debug_dir.mkdir(parents=True, exist_ok=True)

            # Cleanup: remove files older than 24 hours or if dir > 100MB
            self._cleanup_debug_dir()

            logger.info(f"Debug mode enabled: {self.debug_dir}")
        except Exception as e:
            logger.error(f"Failed to setup debug directory: {e}")
            self.debug = False

    def _cleanup_debug_dir(self):
        """Remove old debug files to prevent disk space issues."""
        if not self.debug_dir.exists():
            return

        try:
            # Calculate directory size
            total_size = sum(
                f.stat().st_size for f in self.debug_dir.rglob("*") if f.is_file()
            )

            # If > 100MB, remove oldest files
            if total_size > 100 * 1024 * 1024:  # 100MB
                files = sorted(
                    self.debug_dir.rglob("*"),
                    key=lambda f: f.stat().st_mtime if f.is_file() else 0,
                )
                for f in files:
                    if f.is_file():
                        f.unlink()
                        total_size -= f.stat().st_size
                        if total_size < 50 * 1024 * 1024:  # Keep under 50MB
                            break
                logger.info("Debug directory cleaned up")

            # Remove files older than 24 hours
            cutoff_time = time.time() - (24 * 60 * 60)
            for f in self.debug_dir.rglob("*"):
                if f.is_file() and f.stat().st_mtime < cutoff_time:
                    f.unlink()

        except Exception as e:
            logger.warning(f"Failed to cleanup debug directory: {e}")

    def _save_debug_frame(self, name: str, frame: np.ndarray):
        """Save frame to debug directory.

        Args:
            name: Name for the debug file
            frame: Frame to save
        """
        if not self.debug:
            return

        try:
            timestamp = int(time.time() * 1000)
            filename = (
                self.debug_dir / f"{timestamp}_{self._frame_count:04d}_{name}.png"
            )
            cv2.imwrite(str(filename), frame)
        except Exception as e:
            logger.warning(f"Failed to save debug frame {name}: {e}")

    @classmethod
    def from_sensitivity(
        cls, sensitivity: str, threshold: float = 10.0
    ) -> "MotionDetector":
        """Create detector with sensitivity preset.

        Args:
            sensitivity: Sensitivity level ("low", "medium", "high")
            threshold: Motion threshold percentage (0-100)

        Returns:
            MotionDetector configured with preset parameters

        Raises:
            ValueError: If sensitivity is not valid
        """
        if sensitivity not in SENSITIVITY_PRESETS:
            raise ValueError(
                f"Invalid sensitivity '{sensitivity}'. Must be one of: {list(SENSITIVITY_PRESETS.keys())}"
            )

        params = SENSITIVITY_PRESETS[sensitivity]
        return cls(
            threshold=threshold,
            blur_kernel=params["blur_kernel"],
            pixel_threshold=params["pixel_threshold"],
            pixel_scale=params["pixel_scale"],
            bg_var_threshold=params["bg_var_threshold"],
            bg_history=params["bg_history"],
        )

    def reset(self):
        """Reset detector state (clear previous frame and background model)."""
        self._previous_frame = None
        self._last_mask = None
        self._background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            history=self.bg_history,
            varThreshold=self.bg_var_threshold,
        )
        logger.debug("Motion detector reset")

    def get_last_mask(self) -> Optional[np.ndarray]:
        """Return the last motion mask generated.

        Returns:
            Motion mask as numpy array, or None if no frame processed yet
        """
        return self._last_mask

    def detect_motion(self, frame: np.ndarray) -> Tuple[float, bool]:
        """Detect motion in frame.

        Args:
            frame: Input frame (BGR format from OpenCV)

        Returns:
            Tuple of (motion_score, has_motion):
            - motion_score: Motion intensity (0-100)
            - has_motion: True if motion >= threshold

        Raises:
            ValueError: If frame is invalid
        """
        if frame is None or frame.size == 0:
            raise ValueError("Invalid frame: None or empty")

        try:
            self._frame_count += 1

            # Preprocess frame for performance
            processed = self._preprocess_frame(frame)

            # Debug: save preprocessed frame
            if self.debug:
                self._save_debug_frame("01_preprocessed", processed)

            # Calculate pixel difference score
            pixel_diff_score = self._calculate_pixel_difference(processed)

            # Calculate background subtraction score
            bg_sub_score = self._calculate_background_subtraction(processed)

            # Combine scores with weights
            motion_score = (
                pixel_diff_score * self.PIXEL_DIFF_WEIGHT
                + bg_sub_score * self.BACKGROUND_SUB_WEIGHT
            )

            has_motion = motion_score >= self.threshold

            # Generate and store motion mask for annotation
            self._last_mask = self._generate_motion_mask(processed)

            # Log motion detection result
            log_msg = (
                f"Motion detection: score={motion_score:.2f}%, "
                f"threshold={self.threshold}%, "
                f"pixel_diff={pixel_diff_score:.2f}%, "
                f"bg_sub={bg_sub_score:.2f}%, "
                f"has_motion={has_motion}"
            )

            if self.debug:
                # Detailed debug logging
                logger.debug(
                    f"[DEBUG] {log_msg} | "
                    f"params: blur={self.blur_kernel}, "
                    f"pixel_thresh={self.pixel_threshold}, "
                    f"pixel_scale={self.pixel_scale}, "
                    f"bg_var={self.bg_var_threshold}, "
                    f"bg_hist={self.bg_history}"
                )
            else:
                logger.info(log_msg)

            return motion_score, has_motion

        except Exception as e:
            logger.error(f"Error detecting motion: {e}")
            # Fail-safe: return high score to avoid filtering errors
            return 100.0, True

    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for motion detection.

        Args:
            frame: Input BGR frame

        Returns:
            Grayscale, downsampled frame
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Downsample for performance
        resized = cv2.resize(gray, self.PROCESS_SIZE, interpolation=cv2.INTER_AREA)

        # Apply configurable blur to reduce noise
        blurred = cv2.GaussianBlur(resized, self.blur_kernel, 0)

        return blurred

    def _calculate_pixel_difference(self, frame: np.ndarray) -> float:
        """Calculate pixel difference score between current and previous frame.

        Args:
            frame: Current preprocessed frame

        Returns:
            Motion score (0-100)
        """
        if self._previous_frame is None:
            # First frame, store as baseline
            self._previous_frame = frame.copy()
            return 100.0  # Always send first frame

        # Calculate absolute difference
        diff = cv2.absdiff(self._previous_frame, frame)

        # Debug: save diff mask
        if self.debug:
            self._save_debug_frame("02_pixel_diff", diff)

        # Apply configurable threshold for pixel difference detection
        _, thresh = cv2.threshold(diff, self.pixel_threshold, 255, cv2.THRESH_BINARY)

        # Debug: save thresholded mask
        if self.debug:
            self._save_debug_frame("03_pixel_thresh", thresh)

        # Calculate percentage of changed pixels
        changed_pixels = cv2.countNonZero(thresh)
        total_pixels = frame.shape[0] * frame.shape[1]
        diff_percentage = (changed_pixels / total_pixels) * 100

        # Update previous frame
        self._previous_frame = frame.copy()

        # Apply configurable scale factor to amplify motion scores
        return min(diff_percentage * self.pixel_scale, 100.0)

    def _calculate_background_subtraction(self, frame: np.ndarray) -> float:
        """Calculate motion using background subtraction.

        Args:
            frame: Current preprocessed frame

        Returns:
            Motion score (0-100)
        """
        # Apply background subtraction
        fg_mask = self._background_subtractor.apply(frame)

        # Debug: save background subtraction mask
        if self.debug:
            self._save_debug_frame("04_bg_sub_raw", fg_mask)

        # Remove shadows (gray pixels in mask)
        _, thresh = cv2.threshold(fg_mask, 127, 255, cv2.THRESH_BINARY)

        # Debug: save thresholded background mask
        if self.debug:
            self._save_debug_frame("05_bg_sub_thresh", thresh)

        # Calculate percentage of foreground pixels
        foreground_pixels = cv2.countNonZero(thresh)
        total_pixels = frame.shape[0] * frame.shape[1]
        fg_percentage = (foreground_pixels / total_pixels) * 100

        # Scale to 0-100
        return min(fg_percentage * 3, 100.0)

    def _generate_motion_mask(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Generate motion mask visualization.

        Args:
            frame: Preprocessed frame

        Returns:
            Motion mask as numpy array, or None if cannot generate
        """
        try:
            if self._previous_frame is None:
                return None

            # Calculate pixel difference mask
            diff = cv2.absdiff(self._previous_frame, frame)
            _, diff_thresh = cv2.threshold(
                diff, self.pixel_threshold, 255, cv2.THRESH_BINARY
            )

            # Calculate background subtraction mask
            fg_mask = self._background_subtractor.apply(frame)
            _, bg_thresh = cv2.threshold(fg_mask, 127, 255, cv2.THRESH_BINARY)

            # Combine masks (use maximum of both)
            combined_mask = cv2.max(diff_thresh, bg_thresh)

            return combined_mask

        except Exception as e:
            logger.warning(f"Failed to generate motion mask: {e}")
            return None

    def update_threshold(self, threshold: float):
        """Update motion detection threshold.

        Args:
            threshold: New threshold percentage (0-100)
        """
        if not 0 <= threshold <= 100:
            raise ValueError(f"Threshold must be between 0 and 100, got {threshold}")

        self.threshold = threshold
        logger.debug(f"Motion threshold updated to {threshold}%")
