"""Testes de benchmark para motion detection com vídeos reais.

Estes testes validam a detecção de movimento contra ground truth anotado.
Requer vídeos de teste em tests/fixtures/videos/.
"""

import json
import asyncio
from pathlib import Path

import pytest
import cv2
import numpy as np

from src.capture.motion_detector import MotionDetector


# Caminho para fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "videos"
GROUND_TRUTH_FILE = FIXTURES_DIR / "ground_truth.json"


def load_ground_truth():
    """Carrega anotações de ground truth."""
    if not GROUND_TRUTH_FILE.exists():
        return None

    with open(GROUND_TRUTH_FILE, "r") as f:
        return json.load(f)


def process_video_for_test(video_path: Path, sensitivity: str, threshold: float = 10.0):
    """Processa vídeo e retorna estatísticas de detecção.

    Args:
        video_path: Caminho para o vídeo
        sensitivity: Nível de sensibilidade
        threshold: Threshold de detecção

    Returns:
        Dict com estatísticas: scores, detection_rate, avg_score, etc.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Não foi possível abrir vídeo: {video_path}")

    detector = MotionDetector.from_sensitivity(sensitivity, threshold)

    scores = []
    frames_detected = 0
    total_frames = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        total_frames += 1
        score, has_motion = detector.detect_motion(frame)
        scores.append(score)

        if has_motion:
            frames_detected += 1

    cap.release()

    detection_rate = frames_detected / total_frames if total_frames > 0 else 0
    avg_score = np.mean(scores) if scores else 0

    return {
        "total_frames": total_frames,
        "frames_detected": frames_detected,
        "detection_rate": detection_rate,
        "avg_score": avg_score,
        "scores": scores,
    }


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_vehicle_lateral_medium_sensitivity():
    """Testa detecção de veículo lateral com sensitivity medium."""
    ground_truth = load_ground_truth()

    if ground_truth is None:
        pytest.skip("Ground truth file not found")

    video_file = "vehicle_lateral_01.mp4"
    video_path = FIXTURES_DIR / video_file

    if not video_path.exists():
        pytest.skip(f"Test video {video_file} not found")

    # Ground truth esperado
    gt = ground_truth[video_file]
    expected = gt["sensitivity_expectations"]["medium"]

    # Processar vídeo
    stats = await asyncio.get_event_loop().run_in_executor(
        None, process_video_for_test, video_path, "medium", 10.0
    )

    # Validar resultados
    assert stats["detection_rate"] >= expected["detection_rate_min"], (
        f"Detection rate {stats['detection_rate']:.2%} below minimum {expected['detection_rate_min']:.2%}"
    )

    assert stats["avg_score"] >= expected["avg_score_min"], (
        f"Avg score {stats['avg_score']:.2f}% below minimum {expected['avg_score_min']}%"
    )

    print(f"\n✅ Vehicle lateral detection (medium):")
    print(f"   Detection rate: {stats['detection_rate']:.2%}")
    print(f"   Avg score: {stats['avg_score']:.2f}%")
    print(f"   Frames: {stats['frames_detected']}/{stats['total_frames']}")


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_static_outdoor_false_positives_medium():
    """Testa taxa de falsos positivos em cena estática."""
    ground_truth = load_ground_truth()

    if ground_truth is None:
        pytest.skip("Ground truth file not found")

    video_file = "static_outdoor_01.mp4"
    video_path = FIXTURES_DIR / video_file

    if not video_path.exists():
        pytest.skip(f"Test video {video_file} not found")

    # Ground truth esperado
    gt = ground_truth[video_file]
    expected = gt["sensitivity_expectations"]["medium"]

    # Processar vídeo
    stats = await asyncio.get_event_loop().run_in_executor(
        None, process_video_for_test, video_path, "medium", 10.0
    )

    # Para cena estática, detection_rate é taxa de falso positivo
    false_positive_rate = stats["detection_rate"]

    # Validar resultados
    assert false_positive_rate <= expected["false_positive_rate_max"], (
        f"False positive rate {false_positive_rate:.2%} above maximum {expected['false_positive_rate_max']:.2%}"
    )

    assert stats["avg_score"] <= expected["avg_score_max"], (
        f"Avg score {stats['avg_score']:.2f}% above maximum {expected['avg_score_max']}%"
    )

    print(f"\n✅ Static outdoor false positives (medium):")
    print(f"   False positive rate: {false_positive_rate:.2%}")
    print(f"   Avg score: {stats['avg_score']:.2f}%")
    print(f"   Frames: {stats['frames_detected']}/{stats['total_frames']}")


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_sensitivity_comparison():
    """Compara todas as sensitivities no mesmo vídeo."""
    ground_truth = load_ground_truth()

    if ground_truth is None:
        pytest.skip("Ground truth file not found")

    video_file = "vehicle_lateral_01.mp4"
    video_path = FIXTURES_DIR / video_file

    if not video_path.exists():
        pytest.skip(f"Test video {video_file} not found")

    results = {}

    # Testar todas as sensitivities
    for sensitivity in ["low", "medium", "high"]:
        stats = await asyncio.get_event_loop().run_in_executor(
            None, process_video_for_test, video_path, sensitivity, 10.0
        )
        results[sensitivity] = stats

    # Validar ordenação: high > medium > low em detection_rate
    assert results["high"]["detection_rate"] >= results["medium"]["detection_rate"], (
        "High sensitivity should have >= detection rate than medium"
    )

    assert results["medium"]["detection_rate"] >= results["low"]["detection_rate"], (
        "Medium sensitivity should have >= detection rate than low"
    )

    print(f"\n✅ Sensitivity comparison:")
    print(
        f"   LOW:    {results['low']['detection_rate']:.2%} detection, {results['low']['avg_score']:.2f}% avg score"
    )
    print(
        f"   MEDIUM: {results['medium']['detection_rate']:.2%} detection, {results['medium']['avg_score']:.2f}% avg score"
    )
    print(
        f"   HIGH:   {results['high']['detection_rate']:.2%} detection, {results['high']['avg_score']:.2f}% avg score"
    )


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_performance_benchmark():
    """Testa performance de processamento (< 50ms por frame)."""
    ground_truth = load_ground_truth()

    if ground_truth is None:
        pytest.skip("Ground truth file not found")

    video_file = "vehicle_lateral_01.mp4"
    video_path = FIXTURES_DIR / video_file

    if not video_path.exists():
        pytest.skip(f"Test video {video_file} not found")

    import time

    cap = cv2.VideoCapture(str(video_path))
    detector = MotionDetector.from_sensitivity("medium", 10.0)

    frame_times = []
    frame_count = 0

    while frame_count < 100:  # Testar primeiros 100 frames
        ret, frame = cap.read()
        if not ret:
            break

        start = time.perf_counter()
        detector.detect_motion(frame)
        elapsed = (time.perf_counter() - start) * 1000  # ms

        frame_times.append(elapsed)
        frame_count += 1

    cap.release()

    avg_time = np.mean(frame_times)
    max_time = np.max(frame_times)
    p95_time = np.percentile(frame_times, 95)

    # Validar performance
    assert avg_time < 50, f"Average processing time {avg_time:.2f}ms exceeds 50ms"
    assert p95_time < 100, f"P95 processing time {p95_time:.2f}ms exceeds 100ms"

    print(f"\n✅ Performance benchmark:")
    print(f"   Avg time: {avg_time:.2f}ms")
    print(f"   Max time: {max_time:.2f}ms")
    print(f"   P95 time: {p95_time:.2f}ms")
    print(f"   Frames tested: {frame_count}")


# Teste parametrizado para todos os vídeos disponíveis
@pytest.mark.asyncio
@pytest.mark.benchmark
@pytest.mark.parametrize("sensitivity", ["low", "medium", "high"])
async def test_all_videos_all_sensitivities(sensitivity):
    """Testa todos os vídeos disponíveis com todas as sensitivities."""
    ground_truth = load_ground_truth()

    if ground_truth is None:
        pytest.skip("Ground truth file not found")

    passed = 0
    failed = 0
    skipped = 0

    for video_file, gt in ground_truth.items():
        if video_file.startswith("_"):
            continue  # Skip metadata

        video_path = FIXTURES_DIR / video_file

        if not video_path.exists():
            print(f"   ⚠️  {video_file}: SKIPPED (not found)")
            skipped += 1
            continue

        try:
            stats = await asyncio.get_event_loop().run_in_executor(
                None, process_video_for_test, video_path, sensitivity, 10.0
            )

            expected = gt.get("sensitivity_expectations", {}).get(sensitivity, {})

            # Validar expectativas
            if "detection_rate_min" in expected:
                assert stats["detection_rate"] >= expected["detection_rate_min"]

            if "false_positive_rate_max" in expected:
                assert stats["detection_rate"] <= expected["false_positive_rate_max"]

            print(f"   ✅ {video_file}: PASSED ({stats['detection_rate']:.2%})")
            passed += 1

        except AssertionError as e:
            print(f"   ❌ {video_file}: FAILED ({e})")
            failed += 1
        except Exception as e:
            print(f"   ❌ {video_file}: ERROR ({e})")
            failed += 1

    print(f"\n📊 Summary for {sensitivity}:")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Skipped: {skipped}")

    assert failed == 0, f"{failed} videos failed validation"
