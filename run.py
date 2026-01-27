"""Script de inicialização do CamOpsAI com correção para Windows."""

import sys
import asyncio

# Configurar event loop ANTES de qualquer importação
if sys.platform == "win32":
    if not isinstance(
        asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy
    ):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            print("Event loop policy configurada para WindowsProactorEventLoopPolicy")
        except Exception as e:
            print(f"Aviso: Não foi possível configurar event loop: {e}")

# Agora importa e executa o uvicorn
if __name__ == "__main__":
    from src.config import settings

    import uvicorn

    print(f"Iniciando CamOpsAI em {settings.api_host}:{settings.api_port}")
    print(f"Modo WhatsApp: {settings.whatsapp_send_mode}")

    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
