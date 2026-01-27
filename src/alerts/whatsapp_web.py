"""Cliente para envio de mensagens via WhatsApp Web usando Playwright."""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from src.config import settings

logger = logging.getLogger(__name__)


class WhatsAppWebClient:
    """Cliente para WhatsApp Web usando Playwright."""

    def __init__(
        self,
        session_dir: Optional[str] = None,
        headless: bool = True,
    ):
        self.session_dir = Path(session_dir or settings.whatsapp_session_dir)
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._authenticated = False
        self._initialized = False
        self._user_data_dir = self.session_dir / "browser_profile"
        self._use_persistent = (
            True  # Usa contexto persistente para melhor recuperação de sessão
        )

    async def initialize(self):
        """Inicializa o browser e context do Playwright."""
        if self._initialized:
            return

        try:
            logger.info("Iniciando WhatsApp Web com Playwright...")

            self._playwright = await async_playwright().start()

            self.session_dir.mkdir(parents=True, exist_ok=True)

            # Cria diretório para perfil do navegador se não existir
            self._user_data_dir.mkdir(parents=True, exist_ok=True)

            if self._use_persistent:
                # Usa contexto persistente para melhor recuperação de sessão
                logger.info(f"Usando perfil persistente em: {self._user_data_dir}")
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self._user_data_dir),
                    headless=self.headless,
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                    ],
                    accept_downloads=False,
                    ignore_https_errors=True,
                )

                # Com launch_persistent_context, o contexto já tem páginas
                if self._context.pages:
                    self._page = self._context.pages[0]
                else:
                    self._page = await self._context.new_page()
            else:
                # Usa browser normal (fallback)
                self._browser = await self._playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                    ],
                )

                session_file = self.session_dir / "state.json"

                # Verificar se o arquivo existe e tem conteúdo válido
                session_valid = False
                if session_file.exists():
                    try:
                        file_size = session_file.stat().st_size
                        logger.info(
                            f"Arquivo de sessão encontrado: {session_file} ({file_size} bytes)"
                        )

                        if file_size > 100:
                            with open(session_file, "r") as f:
                                state_data = json.load(f)
                                logger.info(
                                    f"Estrutura da sessão: {list(state_data.keys())}"
                                )
                                has_cookies = (
                                    state_data.get("cookies")
                                    and len(state_data["cookies"]) > 0
                                )
                                has_origins = (
                                    state_data.get("origins")
                                    and len(state_data["origins"]) > 0
                                )

                                if has_cookies and has_origins:
                                    logger.info(
                                        f"Sessão válida: {len(state_data['cookies'])} cookies, {len(state_data['origins'])} origins"
                                    )
                                    session_valid = True
                                else:
                                    logger.warning(
                                        f"Sessão incompleta - cookies: {has_cookies}, origins: {has_origins}"
                                    )
                        else:
                            logger.warning(
                                f"Arquivo de sessão muito pequeno: {file_size} bytes"
                            )
                    except (json.JSONDecodeError, Exception) as e:
                        logger.warning(f"Erro ao validar arquivo de sessão: {e}")
                        if session_file.exists():
                            session_file.unlink()

                if session_valid:
                    logger.info(f"Carregando sessão existente de {session_file}")
                    self._context = await self._browser.new_context(
                        storage_state=str(session_file),
                        viewport={"width": 1280, "height": 720},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        ignore_https_errors=True,
                    )
                else:
                    logger.info(
                        "Nenhuma sessão válida encontrada, criando nova sessão..."
                    )
                    self._context = await self._browser.new_context(
                        viewport={"width": 1280, "height": 720},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        ignore_https_errors=True,
                    )

                self._page = await self._context.new_page()

            await self._authenticate()

            self._initialized = True
            logger.info("WhatsApp Web inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar WhatsApp Web: {e}")
            await self.close()
            raise

    async def _authenticate(self):
        """Autentica no WhatsApp Web (QR code ou sessão salva)."""
        try:
            logger.info("Verificando se já está na página do WhatsApp Web...")
            current_url = self._page.url

            # Se já estiver no WhatsApp Web, verifica se precisa autenticar
            if "web.whatsapp.com" in current_url:
                logger.info(f"Já está no WhatsApp Web: {current_url}")
                # Verifica se precisa autenticar (QR code visível)
                qr_code_element = await self._page.query_selector(
                    "canvas[aria-label^='Scan this QR code']"
                )

                if not qr_code_element:
                    # Sessão pode estar ativa, verifica campo de chat
                    logger.info("Sessão pode estar ativa, verificando campo de chat...")
                    try:
                        chat_input = await self._page.wait_for_selector(
                            "div[contenteditable='true']",
                            state="visible",
                            timeout=10000,
                        )
                        if chat_input:
                            logger.info("Sessão ativa encontrada!")
                            self._authenticated = True
                            return
                    except Exception as e:
                        logger.info(f"Sessão não ativa: {e}")

            logger.info("Navegando para WhatsApp Web...")
            try:
                await self._page.goto(
                    "https://web.whatsapp.com",
                    wait_until="domcontentloaded",
                    timeout=60000,  # 60 segundos
                )
                logger.info("Página carregada (DOM content loaded)")
            except Exception as e:
                logger.warning(f"Timeout ao carregar página: {e}")
                logger.info("Tentando continuar mesmo assim...")

            logger.info("Aguardando 3 segundos para estabilizar...")
            await asyncio.sleep(3)

            # Verificar se há QR code (precisa autenticar)
            qr_code_element = await self._page.query_selector(
                "canvas[aria-label^='Scan this QR code']"
            )

            if qr_code_element:
                logger.info("=" * 60)
                logger.info("QR CODE DETECTADO")
                logger.info(
                    "Escaneie o QR code com seu aplicativo WhatsApp para autenticar"
                )
                logger.info("O navegador ficará aberto até você escanear")
                logger.info("=" * 60)

                # Esperar o campo de chat aparecer (autenticação completa)
                await self._page.wait_for_selector(
                    "div[contenteditable='true']",
                    state="visible",
                    timeout=600000,  # 10 minutos para scanear QR code
                )

                self._authenticated = True
                logger.info("Autenticação bem-sucedida!")

                await asyncio.sleep(3)

                state = await self._context.storage_state()
                session_file = self.session_dir / "state.json"
                with open(session_file, "w") as f:
                    json.dump(state, f)
                logger.info(f"Sessão salva em {session_file}")

            else:
                # Verificar se já está autenticado (sessão carregada)
                logger.info("Sessão carregada, verificando autenticação...")

                # Primeiro, espera um pouco para a página carregar
                await asyncio.sleep(5)

                # Tenta encontrar o campo de chat com timeout maior
                try:
                    logger.info("Aguardando campo de chat (timeout: 30s)...")
                    chat_input = await self._page.wait_for_selector(
                        "div[contenteditable='true']",
                        state="visible",
                        timeout=30000,
                    )
                    logger.info("Campo de chat encontrado!")
                    if chat_input:
                        logger.info("Sessão restaurada com sucesso")
                        self._authenticated = True

                        # Salva o estado da sessão para garantir persistência
                        state = await self._context.storage_state()
                        session_file = self.session_dir / "state.json"
                        with open(session_file, "w") as f:
                            json.dump(state, f)
                        logger.info(f"Sessão salva em {session_file}")
                        return
                except Exception as e:
                    logger.warning(f"Não foi possível verificar autenticação: {e}")

                # Se não encontrou o campo de chat, verifica se o QR code apareceu
                logger.info("Verificando se QR code apareceu (sessão expirou)...")
                qr_check = await self._page.query_selector(
                    "canvas[aria-label^='Scan this QR code']"
                )

                if qr_check:
                    logger.warning("Sessão expirou! QR code apareceu novamente")
                    raise Exception(
                        "Sessão expirada, precisa escanear QR code novamente"
                    )
                else:
                    # Tenta com múltiplos seletores para o campo de chat
                    logger.info("Tentando com múltiplos seletores...")
                    selectors = [
                        'div[contenteditable="true"][data-tab="10"]',
                        'div[contenteditable="true"][data-tab="3"]',
                        "div[contenteditable='true']",
                    ]
                    found = False
                    for selector in selectors:
                        try:
                            chat_input = await self._page.wait_for_selector(
                                selector,
                                state="visible",
                                timeout=10000,
                            )
                            if chat_input:
                                logger.info(
                                    f"Sessão restaurada com sucesso (seletor: {selector})"
                                )
                                self._authenticated = True
                                found = True

                                # Salva o estado da sessão
                                state = await self._context.storage_state()
                                session_file = self.session_dir / "state.json"
                                with open(session_file, "w") as f:
                                    json.dump(state, f)
                                logger.info(f"Sessão salva em {session_file}")
                                break
                        except Exception as e:
                            logger.debug(f"Seletor {selector} não funcionou: {e}")

                    if not found:
                        logger.error("Campo de chat não encontrado")
                        logger.info("Tirando screenshot para debug...")
                        try:
                            await self._page.screenshot(path="debug_auth_fail.png")
                        except:
                            pass
                        raise Exception(
                            "Não foi possível verificar autenticação após carregar sessão"
                        )

        except Exception as e:
            logger.error(f"Erro durante autenticação: {e}")
            raise

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
            Resposta com status do envio
        """
        if not self._initialized:
            await self.initialize()

        if not self._authenticated:
            raise RuntimeError("WhatsApp Web não está autenticado")

        try:
            # Remove o + do número se existir
            phone_clean = to.replace("+", "")
            url = f"https://web.whatsapp.com/send?phone={phone_clean}"
            logger.info(f"Navegando para chat: {to} ({phone_clean})")

            await self._page.goto(url, wait_until="domcontentloaded", timeout=120000)
            await asyncio.sleep(3)

            # Seleciona o campo de mensagem corrigido (data-tab="10" ou "3")
            message_input = await self._page.wait_for_selector(
                'div[contenteditable="true"][data-tab="10"]',
                state="visible",
                timeout=30000,
            )

            # Se não achou, tenta o antigo
            if not message_input:
                logger.warning("Campo data-tab=10 não encontrado, tentando data-tab=3")
                message_input = await self._page.wait_for_selector(
                    'div[contenteditable="true"][data-tab="3"]',
                    state="visible",
                    timeout=5000,
                )

            if not message_input:
                raise Exception("Campo de mensagem não encontrado")

            # Aguarda mais um pouco e clica
            await asyncio.sleep(1)
            await message_input.click()
            await asyncio.sleep(1)

            # Digita a mensagem
            await message_input.fill(message)
            await asyncio.sleep(1)

            # Tenta encontrar botão de envio (pode mudar de ícone)
            send_button = await self._page.query_selector('span[data-icon="send"]')

            if not send_button:
                # Tenta pressionar Enter
                logger.info("Botão de envio não encontrado, tentando Enter")
                await message_input.press("Enter")
            else:
                await send_button.click()

            logger.info(f"Mensagem enviada para {to}")

            await asyncio.sleep(2)

            # Salva a sessão após cada mensagem bem-sucedida
            await self._save_session()

            return {
                "status": "sent",
                "phone": to,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            return {
                "status": "failed",
                "phone": to,
                "success": False,
                "error": str(e),
            }

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
        priority_emoji = {"high": "🚨", "normal": "⚠️", "low": "ℹ️"}.get(priority, "⚠️")

        message = f"""{priority_emoji} *ALERTA DE SEGURANÇA*

📷 *Câmera:* {camera_name}

📝 *Descrição:*
{description}

🏷️ *Palavras-chave detectadas:*
{", ".join(keywords_matched)}

⏰ *Prioridade:* {priority.upper()}"""

        if frame_url:
            message += f"\n\n🖼️ *Frame:* {frame_url}"

        results = {
            "success": [],
            "failed": [],
        }

        for number in to_numbers:
            try:
                result = await self.send_message(number, message)
                if result.get("success"):
                    results["success"].append(number)
                else:
                    results["failed"].append(
                        {"number": number, "error": result.get("error")}
                    )
            except Exception as e:
                logger.error(f"Falha ao enviar para {number}: {e}")
                results["failed"].append({"number": number, "error": str(e)})

        return results

    async def health_check(self) -> dict:
        """Verifica se o WhatsApp Web está funcionando.

        Returns:
            Dict com status do serviço
        """
        if not self._initialized:
            return {
                "status": "unhealthy",
                "mode": "web",
                "authenticated": False,
                "message": "Cliente não inicializado",
            }

        if not self._authenticated:
            return {
                "status": "unhealthy",
                "mode": "web",
                "authenticated": False,
                "message": "Não autenticado",
            }

        try:
            if self._page and not self._page.is_closed():
                chat_input = await self._page.query_selector(
                    "div[contenteditable='true']"
                )
                is_active = chat_input is not None

                return {
                    "status": "healthy" if is_active else "degraded",
                    "mode": "web",
                    "authenticated": True,
                    "active": is_active,
                }
            else:
                return {
                    "status": "unhealthy",
                    "mode": "web",
                    "authenticated": False,
                    "message": "Página fechada",
                }
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return {
                "status": "unhealthy",
                "mode": "web",
                "authenticated": False,
                "error": str(e),
            }

    async def _save_session(self):
        """Salva o estado da sessão do WhatsApp Web (backup)."""
        try:
            if self._context and self._authenticated:
                state = await self._context.storage_state()
                session_file = self.session_dir / "state.json"
                with open(session_file, "w") as f:
                    json.dump(state, f)
                logger.debug(f"Sessão salva em {session_file}")
        except Exception as e:
            logger.warning(f"Erro ao salvar sessão: {e}")

    async def close(self):
        """Fecha o browser e libera recursos."""
        try:
            # Salva a sessão antes de fechar (backup)
            await self._save_session()

            if self._use_persistent:
                # Com launch_persistent_context, self._context já é o contexto persistente
                if self._context:
                    await self._context.close()
            else:
                # Com browser normal, fecha página, contexto e browser separadamente
                if self._page and not self._page.is_closed():
                    await self._page.close()

                if self._context:
                    await self._context.close()

                if self._browser:
                    await self._browser.close()

            if self._playwright:
                await self._playwright.stop()

            self._initialized = False
            self._authenticated = False
            logger.info("WhatsApp Web fechado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao fechar WhatsApp Web: {e}")

    @property
    def is_configured(self) -> bool:
        """Verifica se o cliente está configurado."""
        return self._authenticated
