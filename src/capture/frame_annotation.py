"""Frame annotation for visual overlay of motion detection and LLM analysis."""

import logging
import time
from typing import Optional, List, Tuple

import cv2
import numpy as np
import platform

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Normalize text to avoid encoding issues with OpenCV.

    OpenCV's putText doesn't support all UTF-8 characters properly on Windows.
    We replace problematic characters with ASCII equivalents.

    Args:
        text: Input text

    Returns:
        Normalized text with special characters replaced
    """
    replacements = {
        "ã": "a",
        "á": "a",
        "à": "a",
        "â": "a",
        "ä": "a",
        "é": "e",
        "ê": "e",
        "è": "e",
        "ë": "e",
        "í": "i",
        "î": "i",
        "ì": "i",
        "ï": "i",
        "ó": "o",
        "õ": "o",
        "ô": "o",
        "ò": "o",
        "ö": "o",
        "ú": "u",
        "û": "u",
        "ù": "u",
        "ü": "u",
        "ç": "c",
        "Á": "A",
        "À": "A",
        "Â": "A",
        "Ä": "A",
        "É": "E",
        "Ê": "E",
        "È": "E",
        "Ë": "E",
        "Í": "I",
        "Î": "I",
        "Ì": "I",
        "Ï": "I",
        "Ó": "O",
        "Õ": "O",
        "Ô": "O",
        "Ò": "O",
        "Ö": "O",
        "Ú": "U",
        "Û": "U",
        "Ù": "U",
        "Ü": "U",
        "Ç": "C",
        "ñ": "n",
        "Ñ": "N",
        "¿": "?",
        "¡": "!",
        "°": " deg",
        "º": "o",
        "ª": "a",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


class FrameAnnotation:
    """Generates annotated frames with motion detection and LLM analysis overlays."""

    def __init__(
        self,
        motion_score: Optional[float],
        motion_threshold: Optional[float],
        motion_mask: Optional[np.ndarray],
        llm_keywords: List[str],
        llm_confidence: Optional[float],
        llm_provider: Optional[str],
        llm_model: Optional[str],
        motion_status: str = "UNKNOWN",
    ):
        """Initialize frame annotator.

        Args:
            motion_score: Motion detection score (0-100)
            motion_threshold: Motion detection threshold percentage
            motion_mask: Motion detection mask (same dimensions as frame)
            llm_keywords: Keywords detected by LLM
            llm_confidence: LLM confidence score (0-1)
            llm_provider: LLM provider name
            llm_model: LLM model name
            motion_status: "MOTION", "NO MOTION", or "UNKNOWN"
        """
        from src.config import settings

        self.motion_score = motion_score
        self.motion_threshold = motion_threshold
        self.motion_mask = motion_mask
        self.llm_keywords = llm_keywords
        self.llm_confidence = llm_confidence
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.motion_status = motion_status

        # Parse RGB colors from settings
        self.mask_color = tuple(map(int, settings.annotation_mask_color.split(",")))  # type: ignore
        self.text_color = tuple(map(int, settings.annotation_text_color.split(",")))  # type: ignore
        self.mask_alpha = settings.annotation_mask_alpha
        self.font_scale = settings.annotation_font_scale
        self.thickness = settings.annotation_thickness

    def annotate_frame(self, frame_bytes: bytes) -> Optional[bytes]:
        """Generate annotated frame from original frame bytes.

        Args:
            frame_bytes: Original frame as JPEG bytes

        Returns:
            Annotated frame as JPEG bytes, or None if annotation fails
        """
        try:
            # Decode frame
            frame = cv2.imdecode(
                np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR
            )
            if frame is None:
                logger.error("Failed to decode frame for annotation")
                return None

            start_time = time.time()

            # Add motion overlay
            frame = self._add_motion_overlay(frame)

            # Add LLM overlay
            frame = self._add_llm_overlay(frame)

            # Encode annotated frame
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            elapsed_ms = (time.time() - start_time) * 1000

            if elapsed_ms > 100:
                logger.warning(f"Annotation took {elapsed_ms:.1f}ms (>100ms target)")

            return buffer.tobytes()

        except Exception as e:
            logger.error(f"Error generating frame annotation: {e}")
            return None

    def _add_motion_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Add motion mask and status information overlay.

        Args:
            frame: Original frame

        Returns:
            Frame with motion overlay
        """
        height, width = frame.shape[:2]
        y_offset = 60

        # Add motion status badge
        if self.motion_status == "MOTION":
            status_text = f"[MOTION]"
            status_color = (0, 255, 0)  # Green
        elif self.motion_status == "NO MOTION":
            status_text = f"[NO MOTION]"
            status_color = (0, 0, 255)  # Red
        else:
            status_text = f"[UNKNOWN]"
            status_color = (128, 128, 128)  # Gray

        frame = self._add_text_with_background(
            frame, status_text, (20, y_offset), status_color, scale=0.65
        )
        y_offset += 32

        # Add motion score and threshold
        if self.motion_score is not None and self.motion_threshold is not None:
            score_text = f"Score: {self.motion_score:.1f}%  Threshold: {self.motion_threshold:.1f}%"
            score_text = normalize_text(score_text)
            frame = self._add_text_with_background(
                frame, score_text, (20, y_offset), self.text_color
            )
            y_offset += 32

        # Add motion mask overlay
        if self.motion_mask is not None and self.motion_status == "MOTION":
            # Resize mask to match frame dimensions
            mask_resized = cv2.resize(self.motion_mask, (width, height))

            # Apply colormap to mask for visualization
            mask_colored = cv2.applyColorMap(mask_resized, cv2.COLORMAP_HOT)

            # Create binary mask for alpha blending
            mask_binary = cv2.threshold(mask_resized, 1, 255, cv2.THRESH_BINARY)[1]
            mask_binary = cv2.cvtColor(mask_binary, cv2.COLOR_GRAY2BGR) / 255.0

            # Blend with frame
            frame = (
                frame * (1 - mask_binary * self.mask_alpha)
                + mask_colored * mask_binary * self.mask_alpha
            ).astype(np.uint8)

        return frame

    def _add_llm_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Add LLM analysis results overlay.

        Args:
            frame: Frame with motion overlay

        Returns:
            Frame with LLM overlay
        """
        height = frame.shape[0]

        # Calculate starting y_offset based on motion overlay (2 lines: status + score)
        # Motion lines: y=60 (status), y=92 (score)
        # LLM should start after: 60 + 32 + 32 = 124
        y_offset = 130

        # Add keywords
        if self.llm_keywords:
            keywords_str = ", ".join(self.llm_keywords)
            keywords_str = normalize_text(keywords_str)
            if len(keywords_str) > 100:
                keywords_str = keywords_str[:100] + "..."
            keywords_text = f"Keywords: {keywords_str}"
            frame = self._add_text_with_background(
                frame,
                keywords_text,
                (20, y_offset),
                (0, 255, 255),  # Yellow
            )
            y_offset += 32

        # Add confidence and provider
        if self.llm_confidence is not None:
            confidence_pct = self.llm_confidence * 100
            confidence_text = f"Confidence: {confidence_pct:.0f}%"
            confidence_text = normalize_text(confidence_text)
            frame = self._add_text_with_background(
                frame, confidence_text, (20, y_offset), self.text_color
            )
            y_offset += 28

        if self.llm_provider and self.llm_model:
            provider_name = self.llm_provider.title()
            model_short = (
                self.llm_model.split("-")[0].upper()
                if "-" in self.llm_model
                else self.llm_model.upper()
            )
            provider_text = f"Provider: {provider_name} ({model_short})"
            provider_text = normalize_text(provider_text)
            frame = self._add_text_with_background(
                frame, provider_text, (20, y_offset), self.text_color
            )

        return frame

    def _add_text_with_background(
        self,
        frame: np.ndarray,
        text: str,
        position: tuple[int, ...],
        text_color: tuple[int, ...],
        scale: Optional[float] = None,
    ) -> np.ndarray:
        """Add text with background box for better visibility.

        Args:
            frame: Input frame
            text: Text to display
            position: (x, y) coordinates
            text_color: RGB color tuple
            scale: Font scale (uses self.font_scale if None)

        Returns:
            Frame with text overlay
        """
        if scale is None:
            scale = self.font_scale

        font = cv2.FONT_HERSHEY_SIMPLEX

        # Get text size
        # text_height is height above baseline, baseline is pixels below baseline
        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, scale, self.thickness
        )

        # Total text vertical extent
        total_text_height = text_height + baseline

        x, y = position

        # Draw background rectangle
        # y is the baseline position, so text extends from (y - text_height) to (y + baseline)
        padding = 10
        bg_x1 = max(0, x - padding)
        bg_y1 = max(0, y - text_height - padding)
        bg_x2 = min(frame.shape[1], x + text_width + padding)
        bg_y2 = min(frame.shape[0], y + baseline + padding)

        cv2.rectangle(
            frame,
            (bg_x1, bg_y1),
            (bg_x2, bg_y2),
            (0, 0, 0),
            -1,
        )

        # Draw text
        cv2.putText(
            frame,
            text,
            (x, y),
            font,
            scale,
            text_color,
            self.thickness,
            cv2.LINE_AA,
        )

        return frame
