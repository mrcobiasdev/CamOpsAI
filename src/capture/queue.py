"""Fila de processamento de frames."""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Callable, Awaitable, Optional

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FrameItem:
    """Item da fila de frames."""

    camera_id: uuid.UUID
    frame_data: bytes
    timestamp: float


class FrameQueue:
    """Fila assíncrona para processamento de frames.

    Gerencia o processamento de frames através de múltiplos workers assíncronos.
    Rastreia estatísticas de frames processados e descartados.
    """

    def __init__(
        self,
        processor: Optional[Callable[[FrameItem], Awaitable[None]]] = None,
        max_size: Optional[int] = None,
        num_workers: int = 2,
    ):
        self.max_size = max_size or settings.max_queue_size
        self._queue: asyncio.Queue[FrameItem] = asyncio.Queue(maxsize=self.max_size)
        self._processor = processor
        self._num_workers = num_workers
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._processed_count = 0
        self._dropped_count = 0

    @property
    def size(self) -> int:
        """Retorna o tamanho atual da fila."""
        return self._queue.qsize()

    @property
    def is_full(self) -> bool:
        """Verifica se a fila está cheia."""
        return self._queue.full()

    @property
    def processed_count(self) -> int:
        """Retorna quantidade de frames processados."""
        return self._processed_count

    @property
    def dropped_count(self) -> int:
        """Retorna quantidade de frames descartados."""
        return self._dropped_count

    def set_processor(self, processor: Callable[[FrameItem], Awaitable[None]]):
        """Define o processador de frames."""
        self._processor = processor

    async def put(
        self, camera_id: uuid.UUID, frame_data: bytes, timestamp: float
    ) -> bool:
        """Adiciona um frame na fila."""
        item = FrameItem(
            camera_id=camera_id,
            frame_data=frame_data,
            timestamp=timestamp,
        )

        try:
            # Tenta adicionar sem bloquear
            self._queue.put_nowait(item)
            return True
        except asyncio.QueueFull:
            # Fila cheia, descarta o frame mais antigo se necessário
            self._dropped_count += 1
            logger.warning(
                f"Fila cheia, frame descartado. "
                f"Total descartados: {self._dropped_count}"
            )
            return False

    async def get(self) -> FrameItem:
        """Obtém o próximo frame da fila."""
        return await self._queue.get()

    def task_done(self):
        """Marca uma tarefa como concluída."""
        self._queue.task_done()

    async def start_workers(self):
        """Inicia os workers de processamento."""
        if self._running:
            return

        if not self._processor:
            raise ValueError("Processador não definido")

        self._running = True
        self._workers = [
            asyncio.create_task(self._worker(i)) for i in range(self._num_workers)
        ]
        logger.info(f"Iniciados {self._num_workers} workers de processamento")

    async def stop_workers(self):
        """Para os workers de processamento."""
        self._running = False

        for worker in self._workers:
            worker.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers = []
        logger.info("Workers de processamento parados")

    async def _worker(self, worker_id: int):
        """Worker que processa frames da fila."""
        logger.info(f"Worker {worker_id} iniciado")

        while self._running:
            try:
                # Aguarda um frame da fila
                item = await asyncio.wait_for(self.get(), timeout=1.0)

                try:
                    # Processa o frame
                    await self._processor(item)
                    self._processed_count += 1
                except Exception as e:
                    logger.error(f"Worker {worker_id} erro ao processar frame: {e}")
                finally:
                    self.task_done()

            except asyncio.TimeoutError:
                # Timeout normal, continua esperando
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} erro inesperado: {e}")

        logger.info(f"Worker {worker_id} finalizado")

    async def wait_empty(self, timeout: Optional[float] = None):
        """Aguarda a fila esvaziar."""
        try:
            await asyncio.wait_for(self._queue.join(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Timeout aguardando fila esvaziar")

    def get_stats(self) -> dict:
        """Retorna estatísticas da fila."""
        return {
            "queue_size": self.size,
            "max_size": self.max_size,
            "processed": self._processed_count,
            "dropped": self._dropped_count,
            "workers": len(self._workers),
            "running": self._running,
        }

    def clear(self):
        """Reseta os contadores da fila de processamento."""
        self._processed_count = 0
        self._dropped_count = 0
