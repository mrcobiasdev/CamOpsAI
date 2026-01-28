"""Performance tests for frame annotation."""

import pytest
import numpy as np
import cv2
import time
from unittest.mock import patch

from src.capture.frame_annotation import FrameAnnotation


def create_test_frame(width: int, height: int) -> bytes:
    """Create a test frame of specified dimensions."""
    frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", frame)
    return buffer.tobytes()


def create_test_mask(width: int, height: int) -> np.ndarray:
    """Create a test motion mask of specified dimensions."""
    return np.random.randint(0, 256, (height, width), dtype=np.uint8)


class TestAnnotationPerformance:
    """Performance tests for frame annotation."""

    @pytest.mark.asyncio
    async def test_annotation_720p_performance(self):
        """Test annotation performance with 720p frames."""
        frame_bytes = create_test_frame(1280, 720)
        motion_mask = create_test_mask(640, 360)

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
                motion_mask=motion_mask,
                llm_keywords=["person", "alert", "walking"],
                llm_confidence=0.92,
                llm_provider="openai",
                llm_model="gpt-4o",
                motion_status="MOTION",
            )

            start = time.time()
            annotated = annotator.annotate_frame(frame_bytes)
            elapsed = (time.time() - start) * 1000

            assert annotated is not None
            assert elapsed < 100, (
                f"720p annotation took {elapsed:.1f}ms, expected <100ms"
            )

    @pytest.mark.asyncio
    async def test_annotation_1080p_performance(self):
        """Test annotation performance with 1080p frames."""
        frame_bytes = create_test_frame(1920, 1080)
        motion_mask = create_test_mask(960, 540)

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
                motion_mask=motion_mask,
                llm_keywords=["person", "alert", "walking"],
                llm_confidence=0.92,
                llm_provider="openai",
                llm_model="gpt-4o",
                motion_status="MOTION",
            )

            start = time.time()
            annotated = annotator.annotate_frame(frame_bytes)
            elapsed = (time.time() - start) * 1000

            assert annotated is not None
            assert elapsed < 200, (
                f"1080p annotation took {elapsed:.1f}ms, expected <200ms"
            )

    @pytest.mark.asyncio
    async def test_annotation_4k_performance(self):
        """Test annotation performance with 4K frames."""
        frame_bytes = create_test_frame(3840, 2160)
        motion_mask = create_test_mask(1920, 1080)

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
                motion_mask=motion_mask,
                llm_keywords=["person", "alert", "walking"],
                llm_confidence=0.92,
                llm_provider="openai",
                llm_model="gpt-4o",
                motion_status="MOTION",
            )

            start = time.time()
            annotated = annotator.annotate_frame(frame_bytes)
            elapsed = (time.time() - start) * 1000

            assert annotated is not None
            # 4K might take longer, but should still be reasonable
            assert elapsed < 700, f"4K annotation took {elapsed:.1f}ms, expected <700ms"

    @pytest.mark.asyncio
    async def test_annotation_concurrent_frames(self):
        """Test annotation performance with concurrent frames."""
        import asyncio

        frame_bytes = create_test_frame(1280, 720)
        motion_mask = create_test_mask(640, 360)

        with (
            patch("src.config.settings.annotation_mask_alpha", 0.3),
            patch("src.config.settings.annotation_mask_color", "0,255,0"),
            patch("src.config.settings.annotation_text_color", "255,255,255"),
            patch("src.config.settings.annotation_font_scale", 0.6),
            patch("src.config.settings.annotation_thickness", 2),
        ):

            async def annotate():
                annotator = FrameAnnotation(
                    motion_score=45.2,
                    motion_threshold=10.0,
                    motion_mask=motion_mask,
                    llm_keywords=["person", "alert"],
                    llm_confidence=0.92,
                    llm_provider="openai",
                    llm_model="gpt-4o",
                    motion_status="MOTION",
                )
                return annotator.annotate_frame(frame_bytes)

            start = time.time()
            results = await asyncio.gather(*[annotate() for _ in range(10)])
            elapsed = (time.time() - start) * 1000

            assert all(results)
            assert elapsed < 1000, (
                f"Concurrent 10 frames took {elapsed:.1f}ms, expected <1000ms"
            )

    @pytest.mark.asyncio
    async def test_annotation_memory_usage(self):
        """Test that annotation doesn't cause memory leaks."""
        import gc
        import sys

        frame_bytes = create_test_frame(1280, 720)
        motion_mask = create_test_mask(640, 360)

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
                motion_mask=motion_mask,
                llm_keywords=["person", "alert"],
                llm_confidence=0.92,
                llm_provider="openai",
                llm_model="gpt-4o",
                motion_status="MOTION",
            )

            gc.collect()
            initial_memory = sys.getsizeof(annotator)

            for _ in range(100):
                annotator.annotate_frame(frame_bytes)

            gc.collect()
            final_memory = sys.getsizeof(annotator)

            # Memory should not grow significantly
            assert final_memory < initial_memory * 2, "Potential memory leak detected"
