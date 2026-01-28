"""Testes para a classe FrameQueue."""

import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock

from src.capture.queue import FrameQueue, FrameItem


@pytest.mark.asyncio
async def test_clear_resets_counters():
    """Testa que clear() zera os contadores."""
    processor = AsyncMock()
    queue = FrameQueue(processor=processor, max_size=10, num_workers=1)

    queue._processed_count = 50
    queue._dropped_count = 5

    queue.clear()

    assert queue._processed_count == 0
    assert queue._dropped_count == 0


@pytest.mark.asyncio
async def test_clear_does_not_affect_queue_content():
    """Testa que clear() não afeta o conteúdo da fila."""
    processor = AsyncMock()
    queue = FrameQueue(processor=processor, max_size=10, num_workers=0)

    camera_id = uuid.uuid4()
    await queue.put(camera_id, b"frame_data_1", 1234567890.0)
    await queue.put(camera_id, b"frame_data_2", 1234567891.0)

    initial_size = queue.size

    queue.clear()

    assert queue.size == initial_size
    assert queue.size == 2


@pytest.mark.asyncio
async def test_clear_does_not_affect_worker_status():
    """Testa que clear() não afeta o status dos workers."""
    processor = AsyncMock()
    queue = FrameQueue(processor=processor, max_size=10, num_workers=2)

    await queue.start_workers()
    initial_running = queue._running
    initial_worker_count = len(queue._workers)

    queue.clear()

    assert queue._running == initial_running
    assert len(queue._workers) == initial_worker_count
    assert queue._num_workers == 2

    await queue.stop_workers()


@pytest.mark.asyncio
async def test_clear_can_be_called_multiple_times():
    """Testa que clear() pode ser chamado múltiplas vezes."""
    processor = AsyncMock()
    queue = FrameQueue(processor=processor, max_size=10, num_workers=0)

    queue._processed_count = 10
    queue._dropped_count = 2

    queue.clear()
    assert queue._processed_count == 0
    assert queue._dropped_count == 0

    queue._processed_count = 5
    queue.clear()
    assert queue._processed_count == 0
    assert queue._dropped_count == 0


@pytest.mark.asyncio
async def test_clear_resets_stats_output():
    """Testa que clear() afeta a saída de get_stats()."""
    processor = AsyncMock()
    queue = FrameQueue(processor=processor, max_size=10, num_workers=0)

    queue._processed_count = 100
    queue._dropped_count = 10

    stats_before = queue.get_stats()
    assert stats_before["processed"] == 100
    assert stats_before["dropped"] == 10

    queue.clear()

    stats_after = queue.get_stats()
    assert stats_after["processed"] == 0
    assert stats_after["dropped"] == 0
