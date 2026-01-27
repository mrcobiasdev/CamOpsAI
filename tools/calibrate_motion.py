"""Ferramenta interativa para calibrar detecção de movimento.

Permite ajustar parâmetros em tempo real visualizando o resultado.

Uso:
    python tools/calibrate_motion.py --camera <camera-id>
    python tools/calibrate_motion.py --rtsp <rtsp-url>
"""

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.capture.motion_detector import MotionDetector, SENSITIVITY_PRESETS
from src.storage.database import AsyncSessionLocal
from src.storage.repository import CameraRepository
from src.main import camera_manager


class MotionCalibrator:
    """Calibrador interativo de detecção de movimento."""

    def __init__(self, rtsp_url: str, camera_id: uuid.UUID = None):
        """Inicializa calibrador.

        Args:
            rtsp_url: URL RTSP da câmera
            camera_id: ID da câmera no banco (opcional, para salvar)
        """
        self.rtsp_url = rtsp_url
        self.camera_id = camera_id
        self.cap = None
        self.detector = None
        self.running = False

        # Parâmetros ajustáveis
        self.threshold = 10.0
        self.sensitivity = "medium"
        self.show_masks = True
        self.show_pixel_diff = True
        self.show_bg_sub = True

    async def start(self):
        """Inicia captura e calibração."""
        # Abrir stream
        self.cap = cv2.VideoCapture(self.rtsp_url)
        if not self.cap.isOpened():
            raise ValueError(f"Não foi possível abrir o stream: {self.rtsp_url}")

        # Criar detector com sensitivity atual
        self.detector = MotionDetector.from_sensitivity(
            self.sensitivity, self.threshold
        )

        # Criar janela
        cv2.namedWindow("Motion Calibration", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Motion Calibration", 1280, 720)

        # Criar trackbars
        cv2.createTrackbar(
            "Threshold",
            "Motion Calibration",
            int(self.threshold),
            100,
            self._on_threshold_change,
        )

        print("\n" + "=" * 70)
        print("🎛️  MOTION DETECTION CALIBRATOR")
        print("=" * 70)
        print("\nControles:")
        print("  [1/2/3] - Mudar sensitivity (Low/Medium/High)")
        print("  [m]     - Toggle máscaras de movimento")
        print("  [p]     - Toggle pixel difference mask")
        print("  [b]     - Toggle background subtraction mask")
        print("  [s]     - Salvar configuração no banco")
        print("  [r]     - Resetar detector")
        print("  [q/ESC] - Sair")
        print("\nParâmetros atuais:")
        self._print_params()
        print("=" * 70 + "\n")

        self.running = True
        await self._run()

    def _on_threshold_change(self, value):
        """Callback para mudança de threshold."""
        self.threshold = float(value)
        if self.detector:
            self.detector.update_threshold(self.threshold)

    def _print_params(self):
        """Imprime parâmetros atuais."""
        params = SENSITIVITY_PRESETS[self.sensitivity]
        print(f"  Sensitivity: {self.sensitivity.upper()}")
        print(f"  Threshold: {self.threshold}%")
        print(f"  Blur kernel: {params['blur_kernel']}")
        print(f"  Pixel threshold: {params['pixel_threshold']}")
        print(f"  Pixel scale: {params['pixel_scale']}")
        print(f"  BG var threshold: {params['bg_var_threshold']}")
        print(f"  BG history: {params['bg_history']}")

    def _update_sensitivity(self, new_sensitivity: str):
        """Atualiza sensitivity e recria detector."""
        self.sensitivity = new_sensitivity
        self.detector = MotionDetector.from_sensitivity(
            self.sensitivity, self.threshold
        )
        print(f"\n✅ Sensitivity alterada para: {self.sensitivity.upper()}")
        self._print_params()

    async def _run(self):
        """Loop principal de calibração."""
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("⚠️  Falha ao capturar frame, tentando reconectar...")
                self.cap.release()
                self.cap = cv2.VideoCapture(self.rtsp_url)
                continue

            # Detectar movimento
            motion_score, has_motion = self.detector.detect_motion(frame)

            # Criar visualização
            viz_frame = self._create_visualization(frame, motion_score, has_motion)

            # Mostrar
            cv2.imshow("Motion Calibration", viz_frame)

            # Processar teclas
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:  # q ou ESC
                break
            elif key == ord("1"):
                self._update_sensitivity("low")
            elif key == ord("2"):
                self._update_sensitivity("medium")
            elif key == ord("3"):
                self._update_sensitivity("high")
            elif key == ord("m"):
                self.show_masks = not self.show_masks
                print(f"Máscaras: {'ON' if self.show_masks else 'OFF'}")
            elif key == ord("p"):
                self.show_pixel_diff = not self.show_pixel_diff
                print(f"Pixel diff: {'ON' if self.show_pixel_diff else 'OFF'}")
            elif key == ord("b"):
                self.show_bg_sub = not self.show_bg_sub
                print(f"BG subtraction: {'ON' if self.show_bg_sub else 'OFF'}")
            elif key == ord("r"):
                self.detector.reset()
                print("🔄 Detector resetado")
            elif key == ord("s"):
                await self._save_config()

        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()

    def _create_visualization(
        self, frame: np.ndarray, motion_score: float, has_motion: bool
    ) -> np.ndarray:
        """Cria frame de visualização com informações e máscaras.

        Args:
            frame: Frame original
            motion_score: Score de movimento
            has_motion: Se houve detecção

        Returns:
            Frame com visualização
        """
        viz = frame.copy()
        height, width = viz.shape[:2]

        # Status e score
        status_text = "✅ MOTION DETECTED" if has_motion else "⏸️  NO MOTION"
        status_color = (0, 255, 0) if has_motion else (0, 0, 255)

        cv2.rectangle(viz, (0, 0), (width, 180), (0, 0, 0), -1)  # Fundo escuro

        cv2.putText(
            viz,
            f"Motion Score: {motion_score:.1f}%",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            viz,
            status_text,
            (10, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            status_color,
            2,
        )
        cv2.putText(
            viz,
            f"Threshold: {self.threshold}% | Sensitivity: {self.sensitivity.upper()}",
            (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
        )
        cv2.putText(
            viz,
            f"Masks: {'ON' if self.show_masks else 'OFF'} | Pixel Diff: {'ON' if self.show_pixel_diff else 'OFF'} | BG Sub: {'ON' if self.show_bg_sub else 'OFF'}",
            (10, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
        )
        cv2.putText(
            viz,
            "Press [1/2/3] for sensitivity, [m/p/b] for masks, [s] to save, [q] to quit",
            (10, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (150, 150, 150),
            1,
        )

        # Adicionar máscaras se habilitado
        if self.show_masks and self.detector._previous_frame is not None:
            # Preprocessar frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (320, 240), interpolation=cv2.INTER_AREA)
            blurred = cv2.GaussianBlur(resized, self.detector.blur_kernel, 0)

            # Pixel difference
            if self.show_pixel_diff:
                diff = cv2.absdiff(self.detector._previous_frame, blurred)
                _, thresh = cv2.threshold(
                    diff, self.detector.pixel_threshold, 255, cv2.THRESH_BINARY
                )
                mask_resized = cv2.resize(thresh, (width, height))
                mask_colored = cv2.applyColorMap(mask_resized, cv2.COLORMAP_HOT)
                viz = cv2.addWeighted(viz, 0.7, mask_colored, 0.3, 0)

            # Background subtraction
            if self.show_bg_sub:
                fg_mask = self.detector._background_subtractor.apply(blurred)
                _, fg_thresh = cv2.threshold(fg_mask, 127, 255, cv2.THRESH_BINARY)
                fg_resized = cv2.resize(fg_thresh, (width, height))
                fg_colored = cv2.applyColorMap(fg_resized, cv2.COLORMAP_WINTER)
                viz = cv2.addWeighted(viz, 0.8, fg_colored, 0.2, 0)

        return viz

    async def _save_config(self):
        """Salva configuração calibrada no banco de dados."""
        if not self.camera_id:
            print("❌ Camera ID não fornecido, não é possível salvar")
            return

        try:
            async with AsyncSessionLocal() as session:
                repo = CameraRepository(session)

                # Atualizar câmera
                camera = await repo.update(
                    self.camera_id,
                    motion_threshold=self.threshold,
                    motion_sensitivity=self.sensitivity,
                )

                if camera:
                    print("\n✅ Configuração salva no banco de dados!")
                    print(f"   Threshold: {self.threshold}%")
                    print(f"   Sensitivity: {self.sensitivity}")

                    # Tentar hot-reload se a câmera estiver rodando
                    success = await camera_manager.update_camera_config(self.camera_id)
                    if success:
                        print("   🔄 Hot-reload aplicado com sucesso!")
                    else:
                        print(
                            "   ⚠️  Câmera não está rodando, configuração será aplicada no próximo start"
                        )
                else:
                    print("❌ Falha ao salvar configuração")

        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")


async def main():
    parser = argparse.ArgumentParser(
        description="Calibra detecção de movimento interativamente"
    )
    parser.add_argument("--camera", type=str, help="ID da câmera no banco de dados")
    parser.add_argument("--rtsp", type=str, help="URL RTSP direta")

    args = parser.parse_args()

    if not args.camera and not args.rtsp:
        print("❌ Forneça --camera <id> ou --rtsp <url>")
        return

    rtsp_url = args.rtsp
    camera_id = None

    # Se camera ID fornecido, buscar URL do banco
    if args.camera:
        try:
            camera_id = uuid.UUID(args.camera)
            async with AsyncSessionLocal() as session:
                repo = CameraRepository(session)
                camera = await repo.get_by_id(camera_id)

                if not camera:
                    print(f"❌ Câmera {args.camera} não encontrada")
                    return

                rtsp_url = camera.url
                print(f"📷 Câmera: {camera.name}")
                print(f"   URL: {rtsp_url}")
                print(f"   Sensitivity atual: {camera.motion_sensitivity}")
                print(f"   Threshold atual: {camera.motion_threshold}%\n")

        except ValueError:
            print(f"❌ Camera ID inválido: {args.camera}")
            return

    # Iniciar calibrador
    calibrator = MotionCalibrator(rtsp_url, camera_id)
    await calibrator.start()


if __name__ == "__main__":
    asyncio.run(main())
