"""Factory para criação de cliente WhatsApp baseado no modo de envio."""

import logging

from src.config import settings, WhatsAppSendMode
from src.alerts.whatsapp import WhatsAppClient
from src.alerts.whatsapp_web import WhatsAppWebClient

logger = logging.getLogger(__name__)


async def create_whatsapp_client():
    """Cria um cliente WhatsApp baseado na configuração de modo de envio.

    Returns:
        Instância de WhatsAppClient (API) ou WhatsAppWebClient (Web)

    Raises:
        ValueError: Se o modo de envio for inválido
        RuntimeError: Se as dependências necessárias não estiverem disponíveis
    """
    mode = settings.whatsapp_send_mode

    logger.info(f"Criando cliente WhatsApp com modo: {mode}")

    if mode == WhatsAppSendMode.API:
        logger.info("Usando WhatsApp Business API")
        return WhatsAppClient()

    elif mode == WhatsAppSendMode.WEB:
        logger.info("Usando WhatsApp Web automação")

        try:
            import playwright
            from playwright.async_api import async_playwright
        except ImportError as e:
            error_msg = (
                "Playwright não está instalado. "
                "Instale com: pip install playwright && playwright install"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        client = WhatsAppWebClient(
            session_dir=settings.whatsapp_session_dir,
            headless=settings.whatsapp_headless,
        )

        return client

    else:
        raise ValueError(f"Modo de envio inválido: {mode}. Use 'api' ou 'web'")


def create_whatsapp_client_sync():
    """Versão síncrona para compatibilidade com código existente.

    Note:
        Para modo Web, o cliente precisa ser inicializado assincronamente
        chamando client.initialize() antes de enviar mensagens.
    """
    mode = settings.whatsapp_send_mode

    if mode == WhatsAppSendMode.API:
        return WhatsAppClient()

    elif mode == WhatsAppSendMode.WEB:
        return WhatsAppWebClient(
            session_dir=settings.whatsapp_session_dir,
            headless=settings.whatsapp_headless,
        )

    else:
        raise ValueError(f"Modo de envio inválido: {mode}. Use 'api' ou 'web'")
