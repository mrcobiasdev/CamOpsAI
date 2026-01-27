"""Script para configurar HIGH sensitivity em todas as câmeras."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import AsyncSessionLocal
from src.storage.repository import CameraRepository
from src.main import camera_manager


async def main():
    async with AsyncSessionLocal() as session:
        repo = CameraRepository(session)
        cameras = await repo.get_all()

        if not cameras:
            print("Nenhuma câmera encontrada!")
            return

        print(f"\nConfigurando HIGH sensitivity em {len(cameras)} câmera(s)...\n")

        for cam in cameras:
            # Atualizar no banco
            updated = await repo.update(
                cam.id, motion_sensitivity="high", motion_threshold=10.0
            )

            if updated:
                print(f"✅ {cam.name}: sensitivity=HIGH, threshold=10.0%")

                # Hot-reload
                success = await camera_manager.update_camera_config(cam.id)
                if success:
                    print(f"   🔄 Hot-reload aplicado!")
                else:
                    print(
                        f"   ⚠️  Camera não está rodando (será aplicado no próximo start)"
                    )
            else:
                print(f"❌ {cam.name}: Falha ao atualizar")

        print("\n" + "=" * 60)
        print("CONFIGURAÇÃO APLICADA")
        print("=" * 60)
        print("\nResultados esperados:")
        print("  - Carros passando: motion_score >= 25% (detectado)")
        print("  - Pessoas andando: motion_score >= 20% (detectado)")
        print("  - Cena estática: motion_score < 5% (filtrado)")
        print("\nMonitore os logs para ver os motion scores!")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
