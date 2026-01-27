"""Script para ajustar o threshold de detecção de movimento de forma interativa."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage.database import AsyncSessionLocal
from src.storage.repository import CameraRepository
from src.capture.camera import CameraConfig
from src.main import camera_manager


async def main():
    """Adjust motion detection threshold for cameras."""
    async with AsyncSessionLocal() as session:
        repo = CameraRepository(session)

        # List all cameras
        cameras = await repo.get_all()

        if not cameras:
            print("❌ Nenhuma câmera encontrada!")
            return

        print(f"\n📷 Encontradas {len(cameras)} câmeras:\n")

        for i, cam in enumerate(cameras, 1):
            sensitivity = getattr(cam, "motion_sensitivity", "medium")
            print(
                f"{i}. {cam.name} - "
                f"Sensitivity: {sensitivity}, "
                f"Threshold: {cam.motion_threshold}%, "
                f"Motion detection: {'ATIVADO' if cam.motion_detection_enabled else 'DESATIVADO'}"
            )

        print("\n" + "=" * 70)
        print("⚙️  Opções de Ajuste - Sensitivity Presets:")
        print("=" * 70)
        print()
        print("1. 🔥 HIGH Sensitivity (MUITO sensível)")
        print("   - Detecta qualquer movimento (carros, pessoas, animais)")
        print("   - Ideal para ruas movimentadas e monitoramento outdoor")
        print("   - Pode gerar falsos positivos em cenas com vento/árvores")
        print()
        print("2. ✅ MEDIUM Sensitivity [RECOMENDADO]")
        print("   - Detecta movimentos claros (carros passando, pessoas andando)")
        print("   - Balanceado para indoor e outdoor")
        print("   - Poucos falsos positivos")
        print()
        print("3. 🎯 LOW Sensitivity (conservador)")
        print("   - Apenas movimentos fortes e óbvios")
        print("   - Mínimos falsos positivos")
        print("   - Pode perder movimentos sutis")
        print()
        print("=" * 70)
        print("Opções Avançadas:")
        print("=" * 70)
        print()
        print("4. 🔢 Threshold personalizado (mantém sensitivity atual)")
        print("5. 🚫 DESATIVAR detecção de movimento")
        print()
        print("0. ❌ Sair sem alterações")
        print()
        print("=" * 70)

        choice = input("👉 Escolha uma opção (0-5): ").strip()

        if choice == "0":
            print("❌ Saindo sem alterações...")
            return

        new_sensitivity = None
        new_threshold = None

        if choice == "1":
            new_sensitivity = "high"
            new_threshold = 10.0  # Keep default threshold, sensitivity does the work
            print("✅ Sensitivity: HIGH (detecta carros e pessoas facilmente)")
        elif choice == "2":
            new_sensitivity = "medium"
            new_threshold = 10.0
            print("✅ Sensitivity: MEDIUM (balanceado)")
        elif choice == "3":
            new_sensitivity = "low"
            new_threshold = 10.0
            print("✅ Sensitivity: LOW (conservador)")
        elif choice == "4":
            try:
                new_threshold = float(input("🔢 Digite o threshold (0.0 a 100.0): "))
                if not 0 <= new_threshold <= 100:
                    print("❌ Threshold deve estar entre 0 e 100!")
                    return
                new_sensitivity = "custom"
                print(
                    f"✅ Threshold personalizado: {new_threshold}% (sensitivity: custom)"
                )
            except ValueError:
                print("❌ Valor inválido!")
                return
        elif choice == "5":
            disable_motion = (
                input(
                    "🔢 Tem certeza que deseja DESATIVAR detecção de movimento? (s/N): "
                )
                .strip()
                .lower()
            )
            if disable_motion == "s":
                for cam in cameras:
                    await repo.update(cam.id, motion_detection_enabled=False)
                print("✅ Detecção de movimento DESATIVADA em todas as câmeras")
                return
            else:
                print("❌ Cancelado - detecção de movimento permanece ATIVADA")
                return
        else:
            print("❌ Opção inválida!")
            return

        # Update all cameras
        print("\n🔄 Atualizando câmeras...")
        updated = []
        for cam in cameras:
            update_params = {}
            if new_threshold is not None:
                update_params["motion_threshold"] = new_threshold
            if new_sensitivity is not None:
                update_params["motion_sensitivity"] = new_sensitivity

            updated_cam = await repo.update(cam.id, **update_params)
            if updated_cam:
                updated.append(cam.name)

        print(f"✅ Atualizadas {len(updated)} câmeras:")
        for name in updated:
            print(f"   - {name}")

        # Update running grabbers (hot-reload)
        print("\n🔄 Atualizando câmeras em execução...")
        grabbers_updated = 0
        for cam in cameras:
            success = await camera_manager.update_camera_config(cam.id)
            if success:
                grabbers_updated = grabbers_updated + 1
                print(f"   ✅ {cam.name}: configuração atualizada (em execução)")
            else:
                print(f"   ⚠️  {cam.name}: grabber não encontrado ou parado")

        print(f"\n🎯 Resumo:")
        print(f"   Banco de dados: {len(updated)} câmeras atualizadas")
        print(f"   Em execução: {grabbers_updated} câmeras atualizadas")
        if new_sensitivity:
            print(f"   Nova sensitivity: {new_sensitivity}")
        if new_threshold:
            print(f"   Novo threshold: {new_threshold}%")

        print(f"\n📊 Resultados Esperados:")
        if new_sensitivity == "high":
            print("   - Carros passando: motion_score >= 25% (detectado)")
            print("   - Pessoas andando: motion_score >= 15% (detectado)")
            print("   - Cena estática: motion_score < 5% (filtrado)")
        elif new_sensitivity == "medium":
            print("   - Carros passando: motion_score >= 20% (detectado)")
            print("   - Pessoas andando: motion_score >= 15% (detectado)")
            print("   - Cena estática: motion_score < 5% (filtrado)")
        elif new_sensitivity == "low":
            print("   - Apenas movimentos muito evidentes serão detectados")
            print("   - Pode perder carros distantes ou movimentos sutis")

        print(f"\n📋 Dica: Teste por alguns minutos e ajuste novamente se necessário.")
        print(f"   - Se muitos falsos positivos: use LOW sensitivity")
        print(f"   - Se não detecta carros/pessoas: use HIGH sensitivity")
        print(f"   - Para balanceado: use MEDIUM sensitivity (recomendado)")
        print(
            f"\n✅ As alterações entrarão em vigor imediatamente (sem reiniciar aplicação!)"
        )


if __name__ == "__main__":
    asyncio.run(main())
