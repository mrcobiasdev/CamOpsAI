"""Ferramenta para visualizar detecção de movimento em vídeos.

Processa um vídeo e gera uma visualização com:
- Máscaras de movimento sobrepostas
- Motion score em cada frame
- Histograma de distribuição de scores

Uso:
    python tools/visualize_motion.py --video path/to/video.mp4
    python tools/visualize_motion.py --video path/to/video.mp4 --sensitivity high
    python tools/visualize_motion.py --video path/to/video.mp4 --all-sensitivities
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import matplotlib.pyplot as plt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.capture.motion_detector import MotionDetector, SENSITIVITY_PRESETS


def process_video(
    video_path: str,
    output_path: str,
    sensitivity: str = "medium",
    threshold: float = 10.0,
    show_masks: bool = True,
) -> dict:
    """Processa vídeo e gera visualização com detecção de movimento.

    Args:
        video_path: Caminho para o vídeo de entrada
        output_path: Caminho para o vídeo de saída
        sensitivity: Nível de sensibilidade (low/medium/high)
        threshold: Threshold de detecção (0-100)
        show_masks: Se deve mostrar máscaras de movimento

    Returns:
        Dict com estatísticas: scores, frames_sent, frames_filtered
    """
    # Abrir vídeo
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Não foi possível abrir o vídeo: {video_path}")

    # Propriedades do vídeo
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"📹 Vídeo: {video_path}")
    print(f"   Resolução: {width}x{height}")
    print(f"   FPS: {fps}")
    print(f"   Total de frames: {total_frames}")
    print(f"   Sensitivity: {sensitivity}")
    print(f"   Threshold: {threshold}%\n")

    # Criar detector de movimento
    detector = MotionDetector.from_sensitivity(sensitivity, threshold)

    # Criar writer para vídeo de saída
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Estatísticas
    scores = []
    frames_sent = 0
    frames_filtered = 0
    frame_count = 0

    print("🔄 Processando frames...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Detectar movimento
        motion_score, has_motion = detector.detect_motion(frame)
        scores.append(motion_score)

        if has_motion:
            frames_sent += 1
        else:
            frames_filtered += 1

        # Criar visualização
        viz_frame = frame.copy()

        # Adicionar score e status
        status_text = "✅ MOTION" if has_motion else "⏸️ FILTERED"
        status_color = (0, 255, 0) if has_motion else (0, 0, 255)

        cv2.putText(
            viz_frame,
            f"Score: {motion_score:.1f}%",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            viz_frame,
            status_text,
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            status_color,
            2,
        )
        cv2.putText(
            viz_frame,
            f"Threshold: {threshold}%",
            (10, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            viz_frame,
            f"Sensitivity: {sensitivity}",
            (10, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        # Adicionar máscaras de movimento se solicitado
        if show_masks and detector._previous_frame is not None:
            # Preprocessar frame atual
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (320, 240), interpolation=cv2.INTER_AREA)
            blurred = cv2.GaussianBlur(resized, detector.blur_kernel, 0)

            # Calcular diff
            diff = cv2.absdiff(detector._previous_frame, blurred)
            _, thresh = cv2.threshold(
                diff, detector.pixel_threshold, 255, cv2.THRESH_BINARY
            )

            # Redimensionar para tamanho original
            mask_resized = cv2.resize(thresh, (width, height))
            mask_colored = cv2.applyColorMap(mask_resized, cv2.COLORMAP_HOT)

            # Sobrepor máscara (50% transparência)
            viz_frame = cv2.addWeighted(viz_frame, 0.7, mask_colored, 0.3, 0)

        # Escrever frame
        out.write(viz_frame)

        # Progresso
        if frame_count % 30 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"   Progresso: {progress:.1f}% ({frame_count}/{total_frames})")

    # Limpar
    cap.release()
    out.release()

    print(f"\n✅ Vídeo processado: {output_path}")
    print(f"\n📊 Estatísticas:")
    print(f"   Total de frames: {frame_count}")
    print(
        f"   Frames enviados (motion): {frames_sent} ({frames_sent / frame_count * 100:.1f}%)"
    )
    print(
        f"   Frames filtrados: {frames_filtered} ({frames_filtered / frame_count * 100:.1f}%)"
    )
    print(f"   Score médio: {np.mean(scores):.2f}%")
    print(f"   Score mínimo: {np.min(scores):.2f}%")
    print(f"   Score máximo: {np.max(scores):.2f}%")

    return {
        "scores": scores,
        "frames_sent": frames_sent,
        "frames_filtered": frames_filtered,
        "total_frames": frame_count,
    }


def generate_histogram(stats: dict, output_path: str, sensitivity: str):
    """Gera histograma de distribuição de scores.

    Args:
        stats: Dicionário com estatísticas
        output_path: Caminho para salvar o histograma
        sensitivity: Nível de sensibilidade usado
    """
    scores = stats["scores"]

    plt.figure(figsize=(10, 6))
    plt.hist(scores, bins=50, edgecolor="black", alpha=0.7)
    plt.axvline(10.0, color="r", linestyle="--", linewidth=2, label="Threshold (10%)")
    plt.axvline(
        np.mean(scores),
        color="g",
        linestyle="--",
        linewidth=2,
        label=f"Média ({np.mean(scores):.1f}%)",
    )

    plt.xlabel("Motion Score (%)")
    plt.ylabel("Frequência")
    plt.title(f"Distribuição de Motion Scores - Sensitivity: {sensitivity}")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"📊 Histograma salvo: {output_path}")


def compare_sensitivities(video_path: str, output_dir: str):
    """Compara todas as sensitivities no mesmo vídeo.

    Args:
        video_path: Caminho para o vídeo de entrada
        output_dir: Diretório para salvar resultados
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for sensitivity in ["low", "medium", "high"]:
        print(f"\n{'=' * 60}")
        print(f"Processando com sensitivity: {sensitivity.upper()}")
        print(f"{'=' * 60}\n")

        output_video = output_dir / f"output_{sensitivity}.mp4"
        stats = process_video(video_path, str(output_video), sensitivity=sensitivity)
        results[sensitivity] = stats

        # Gerar histograma
        hist_path = output_dir / f"histogram_{sensitivity}.png"
        generate_histogram(stats, str(hist_path), sensitivity)

    # Gerar comparação
    print(f"\n{'=' * 60}")
    print("COMPARAÇÃO DE SENSITIVITIES")
    print(f"{'=' * 60}\n")

    print(
        f"{'Sensitivity':<12} {'Frames Sent':<15} {'Detection Rate':<15} {'Avg Score':<12}"
    )
    print("-" * 60)

    for sensitivity, stats in results.items():
        detection_rate = stats["frames_sent"] / stats["total_frames"] * 100
        avg_score = np.mean(stats["scores"])
        print(
            f"{sensitivity:<12} {stats['frames_sent']:<15} {detection_rate:<15.1f}% {avg_score:<12.2f}%"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Visualiza detecção de movimento em vídeos"
    )
    parser.add_argument(
        "--video", required=True, help="Caminho para o vídeo de entrada"
    )
    parser.add_argument(
        "--output",
        help="Caminho para o vídeo de saída (padrão: output.mp4)",
        default="output.mp4",
    )
    parser.add_argument(
        "--sensitivity",
        choices=["low", "medium", "high"],
        default="medium",
        help="Nível de sensibilidade (padrão: medium)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Threshold de detecção (padrão: 10.0)",
    )
    parser.add_argument(
        "--no-masks",
        action="store_true",
        help="Não mostrar máscaras de movimento",
    )
    parser.add_argument(
        "--all-sensitivities",
        action="store_true",
        help="Processa com todas as sensitivities e compara",
    )
    parser.add_argument(
        "--output-dir",
        default="motion_analysis",
        help="Diretório para salvar resultados (padrão: motion_analysis)",
    )

    args = parser.parse_args()

    if args.all_sensitivities:
        compare_sensitivities(args.video, args.output_dir)
    else:
        stats = process_video(
            args.video,
            args.output,
            args.sensitivity,
            args.threshold,
            show_masks=not args.no_masks,
        )

        # Gerar histograma
        hist_path = Path(args.output).with_suffix(".png")
        generate_histogram(stats, str(hist_path), args.sensitivity)


if __name__ == "__main__":
    main()
