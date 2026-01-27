"""Script rápido para atualizar sensitivity das câmeras."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import AsyncSessionLocal
from src.storage.repository import CameraRepository


async def main():
    async with AsyncSessionLocal() as session:
        repo = CameraRepository(session)
        cameras = await repo.get_all()

        if not cameras:
            print("Nenhuma câmera encontrada!")
            return

        print(f"\nAtualizando {len(cameras)} câmera(s) para HIGH sensitivity...\n")

        for cam in cameras:
            updated = await repo.update(
                cam.id, motion_sensitivity="high", motion_threshold=10.0
            )

            if updated:
                print(f"✅ {cam.name}")
                print(f"   Sensitivity: high")
                print(f"   Threshold: 10.0%")
                print(f"   Blur kernel: (3, 3)")
                print(f"   Pixel threshold: 5")
                print(f"   Pixel scale: 20x")
                print()
            else:
                print(f"❌ {cam.name}: Falha")

        print("=" * 60)
        print("✅ CONFIGURAÇÃO APLICADA!")
        print("=" * 60)
        print("\nReinicie a aplicação para aplicar as mudanças.")
        print("\nResultados esperados com HIGH sensitivity:")
        print("  - Carros passando: 25-50% (antes: 0-3%)")
        print("  - Pessoas andando: 20-35% (antes: 5-10%)")
        print("  - Cena estática: 0-5% (filtrado)")
        print()


if __name__ == "__main__":
    asyncio.run(main())
