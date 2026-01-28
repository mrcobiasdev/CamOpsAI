"""Tests for frame annotation functionality."""

import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

from src.capture.frame_annotation import FrameAnnotation


@pytest.fixture
def sample_frame_bytes():
    """Create a valid JPEG frame for testing."""
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    # Use cv2.IMWRITE_JPEG_QUALITY for better compatibility
    _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return buffer.tobytes()


@pytest.fixture
def sample_motion_mask():
    """Create a sample motion mask."""
    mask = np.random.randint(0, 256, (240, 320), dtype=np.uint8)
    return mask


@pytest.fixture
def sample_llm_keywords():
    """Sample LLM keywords."""
    return ["person", "walking", "entrance", "alert"]


class TestFrameAnnotation:
    """Test FrameAnnotation class."""

    @pytest.mark.asyncio
    async def test_annotation_with_motion_data(
        self, sample_frame_bytes, sample_motion_mask
    ):
        """Test annotation with only motion data."""
        with (
            patch("src.config.settings.annotation_mask_alpha", 0.3),
            patch("src.config.settings.annotation_mask_color", "0,255,0"),
            patch("src.config.settings.annotation_text_color", "255,255,255"),
            patch("src.config.settings.annotation_font_scale", 0.6),
            patch("src.config.settings.annotation_thickness", 2),
        ):
            annotator = FrameAnnotation(
                motion_score=45.2,
                motion_threshold=10.0,
                motion_mask=sample_motion_mask,
                llm_keywords=[],
                llm_confidence=None,
                llm_provider=None,
                llm_model=None,
                motion_status="MOTION",
            )

            annotated = annotator.annotate_frame(sample_frame_bytes)
            assert annotated is not None
            assert len(annotated) > 0

    @pytest.mark.asyncio
    async def test_annotation_with_llm_data(
        self, sample_frame_bytes, sample_llm_keywords
    ):
        """Test annotation with only LLM data."""
        with (
            patch("src.config.settings.annotation_mask_alpha", 0.3),
            patch("src.config.settings.annotation_mask_color", "0,255,0"),
            patch("src.config.settings.annotation_text_color", "255,255,255"),
            patch("src.config.settings.annotation_font_scale", 0.6),
            patch("src.config.settings.annotation_thickness", 2),
        ):
            annotator = FrameAnnotation(
                motion_score=None,
                motion_threshold=None,
                motion_mask=None,
                llm_keywords=sample_llm_keywords,
                llm_confidence=0.92,
                llm_provider="openai",
                llm_model="gpt-4o",
                motion_status="UNKNOWN",
            )

            annotated = annotator.annotate_frame(sample_frame_bytes)
            assert annotated is not None
            assert len(annotated) > 0

    @pytest.mark.asyncio
    async def test_annotation_with_both_data(
        self, sample_frame_bytes, sample_motion_mask, sample_llm_keywords
    ):
        """Test annotation with both motion and LLM data."""
        with (
            patch("src.config.settings.annotation_mask_alpha", 0.3),
            patch("src.config.settings.annotation_mask_color", "0,255,0"),
            patch("src.config.settings.annotation_text_color", "255,255,255"),
            patch("src.config.settings.annotation_font_scale", 0.6),
            patch("src.config.settings.annotation_thickness", 2),
        ):
            annotator = FrameAnnotation(
                motion_score=45.2,
                motion_threshold=10.0,
                motion_mask=sample_motion_mask,
                llm_keywords=sample_llm_keywords,
                llm_confidence=0.92,
                llm_provider="openai",
                llm_model="gpt-4o",
                motion_status="MOTION",
            )

            annotated = annotator.annotate_frame(sample_frame_bytes)
            assert annotated is not None
            assert len(annotated) > 0

    @pytest.mark.asyncio
    async def test_annotation_with_missing_data(self, sample_frame_bytes):
        """Test annotation with missing/null data."""
        with (
            patch("src.config.settings.annotation_mask_alpha", 0.3),
            patch("src.config.settings.annotation_mask_color", "0,255,0"),
            patch("src.config.settings.annotation_text_color", "255,255,255"),
            patch("src.config.settings.annotation_font_scale", 0.6),
            patch("src.config.settings.annotation_thickness", 2),
        ):
            annotator = FrameAnnotation(
                motion_score=None,
                motion_threshold=None,
                motion_mask=None,
                llm_keywords=[],
                llm_confidence=None,
                llm_provider=None,
                llm_model=None,
                motion_status="UNKNOWN",
            )

            annotated = annotator.annotate_frame(sample_frame_bytes)
            assert annotated is not None
            assert len(annotated) > 0

    @pytest.mark.asyncio
    async def test_annotation_text_truncation(
        self, sample_frame_bytes, sample_llm_keywords
    ):
        """Test that long text is truncated properly."""
        long_keywords = ["keyword_" + str(i) for i in range(50)]

        with (
            patch("src.config.settings.annotation_mask_alpha", 0.3),
            patch("src.config.settings.annotation_mask_color", "0,255,0"),
            patch("src.config.settings.annotation_text_color", "255,255,255"),
            patch("src.config.settings.annotation_font_scale", 0.6),
            patch("src.config.settings.annotation_thickness", 2),
        ):
            annotator = FrameAnnotation(
                motion_score=None,
                motion_threshold=None,
                motion_mask=None,
                llm_keywords=long_keywords,
                llm_confidence=0.92,
                llm_provider="openai",
                llm_model="gpt-4o",
                motion_status="UNKNOWN",
            )

            annotated = annotator.annotate_frame(sample_frame_bytes)
            assert annotated is not None

    @pytest.mark.asyncio
    async def test_annotation_invalid_frame(self):
        """Test that invalid frame is handled gracefully."""
        with (
            patch("src.config.settings.annotation_mask_alpha", 0.3),
            patch("src.config.settings.annotation_mask_color", "0,255,0"),
            patch("src.config.settings.annotation_text_color", "255,255,255"),
            patch("src.config.settings.annotation_font_scale", 0.6),
            patch("src.config.settings.annotation_thickness", 2),
        ):
            annotator = FrameAnnotation(
                motion_score=45.2,
                motion_threshold=10.0,
                motion_mask=None,
                llm_keywords=[],
                llm_confidence=None,
                llm_provider=None,
                llm_model=None,
                motion_status="MOTION",
            )

            invalid_frame = b"invalid_jpeg_data"
            annotated = annotator.annotate_frame(invalid_frame)
            assert annotated is None

    @pytest.mark.asyncio
    async def test_annotation_color_parsing(self, sample_frame_bytes):
        """Test that RGB colors are parsed correctly from settings."""
        with (
            patch("src.config.settings.annotation_mask_alpha", 0.3),
            patch("src.config.settings.annotation_mask_color", "255,128,64"),
            patch("src.config.settings.annotation_text_color", "200,200,200"),
            patch("src.config.settings.annotation_font_scale", 0.6),
            patch("src.config.settings.annotation_thickness", 2),
        ):
            annotator = FrameAnnotation(
                motion_score=45.2,
                motion_threshold=10.0,
                motion_mask=None,
                llm_keywords=[],
                llm_confidence=None,
                llm_provider=None,
                llm_model=None,
                motion_status="MOTION",
            )

            assert annotator.mask_color == (255, 128, 64)
            assert annotator.text_color == (200, 200, 200)

    @pytest.mark.asyncio
    async def test_annotation_motion_status_colors(
        self, sample_frame_bytes, sample_motion_mask
    ):
        """Test that different motion statuses use different colors."""
        with (
            patch("src.config.settings.annotation_mask_alpha", 0.3),
            patch("src.config.settings.annotation_mask_color", "0,255,0"),
            patch("src.config.settings.annotation_text_color", "255,255,255"),
            patch("src.config.settings.annotation_font_scale", 0.6),
            patch("src.config.settings.annotation_thickness", 2),
        ):
            annotator_motion = FrameAnnotation(
                motion_score=45.2,
                motion_threshold=10.0,
                motion_mask=sample_motion_mask,
                llm_keywords=[],
                llm_confidence=None,
                llm_provider=None,
                llm_model=None,
                motion_status="MOTION",
            )

            annotator_no_motion = FrameAnnotation(
                motion_score=5.0,
                motion_threshold=10.0,
                motion_mask=sample_motion_mask,
                llm_keywords=[],
                llm_confidence=None,
                llm_provider=None,
                llm_model=None,
                motion_status="NO MOTION",
            )

            annotated_motion = annotator_motion.annotate_frame(sample_frame_bytes)
            annotated_no_motion = annotator_no_motion.annotate_frame(sample_frame_bytes)

            assert annotated_motion is not None
            assert annotated_no_motion is not None

    @pytest.mark.asyncio
    async def test_annotation_performance(self, sample_frame_bytes):
        """Test that annotation completes within 100ms target."""
        with (
            patch("src.config.settings.annotation_mask_alpha", 0.3),
            patch("src.config.settings.annotation_mask_color", "0,255,0"),
            patch("src.config.settings.annotation_text_color", "255,255,255"),
            patch("src.config.settings.annotation_font_scale", 0.6),
            patch("src.config.settings.annotation_thickness", 2),
        ):
            annotator = FrameAnnotation(
                motion_score=45.2,
                motion_threshold=10.0,
                motion_mask=None,
                llm_keywords=["person", "alert"],
                llm_confidence=0.92,
                llm_provider="openai",
                llm_model="gpt-4o",
                motion_status="MOTION",
            )

            import time

            start = time.time()
            annotated = annotator.annotate_frame(sample_frame_bytes)
            elapsed = (time.time() - start) * 1000

            assert annotated is not None
            assert elapsed < 100, f"Annotation took {elapsed:.1f}ms, expected <100ms"
