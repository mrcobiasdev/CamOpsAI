"""Script de teste rápido para enviar alerta via WhatsApp Web."""

import asyncio
from src.alerts.factory import create_whatsapp_client


async def test_alert():
    """Testa envio de alerta."""
    print("Criando cliente WhatsApp...")
    client = await create_whatsapp_client()

    if hasattr(client, "initialize"):
        print("Inicializando WhatsApp Web...")
        await client.initialize()

    # Testar health check
    print("\nVerificando saúde do cliente...")
    health = await client.health_check()
    print(f"Health check: {health}")

    # Enviar alerta de teste
    print("\nEnviando alerta de teste...")
    result = await client.send_alert(
        to_numbers=["+5561998700962"],
        camera_name="Câmera de Teste",
        description="Pessoa detectada andando pela entrada principal do escritório",
        keywords_matched=["pessoa"],
        priority="normal",
    )

    print(f"\nResultado do envio:")
    print(f"  Sucesso: {result['success']}")
    print(f"  Falhas: {result['failed']}")

    if client:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_alert())
