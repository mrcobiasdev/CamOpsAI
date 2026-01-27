"""Script para verificar configuração das câmeras."""

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
            print("\nNenhuma câmera encontrada!")
            return

        print(f"\n{'=' * 60}")
        print(f"Cameras Configuradas ({len(cameras)})")
        print(f"{'=' * 60}\n")

        for i, cam in enumerate(cameras, 1):
            print(f"{i}. {cam.name}")
            print(f"   Sensitivity: {cam.motion_sensitivity}")
            print(f"   Threshold: {cam.motion_threshold}%")
            print(
                f"   Motion Detection: {'ATIVADO' if cam.motion_detection_enabled else 'DESATIVADO'}"
            )
            print()


if __name__ == "__main__":
    asyncio.run(main())
