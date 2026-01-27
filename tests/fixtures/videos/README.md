# Motion Detection Test Videos

Este diretório contém vídeos de teste para validar a detecção de movimento.

## Estrutura

```
videos/
├── README.md (este arquivo)
├── ground_truth.json (anotações dos eventos esperados)
├── vehicle_lateral_01.mp4 (veículo passando - vista lateral)
├── vehicle_frontal_01.mp4 (veículo aproximando - vista frontal)
├── person_walking_01.mp4 (pessoa caminhando)
├── static_outdoor_01.mp4 (cena externa estática)
└── false_positives_01.mp4 (árvores balançando, chuva, etc.)
```

## Ground Truth Format

O arquivo `ground_truth.json` contém as anotações dos eventos esperados em cada vídeo:

```json
{
  "vehicle_lateral_01.mp4": {
    "duration_seconds": 10,
    "fps": 30,
    "motion_events": [
      {
        "start_frame": 30,
        "end_frame": 120,
        "type": "vehicle",
        "description": "Carro passando da esquerda para direita"
      }
    ],
    "expected_detection_rate": 0.90,
    "expected_avg_score": 25.0
  }
}
```

## Como Adicionar Vídeos de Teste

1. Grave ou obtenha vídeos curtos (5-15 segundos) de cenários específicos
2. Salve neste diretório com nomes descritivos
3. Anote os eventos esperados no `ground_truth.json`
4. Execute o teste: `pytest tests/test_motion_benchmark.py`

## Sensitivities Esperadas

### LOW Sensitivity
- vehicle_lateral: 70-80% detection rate
- vehicle_frontal: 60-70% detection rate
- person_walking: 60-75% detection rate
- static_outdoor: < 5% false positive rate

### MEDIUM Sensitivity (Recomendado)
- vehicle_lateral: 85-95% detection rate
- vehicle_frontal: 75-85% detection rate
- person_walking: 80-90% detection rate
- static_outdoor: < 10% false positive rate

### HIGH Sensitivity
- vehicle_lateral: 95-100% detection rate
- vehicle_frontal: 90-95% detection rate
- person_walking: 90-95% detection rate
- static_outdoor: < 15% false positive rate (trade-off)

## Obtendo Vídeos de Teste

Você pode:
1. Gravar seus próprios vídeos com a câmera do sistema
2. Usar vídeos de domínio público (ex: Pexels, Pixabay)
3. Usar o script `tools/record_test_video.py` para gravar direto da câmera

## Notas

- Vídeos não são incluídos no repositório por questões de tamanho
- Cada desenvolvedor deve adicionar seus próprios vídeos localmente
- `.gitignore` está configurado para ignorar arquivos `.mp4` e `.avi`
