"""Cliente para envio de mensagens via WhatsApp Business API."""

import logging
from typing import List, Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Cliente para WhatsApp Business API."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        token: Optional[str] = None,
        phone_id: Optional[str] = None,
    ):
        self.api_url = api_url or settings.whatsapp_api_url
        self.token = token or settings.whatsapp_token
        self.phone_id = phone_id or settings.whatsapp_phone_id
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        """Verifica se o cliente está configurado."""
        return bool(self.token and self.phone_id)

    async def _get_client(self) -> httpx.AsyncClient:
        """Retorna ou cria o cliente HTTP."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        """Fecha o cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def send_message(
        self,
        to: str,
        message: str,
    ) -> dict:
        """Envia uma mensagem de texto.

        Args:
            to: Número de telefone no formato internacional (ex: 5511999999999)
            message: Texto da mensagem

        Returns:
            Resposta da API
        """
        if not self.is_configured:
            raise ValueError("WhatsApp não configurado. Verifique token e phone_id.")

        client = await self._get_client()
        url = f"{self.api_url}/{self.phone_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }

        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Mensagem enviada para {to}")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao enviar mensagem: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            raise

    async def send_alert(
        self,
        to_numbers: List[str],
        camera_name: str,
        description: str,
        keywords_matched: List[str],
        priority: str = "normal",
        frame_url: Optional[str] = None,
    ) -> dict:
        """Envia um alerta formatado.

        Args:
            to_numbers: Lista de números para enviar
            camera_name: Nome da câmera
            description: Descrição do evento
            keywords_matched: Palavras-chave que dispararam o alerta
            priority: Nível de prioridade
            frame_url: URL do frame (opcional)

        Returns:
            Dict com resultados de envio
        """
        # Monta a mensagem de alerta
        priority_emoji = {"high": "🚨", "normal": "⚠️", "low": "ℹ️"}.get(
            priority, "⚠️"
        )

        message = f"""{priority_emoji} *ALERTA DE SEGURANÇA*

📷 *Câmera:* {camera_name}

📝 *Descrição:*
{description}

🏷️ *Palavras-chave detectadas:*
{', '.join(keywords_matched)}

⏰ *Prioridade:* {priority.upper()}"""

        if frame_url:
            message += f"\n\n🖼️ *Frame:* {frame_url}"

        results = {
            "success": [],
            "failed": [],
        }

        for number in to_numbers:
            try:
                await self.send_message(number, message)
                results["success"].append(number)
            except Exception as e:
                logger.error(f"Falha ao enviar para {number}: {e}")
                results["failed"].append({"number": number, "error": str(e)})

        return results

    async def send_template(
        self,
        to: str,
        template_name: str,
        template_params: Optional[List[str]] = None,
        language_code: str = "pt_BR",
    ) -> dict:
        """Envia uma mensagem usando template aprovado.

        Args:
            to: Número de telefone
            template_name: Nome do template
            template_params: Parâmetros do template
            language_code: Código do idioma

        Returns:
            Resposta da API
        """
        if not self.is_configured:
            raise ValueError("WhatsApp não configurado.")

        client = await self._get_client()
        url = f"{self.api_url}/{self.phone_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }

        if template_params:
            payload["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": param} for param in template_params
                    ],
                }
            ]

        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao enviar template: {e}")
            raise

    async def health_check(self) -> bool:
        """Verifica se a API do WhatsApp está acessível."""
        if not self.is_configured:
            return False

        try:
            client = await self._get_client()
            url = f"{self.api_url}/{self.phone_id}"
            response = await client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check WhatsApp falhou: {e}")
            return False
