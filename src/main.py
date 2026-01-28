"""Entry point principal do CamOpsAI."""

import sys

# Fix para Windows: usar ProactorEventLoop para suportar subprocessos
# Precisa ser definido ANTES de importar qualquer coisa assíncrona
if sys.platform == "win32":
    import asyncio

    # Força redefinição da política se necessário
    if not isinstance(
        asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy
    ):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except:
            pass

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import __version__
from src.config import settings
from src.storage.database import init_db, close_db, AsyncSessionLocal
from src.storage.repository import CameraRepository, EventRepository, AlertRepository
from src.capture.camera import CameraConfig, CameraState, CameraStatus
from src.capture.frame_grabber import FrameGrabber
from src.capture.queue import FrameQueue, FrameItem
from src.analysis import LLMVisionFactory, AnalysisResult
from src.alerts.detector import KeywordDetector, AlertRule as DetectorAlertRule
from src.alerts.factory import create_whatsapp_client
from src.api.routes import cameras, events, alerts
from src.api.schemas import HealthResponse, StatsResponse

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class CameraManager:
    """Gerenciador de câmeras e captura."""

    def __init__(self):
        self._grabbers: Dict[uuid.UUID, FrameGrabber] = {}
        self._frame_queue: Optional[FrameQueue] = None

    def set_frame_queue(self, queue: FrameQueue):
        """Define a fila de processamento."""
        self._frame_queue = queue

    async def add_camera(self, config: CameraConfig) -> bool:
        """Adiciona uma câmera ao gerenciador."""
        if config.id in self._grabbers:
            return False

        grabber = FrameGrabber(
            camera_config=config,
            on_frame=self._on_frame_captured,
        )
        self._grabbers[config.id] = grabber
        logger.info(f"Câmera adicionada: {config.name} ({config.id})")
        return True

    def remove_camera(self, camera_id: uuid.UUID):
        """Remove uma câmera do gerenciador."""
        if camera_id in self._grabbers:
            del self._grabbers[camera_id]
            logger.info(f"Câmera removida: {camera_id}")

    async def start_camera(self, camera_id: uuid.UUID):
        """Inicia a captura de uma câmera."""
        grabber = self._grabbers.get(camera_id)
        if not grabber:
            raise ValueError(f"Câmera não encontrada: {camera_id}")
        await grabber.start()

    async def stop_camera(self, camera_id: uuid.UUID):
        """Para a captura de uma câmera."""
        grabber = self._grabbers.get(camera_id)
        if grabber:
            await grabber.stop()

    async def start_all(self):
        """Inicia todas as câmeras habilitadas."""
        for camera_id, grabber in self._grabbers.items():
            if grabber.config.enabled:
                await grabber.start()

    async def stop_all(self):
        """Para todas as câmeras."""
        for grabber in self._grabbers.values():
            await grabber.stop()
            await grabber.disconnect()

    def get_camera_status(self, camera_id: uuid.UUID) -> Optional[dict]:
        """Retorna o status de uma câmera."""
        grabber = self._grabbers.get(camera_id)
        if not grabber:
            return None

        state = grabber.state
        return {
            "status": state.status.value,
            "frames_captured": state.frames_captured,
            "frames_sent": state.frames_sent,
            "frames_filtered": state.frames_filtered,
            "detection_rate": state.detection_rate,
            "avg_motion_score": state.avg_motion_score,
            "last_frame_at": (
                datetime.fromtimestamp(state.last_frame_at)
                if state.last_frame_at
                else None
            ),
            "errors_count": state.errors_count,
            "last_error": state.last_error,
            "decoder_error_count": state.decoder_error_count,
            "decoder_error_rate": state.decoder_error_rate,
            "last_decoder_error": state.last_decoder_error,
            "initial_frames_discarded": state.initial_frames_discarded,
        }

    async def update_camera_config(self, camera_id: uuid.UUID) -> bool:
        """Atualiza a configuração de uma câmera em execução.

        Args:
            camera_id: ID da câmera a ser atualizada

        Returns:
            True se atualização foi bem-sucedida, False caso contrário
        """
        grabber = self._grabbers.get(camera_id)
        if not grabber:
            logger.warning(f"Grabber não encontrado para câmera: {camera_id}")
            return False

        async with AsyncSessionLocal() as session:
            repo = CameraRepository(session)
            camera = await repo.get_by_id(camera_id)
            if not camera:
                logger.warning(f"Câmera não encontrada no banco: {camera_id}")
                return False

            # Converte de banco de dados para CameraConfig
            config = CameraConfig(
                id=camera.id,
                name=camera.name,
                url=camera.url,
                enabled=camera.enabled,
                frame_interval=camera.frame_interval,
                motion_detection_enabled=camera.motion_detection_enabled,
                motion_threshold=camera.motion_threshold,
            )

            # Atualiza o grabber com nova configuração
            updated = await grabber.update_config(config)
            if updated:
                logger.info(f"Configuração atualizada para câmera: {camera.name}")
                return True
            else:
                logger.warning(
                    f"Não foi possível atualizar configuração: {camera.name}"
                )
                return False

    def _on_frame_captured(
        self, camera_id: uuid.UUID, frame_data: bytes, timestamp: float
    ):
        """Callback quando um frame é capturado."""
        if self._frame_queue:
            asyncio.create_task(self._frame_queue.put(camera_id, frame_data, timestamp))


# Instâncias globais
camera_manager = CameraManager()
alert_detector = KeywordDetector()
whatsapp_client = None  # Inicializado no lifespan
frame_queue: Optional[FrameQueue] = None


async def process_frame(item: FrameItem):
    """Processa um frame capturado."""
    try:
        # Obtém o provedor LLM
        llm = LLMVisionFactory.get_instance()

        # Analisa o frame
        result: AnalysisResult = await llm.analyze_frame(item.frame_data)

        # Salva o frame
        storage_path = Path(settings.frames_storage_path)
        storage_path.mkdir(parents=True, exist_ok=True)
        timestamp_ms = int(item.timestamp * 1000)
        frame_filename = f"{item.camera_id}_{timestamp_ms}.jpg"
        frame_path = storage_path / frame_filename

        with open(frame_path, "wb") as f:
            f.write(item.frame_data)

        # Salva o evento no banco de dados
        async with AsyncSessionLocal() as session:
            event_repo = EventRepository(session)
            event = await event_repo.create(
                camera_id=item.camera_id,
                description=result.description,
                keywords=result.keywords,
                frame_path=str(frame_path),
                confidence=result.confidence,
                llm_provider=result.provider,
                llm_model=result.model,
                processing_time_ms=result.processing_time_ms,
            )
            await session.commit()

            # Verifica alertas
            matches = alert_detector.detect(
                description=result.description,
                keywords=result.keywords,
                camera_id=item.camera_id,
            )

            # Envia alertas via WhatsApp
            if matches and whatsapp_client and whatsapp_client.is_configured:
                alert_repo = AlertRepository(session)
                camera_repo = CameraRepository(session)
                camera = await camera_repo.get_by_id(item.camera_id)
                camera_name = camera.name if camera else str(item.camera_id)

                for match in matches:
                    # Envia alerta
                    send_result = await whatsapp_client.send_alert(
                        to_numbers=match.phone_numbers,
                        camera_name=camera_name,
                        description=result.description,
                        keywords_matched=match.keywords_matched,
                        priority=match.priority,
                    )

                    # Registra log
                    status = "sent" if send_result["success"] else "failed"
                    error_msg = None
                    if send_result["failed"]:
                        error_msg = str(send_result["failed"])

                    await alert_repo.create_log(
                        event_id=event.id,
                        alert_rule_id=match.rule_id,
                        keywords_matched=match.keywords_matched,
                        sent_to=match.phone_numbers,
                        status=status,
                        error_message=error_msg,
                    )

                await session.commit()

        logger.info(
            f"Frame processado: câmera={item.camera_id}, "
            f"keywords={result.keywords}, "
            f"alertas={len(matches)}"
        )

    except Exception as e:
        logger.error(f"Erro ao processar frame: {e}")


async def load_cameras_from_db():
    """Carrega câmeras do banco de dados."""
    async with AsyncSessionLocal() as session:
        repo = CameraRepository(session)
        cameras_db = await repo.get_all()

        for cam in cameras_db:
            config = CameraConfig(
                id=cam.id,
                name=cam.name,
                url=cam.url,
                enabled=cam.enabled,
                frame_interval=cam.frame_interval,
                motion_detection_enabled=cam.motion_detection_enabled,
                motion_threshold=cam.motion_threshold,
            )
            await camera_manager.add_camera(config)


async def load_alert_rules_from_db():
    """Carrega regras de alerta do banco de dados."""
    async with AsyncSessionLocal() as session:
        repo = AlertRepository(session)
        rules = await repo.get_all_rules()

        for rule in rules:
            alert_detector.add_rule(
                DetectorAlertRule(
                    id=rule.id,
                    name=rule.name,
                    keywords=rule.keywords,
                    phone_numbers=rule.phone_numbers,
                    camera_ids=rule.camera_ids,
                    enabled=rule.enabled,
                    priority=rule.priority,
                    cooldown_seconds=rule.cooldown_seconds,
                )
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    global frame_queue, whatsapp_client

    logger.info("Iniciando CamOpsAI...")

    # Inicializa banco de dados
    await init_db()
    logger.info("Banco de dados inicializado")

    # Cria diretório de frames
    Path(settings.frames_storage_path).mkdir(parents=True, exist_ok=True)

    # Inicializa cliente WhatsApp
    try:
        whatsapp_client = await create_whatsapp_client()

        # Inicializa o cliente Web (abre navegador e autentica)
        if hasattr(whatsapp_client, "initialize"):
            logger.info("Inicializando WhatsApp Web (abre navegador e autenticação)...")
            await whatsapp_client.initialize()

        logger.info(
            f"Cliente WhatsApp inicializado (modo: {settings.whatsapp_send_mode})"
        )
    except Exception as e:
        logger.warning(f"Não foi possível inicializar cliente WhatsApp: {e}")
        whatsapp_client = None

    # Inicializa fila de processamento
    frame_queue = FrameQueue(processor=process_frame, num_workers=2)
    frame_queue.clear()
    camera_manager.set_frame_queue(frame_queue)

    # Carrega dados do banco
    await load_cameras_from_db()
    await load_alert_rules_from_db()

    # Inicia workers de processamento
    await frame_queue.start_workers()

    # Inicia câmeras habilitadas
    await camera_manager.start_all()

    logger.info("CamOpsAI iniciado com sucesso")

    yield

    # Shutdown
    logger.info("Encerrando CamOpsAI...")

    await camera_manager.stop_all()
    await frame_queue.stop_workers()

    if whatsapp_client:
        try:
            if hasattr(whatsapp_client, "close"):
                await whatsapp_client.close()
        except Exception as e:
            logger.error(f"Erro ao fechar cliente WhatsApp: {e}")

    await close_db()

    logger.info("CamOpsAI encerrado")


# Cria aplicação FastAPI
app = FastAPI(
    title="CamOpsAI",
    description="Sistema de Monitoramento Inteligente de Câmeras IP",
    version=__version__,
    lifespan=lifespan,
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra rotas
app.include_router(cameras.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Verifica a saúde do sistema."""
    # Verifica LLM
    llm_health = await LLMVisionFactory.check_provider_health()

    # Verifica WhatsApp
    whatsapp_health = False
    if whatsapp_client:
        try:
            if hasattr(whatsapp_client, "health_check"):
                whatsapp_check = await whatsapp_client.health_check()
                # Web client returns dict, API client returns bool
                if isinstance(whatsapp_check, dict):
                    whatsapp_health = whatsapp_check.get("status") == "healthy"
                else:
                    whatsapp_health = whatsapp_check
            elif hasattr(whatsapp_client, "is_configured"):
                whatsapp_health = whatsapp_client.is_configured
        except Exception as e:
            logger.error(f"Erro ao verificar saúde do WhatsApp: {e}")
            whatsapp_health = False

    return HealthResponse(
        status="healthy",
        database=True,  # Se chegou aqui, o banco está OK
        llm_provider=llm_health,
        whatsapp=whatsapp_health,
        version=__version__,
    )


@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats():
    """Retorna estatísticas do sistema."""
    async with AsyncSessionLocal() as session:
        camera_repo = CameraRepository(session)
        cameras_all = await camera_repo.get_all()
        cameras_active = await camera_repo.get_all(enabled_only=True)

        event_repo = EventRepository(session)
        events_all = await event_repo.get_timeline(limit=1000)

        alert_repo = AlertRepository(session)
        alerts_all = await alert_repo.get_logs(limit=1000)

    queue_stats = frame_queue.get_stats() if frame_queue else {}

    # Aggregate motion detection stats from all cameras
    motion_total = 0
    motion_sent = 0
    motion_filtered = 0
    for grabber in camera_manager._grabbers.values():
        state = grabber.state
        motion_total += state.frames_captured
        motion_sent += state.frames_sent
        motion_filtered += state.frames_filtered

    motion_rate = (motion_sent / motion_total * 100) if motion_total > 0 else 0.0

    # Aggregate decoder health stats from all cameras
    decoder_total_errors = 0
    decoder_rates = []
    for grabber in camera_manager._grabbers.values():
        state = grabber.state
        decoder_total_errors += state.decoder_error_count
        if state.decoder_error_rate > 0:
            decoder_rates.append(state.decoder_error_rate)

    decoder_avg_rate = sum(decoder_rates) / len(decoder_rates) if decoder_rates else 0.0

    return StatsResponse(
        cameras_total=len(cameras_all),
        cameras_active=len(cameras_active),
        events_total=len(events_all),
        events_today=0,  # TODO: implementar filtro por data
        alerts_sent_total=len(alerts_all),
        alerts_sent_today=0,  # TODO: implementar filtro por data
        queue_size=queue_stats.get("queue_size", 0),
        queue_processed=queue_stats.get("processed", 0),
        queue_dropped=queue_stats.get("dropped", 0),
        motion_frames_total=motion_total,
        motion_frames_sent=motion_sent,
        motion_frames_filtered=motion_filtered,
        motion_detection_rate=motion_rate,
        decoder_total_errors=decoder_total_errors,
        decoder_avg_error_rate=decoder_avg_rate,
    )


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {
        "name": "CamOpsAI",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import asyncio
    import sys
    import uvicorn

    # Fix para Windows: redefinir política de event loop para Proactor
    if sys.platform == "win32":
        if not isinstance(
            asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy
        ):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
