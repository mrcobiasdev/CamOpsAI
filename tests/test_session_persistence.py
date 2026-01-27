"""Script para testar a persistência de sessão do WhatsApp."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.alerts.whatsapp_web import WhatsAppWebClient


async def test_session_persistence():
    """Testa se a sessão é persistente entre execuções."""

    client = WhatsAppWebClient(
        session_dir="./sessions/whatsapp_test",
        headless=False,  # Mostrar navegador para debug
    )

    try:
        print("\n=== Iniciando primeira execução ===")
        await client.initialize()
        print("✓ Cliente inicializado com sucesso")
        print(f"✓ Autenticado: {client.is_configured}")

        # Enviar uma mensagem de teste
        # Substitua pelo seu número
        phone = input("\nDigite seu número (com DDD, ex: 5511999999999): ").strip()
        message = "Teste de persistência de sessão - Execução 1"

        result = await client.send_message(phone, message)
        print(f"\n✓ Resultado do envio: {result}")

        # Salvar sessão
        await client._save_session()
        print("\n✓ Sessão salva")

        # Fechar cliente
        await client.close()
        print("✓ Cliente fechado")

        print("\n=== Aguardando 5 segundos antes da segunda execução ===")
        await asyncio.sleep(5)

        print("\n=== Iniciando segunda execução ===")
        # Criar novo cliente
        client2 = WhatsAppWebClient(
            session_dir="./sessions/whatsapp_test",
            headless=False,
        )

        await client2.initialize()
        print("✓ Cliente inicializado com sucesso")
        print(f"✓ Autenticado: {client2.is_configured}")

        # Enviar outra mensagem
        message2 = "Teste de persistência de sessão - Execução 2"
        result2 = await client2.send_message(phone, message2)
        print(f"\n✓ Resultado do envio: {result2}")

        if result2.get("success") and result.get("success"):
            print("\n✅ TESTE DE PERSISTÊNCIA BEM-SUCEDIDO!")
            print("A sessão foi recuperada sem precisar escanear QR code novamente.")
        else:
            print("\n❌ TESTE FALHOU")
            print("A sessão não foi recuperada corretamente.")

        await client2.close()

    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback

        traceback.print_exc()
        if client:
            await client.close()


if __name__ == "__main__":
    asyncio.run(test_session_persistence())
