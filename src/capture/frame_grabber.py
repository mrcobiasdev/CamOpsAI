"""Captura de frames de câmeras RTSP usando OpenCV."""

import asyncio
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np

from src.config import settings
from .camera import CameraConfig, CameraState, CameraStatus
from .motion_detector import MotionDetector

logger = logging.getLogger(__name__)

# Supress FFmpeg stderr noise
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"  # Quiet mode


class FrameGrabber:
    """Captura frames de uma câmera RTSP."""

    def __init__(
        self,
        camera_config: CameraConfig,
        on_frame: Optional[Callable[[uuid.UUID, bytes, float], None]] = None,
    ):
        self.config = camera_config
        self.state = CameraState(config=camera_config)
        self.on_frame = on_frame
        self._capture: Optional[cv2.VideoCapture] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._config_lock = asyncio.Lock()

        # Initialize motion detector with sensitivity preset
        if self.config.motion_detection_enabled:
            # Check if sensitivity is a preset or custom
            sensitivity = getattr(self.config, "motion_sensitivity", "medium")
            if sensitivity in ["low", "medium", "high"]:
                self._motion_detector = MotionDetector.from_sensitivity(
                    sensitivity=sensitivity, threshold=self.config.motion_threshold
                )
            else:
                # Custom sensitivity - use default parameters
                self._motion_detector = MotionDetector(
                    threshold=self.config.motion_threshold
                )
        else:
            self._motion_detector = None

    @property
    def is_running(self) -> bool:
        """Verifica se está capturando."""
        return self._running

    @property
    def status(self) -> CameraStatus:
        """Retorna o status atual."""
        return self.state.status

    def update_config(self, new_config: CameraConfig) -> bool:
        """Atualiza a configuração da câmera em tempo de execução.

        Args:
            new_config: Nova configuração da câmera

        Returns:
            True se atualização foi bem-sucedida, False caso contrário
        """

        async def _update():
            async with self._config_lock:
                old_threshold = self.config.motion_threshold
                old_sensitivity = getattr(self.config, "motion_sensitivity", "medium")
                self.config = new_config

                # Reinicializa o detector de movimento se threshold ou sensitivity mudou
                new_sensitivity = getattr(self.config, "motion_sensitivity", "medium")
                if self.config.motion_detection_enabled:
                    if (
                        self._motion_detector is None
                        or old_threshold != self.config.motion_threshold
                        or old_sensitivity != new_sensitivity
                    ):
                        # Use sensitivity preset if available
                        if new_sensitivity in ["low", "medium", "high"]:
                            self._motion_detector = MotionDetector.from_sensitivity(
                                sensitivity=new_sensitivity,
                                threshold=self.config.motion_threshold,
                            )
                            logger.info(
                                f"Detector de movimento reinicializado: "
                                f"sensitivity={new_sensitivity}, threshold={self.config.motion_threshold}%"
                            )
                        else:
                            self._motion_detector = MotionDetector(
                                threshold=self.config.motion_threshold
                            )
                            logger.info(
                                f"Detector de movimento reinicializado com novo threshold: "
                                f"{self.config.motion_threshold}%"
                            )
                        return True
                elif old_threshold != self.config.motion_threshold:
                    # Threshold mudou mas detecção está desabilitada
                    logger.info(
                        f"Threshold atualizado para {self.config.motion_threshold}% "
                        f"(detecção de movimento desabilitada)"
                    )
                    return True

                return False

        # Executa atualização de forma thread-safe
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(_update())
        except Exception as e:
            logger.error(f"Erro ao atualizar configuração: {e}")
            return False

    async def connect(self) -> bool:
        """Conecta à câmera."""
        self.state.status = CameraStatus.CONNECTING
        logger.info(f"Conectando à câmera {self.config.name} ({self.config.url})")

        try:
            # Executa a conexão em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            self._capture = await loop.run_in_executor(None, self._create_capture)

            if self._capture is None or not self._capture.isOpened():
                raise ConnectionError("Não foi possível abrir o stream")

            self.state.status = CameraStatus.CONNECTED
            self.state.reset_stats()

            # Reset motion detector on connection
            if self._motion_detector:
                self._motion_detector.reset()

            logger.info(f"Câmera {self.config.name} conectada")
            logger.info(
                f"RTSP configuração: transport={settings.rtsp_transport}, "
                f"error_recovery={settings.rtsp_error_recovery}, "
                f"max_consecutive_errors={settings.rtsp_max_consecutive_errors}"
            )
            return True

        except Exception as e:
            self.state.status = CameraStatus.ERROR
            self.state.record_error(str(e))
            logger.error(f"Erro ao conectar à câmera {self.config.name}: {e}")
            return False

    def _create_capture(self) -> cv2.VideoCapture:
        """Cria o objeto de captura (executado em thread)."""
        # Set FFmpeg environment variables before creating VideoCapture
        old_env = {}
        if settings.rtsp_error_recovery:
            # Store old values
            if "OPENCV_FFMPEG_CAPTURE_OPTIONS" in os.environ:
                old_env["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = os.environ[
                    "OPENCV_FFMPEG_CAPTURE_OPTIONS"
                ]
            if "OPENCV_FFMPEG_LOGLEVEL" in os.environ:
                old_env["OPENCV_FFMPEG_LOGLEVEL"] = os.environ["OPENCV_FFMPEG_LOGLEVEL"]

            # Transport protocol
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                f"rtsp_transport;{settings.rtsp_transport}"
            )

        cap = cv2.VideoCapture(self.config.rtsp_url, cv2.CAP_FFMPEG)

        # Configurações para melhor performance com RTSP
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Restore old environment variables
        if settings.rtsp_error_recovery:
            for key, value in old_env.items():
                os.environ[key] = value
            # Remove our temporary env vars
            if "OPENCV_FFMPEG_CAPTURE_OPTIONS" in os.environ:
                del os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"]

        return cap

    async def disconnect(self):
        """Desconecta da câmera."""
        await self.stop()

        if self._capture:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._capture.release)
            self._capture = None

        self.state.status = CameraStatus.DISCONNECTED
        logger.info(f"Câmera {self.config.name} desconectada")

    async def start(self):
        """Inicia a captura de frames."""
        if self._running:
            return

        if self.state.status != CameraStatus.CONNECTED:
            connected = await self.connect()
            if not connected:
                return

        self._running = True
        self.state.status = CameraStatus.CAPTURING
        self._task = asyncio.create_task(self._capture_loop())
        logger.info(f"Captura iniciada para câmera {self.config.name}")

    async def stop(self):
        """Para a captura de frames."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self.state.status == CameraStatus.CAPTURING:
            self.state.status = CameraStatus.CONNECTED

        logger.info(f"Captura parada para câmera {self.config.name}")

    async def _capture_loop(self):
        """Loop principal de captura."""
        interval = self.config.frame_interval
        last_capture = 0
        consecutive_errors = 0

        while self._running:
            try:
                current_time = time.time()

                # Verifica se é hora de capturar
                if current_time - last_capture >= interval:
                    logger.info(
                        f"📸 Capturing frame for camera {self.config.name} "
                        f"(interval: {interval}s, time since last: {current_time - last_capture:.1f}s)"
                    )
                    frame = await self._grab_frame()

                    if frame is not None:
                        self.state.record_frame(current_time)
                        logger.info(
                            f"✅ Frame captured: camera={self.config.name}, "
                            f"size={len(frame)} bytes, "
                            f"total_frames={self.state.frames_captured}"
                        )

                        # Check motion before sending frame
                        if self._motion_detector:
                            should_send = await self._check_motion(frame)
                        else:
                            should_send = True

                        if should_send:
                            # Callback para processar o frame
                            if self.on_frame:
                                self.on_frame(self.config.id, frame, current_time)

                        last_capture = current_time
                        consecutive_errors = 0
                    else:
                        consecutive_errors += 1
                        logger.warning(
                            f"⚠️ Frame capture failed (consecutive errors: {consecutive_errors}/{settings.rtsp_max_consecutive_errors})"
                        )

                # Reconnect only if consecutive errors exceed threshold
                if consecutive_errors >= settings.rtsp_max_consecutive_errors:
                    logger.warning(
                        f"🔄 Too many consecutive errors ({consecutive_errors}), reconnecting camera {self.config.name}"
                    )
                    await self._reconnect()
                    consecutive_errors = 0
                else:
                    # Log that we're waiting for next capture interval
                    time_until_next = interval - (current_time - last_capture)
                    if time_until_next > 0:
                        logger.debug(
                            f"⏳ Waiting {time_until_next:.1f}s before next capture for camera {self.config.name}"
                        )

                # Pequena pausa para não sobrecarregar
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.state.record_error(str(e))
                logger.error(f"Erro na captura da câmera {self.config.name}: {e}")
                await asyncio.sleep(5)  # Pausa antes de tentar novamente

    async def _grab_frame(self) -> Optional[bytes]:
        """Captura um frame da câmera."""
        if not self._capture or not self._capture.isOpened():
            logger.debug(f"Capture not available for camera {self.config.name}")
            return None

        try:
            loop = asyncio.get_event_loop()
            ret, frame = await loop.run_in_executor(None, self._capture.read)

            if not ret or frame is None:
                # Frame failed to decode - this is normal with RTSP/H.264 streams
                # FFmpeg may print warnings to stderr, but we continue gracefully
                logger.debug(
                    f"Frame decode failed for camera {self.config.name} "
                    "(normal with RTSP streams, will retry)"
                )
                return None

            # Validate frame quality
            if not self._validate_frame(frame):
                logger.warning(f"Frame validation failed for camera {self.config.name}")
                return None

            # Converte para JPEG
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return buffer.tobytes()

        except cv2.error as e:
            error_str = str(e).lower()
            if "no frame" in error_str or "missing picture" in error_str:
                # Decoder error - this is normal with RTSP/H.264 streams
                self.state.record_decoder_error()
                logger.debug(
                    f"Decoder error skipped for camera {self.config.name}: {e}"
                )
                return None
            else:
                # Other cv2.error - log and return None
                logger.error(f"CV2 error for camera {self.config.name}: {e}")
                return None
        except Exception as e:
            logger.error(f"Erro ao capturar frame: {e}")
            return None

    async def _check_motion(self, frame_bytes: bytes) -> bool:
        """Check if frame has motion and log results.

        Args:
            frame_bytes: JPEG encoded frame bytes

        Returns:
            True if frame should be sent, False if filtered
        """
        if not self._motion_detector:
            logger.info(
                f"Motion detection DISABLED for camera {self.config.name}, sending frame"
            )
            return True

        try:
            logger.info(
                f"Checking motion for camera {self.config.name} (frame size: {len(frame_bytes)} bytes)"
            )

            # Decode JPEG to numpy array
            loop = asyncio.get_event_loop()
            frame = await loop.run_in_executor(
                None,
                lambda: cv2.imdecode(
                    np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR
                ),
            )

            if frame is None:
                logger.warning("Failed to decode frame, sending to LLM anyway")
                return True

            # Detect motion
            motion_score, has_motion = self._motion_detector.detect_motion(frame)

            # Log and update statistics
            if has_motion:
                self.state.record_sent_frame(motion_score)
                logger.info(
                    f"✅ MOTION DETECTED - camera={self.config.name}, "
                    f"motion_score={motion_score:.2f}%, "
                    f"threshold={self.config.motion_threshold}%, "
                    f"frame_size={len(frame_bytes)} bytes"
                )
            else:
                self.state.record_filtered_frame()
                logger.info(
                    f"⏸️ NO MOTION - camera={self.config.name}, "
                    f"motion_score={motion_score:.2f}%, "
                    f"threshold={self.config.motion_threshold}%, "
                    f"frame_size={len(frame_bytes)} bytes"
                )

            # Check for abnormal detection rates
            self._check_detection_rate()

            return has_motion

        except Exception as e:
            logger.error(f"Error checking motion: {e}, sending frame to LLM")
            # Fail-safe: send frame if motion detection fails
            return True

            # Detect motion
            motion_score, has_motion = self._motion_detector.detect_motion(frame)

            # Log and update statistics
            if has_motion:
                self.state.record_sent_frame(motion_score)
                logger.debug(
                    f"Frame sent: camera={self.config.id}, "
                    f"motion_score={motion_score:.2f}, "
                    f"threshold={self.config.motion_threshold}"
                )
            else:
                self.state.record_filtered_frame()
                logger.debug(
                    f"Frame filtered: camera={self.config.id}, "
                    f"motion_score={motion_score:.2f}, "
                    f"threshold={self.config.motion_threshold}"
                )

            # Check for abnormal detection rates
            self._check_detection_rate()

            return has_motion

        except Exception as e:
            logger.error(f"Error checking motion: {e}, sending frame to LLM")
            # Fail-safe: send frame if motion detection fails
            return True

    def _check_detection_rate(self):
        """Check if detection rate is abnormal and log warning."""
        if self.state.frames_captured < 100:
            return  # Not enough data

        rate = self.state.detection_rate

        if rate < 5.0:
            logger.warning(
                f"Low detection rate: {rate:.1f}% for camera {self.config.name}. "
                f"Consider lowering motion_threshold (current: {self.config.motion_threshold})"
            )
        elif rate > 95.0:
            logger.warning(
                f"High detection rate: {rate:.1f}% for camera {self.config.name}. "
                f"Consider increasing motion_threshold (current: {self.config.motion_threshold})"
            )

    def _validate_frame(self, frame: np.ndarray) -> bool:
        """Validates decoded frame quality before processing."""
        if frame is None:
            return False

        # Check dimensions
        if frame.size == 0 or len(frame.shape) < 2:
            return False

        # Check for uniform color (possible corruption)
        if np.all(frame == frame.flat[0]):
            return False

        # Check resolution is reasonable
        height, width = frame.shape[:2]
        if width < 160 or height < 120:
            return False

        return True

    async def _reconnect(self):
        """Tenta reconectar à câmera."""
        max_attempts = 3
        for attempt in range(max_attempts):
            logger.info(
                f"Tentativa de reconexão {attempt + 1}/{max_attempts} "
                f"para câmera {self.config.name}"
            )

            if self._capture:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._capture.release)

            await asyncio.sleep(2)

            if await self.connect():
                return

        # Falhou todas as tentativas
        self.state.status = CameraStatus.ERROR
        self._running = False
        logger.error(f"Falha ao reconectar à câmera {self.config.name}")

    async def capture_single_frame(self) -> Optional[bytes]:
        """Captura um único frame (para testes/preview)."""
        was_running = self._running

        if not was_running:
            if not await self.connect():
                return None

        frame = await self._grab_frame()

        if not was_running:
            await self.disconnect()

        return frame

    def save_frame(self, frame_bytes: bytes, camera_id: uuid.UUID) -> str:
        """Salva um frame em disco e retorna o caminho."""
        storage_path = Path(settings.frames_storage_path)
        storage_path.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time() * 1000)
        filename = f"{camera_id}_{timestamp}.jpg"
        filepath = storage_path / filename

        with open(filepath, "wb") as f:
            f.write(frame_bytes)

        return str(filepath)
