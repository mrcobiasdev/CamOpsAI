# Motion Detection - Guia Completo

## Visão Geral

O sistema de detecção de movimento do CamOpsAI filtra frames antes do processamento LLM, reduzindo custos de API e melhorando a eficiência. Apenas frames com movimento significativo são enviados para análise.

## Como Funciona

### Algoritmo Híbrido

O detector usa uma abordagem híbrida combinando:

1. **Pixel Difference (50%)**: Compara frames consecutivos pixel a pixel
2. **Background Subtraction (50%)**: Usa MOG2 para modelar o background e detectar foreground

**Motion Score** = (Pixel Diff Score × 0.5) + (BG Sub Score × 0.5)

Se `Motion Score >= Threshold`, o frame é enviado ao LLM.

### Sensitivity Presets

Três níveis de sensibilidade pré-configurados:

| Sensitivity | Uso Recomendado | Detection Rate | False Positives |
|-------------|-----------------|----------------|-----------------|
| **LOW** | Indoor, cenas controladas | 70-80% | Muito baixo |
| **MEDIUM** | Geral, balanceado | 85-95% | Baixo |
| **HIGH** | Outdoor, ruas, monitoramento | 95-100% | Médio |

#### Parâmetros por Sensitivity

```python
LOW:
  blur_kernel: (5, 5)      # Mais blur, menos ruído
  pixel_threshold: 20      # Mais conservador
  pixel_scale: 8           # Menos amplificação
  bg_var_threshold: 20     # Menos sensível
  bg_history: 300          # Menor histórico

MEDIUM (Recomendado):
  blur_kernel: (3, 3)      # Blur balanceado
  pixel_threshold: 10      # Threshold médio
  pixel_scale: 15          # Amplificação média
  bg_var_threshold: 10     # Sensibilidade média
  bg_history: 500          # Histórico adequado

HIGH:
  blur_kernel: (3, 3)      # Mesmo blur que medium
  pixel_threshold: 5       # Muito sensível (metade do medium)
  pixel_scale: 20          # Máxima amplificação
  bg_var_threshold: 8      # Muito sensível
  bg_history: 700          # Maior histórico
```

## Configuração

### Via adjust_threshold.py

A forma mais fácil de configurar:

```bash
python adjust_threshold.py
```

Opções:
1. **HIGH Sensitivity** - Para ruas e outdoor
2. **MEDIUM Sensitivity** - Recomendado, balanceado
3. **LOW Sensitivity** - Indoor, conservador
4. Threshold personalizado
5. Desabilitar motion detection

### Via API

```bash
# Atualizar sensitivity
curl -X PATCH http://localhost:8000/api/cameras/{camera_id} \
  -H "Content-Type: application/json" \
  -d '{"motion_sensitivity": "high", "motion_threshold": 10.0}'
```

### Via Banco de Dados

```sql
UPDATE cameras
SET motion_sensitivity = 'high',
    motion_threshold = 10.0
WHERE id = '<camera-id>';
```

## Ferramentas de Calibração

### 1. Visualização de Vídeo

Processe um vídeo gravado e veja motion scores + máscaras:

```bash
# Processar com sensitivity medium
python tools/visualize_motion.py --video test.mp4

# Processar com sensitivity específica
python tools/visualize_motion.py --video test.mp4 --sensitivity high

# Comparar todas as sensitivities
python tools/visualize_motion.py --video test.mp4 --all-sensitivities
```

**Saída**:
- `output.mp4`: Vídeo com motion score e máscaras sobrepostas
- `output.png`: Histograma de distribuição de scores

### 2. Calibração em Tempo Real

Calibre ajustando parâmetros ao vivo:

```bash
# Com câmera do banco
python tools/calibrate_motion.py --camera <camera-id>

# Com URL RTSP direta
python tools/calibrate_motion.py --rtsp rtsp://192.168.1.100/stream
```

**Controles**:
- `[1/2/3]` - Mudar sensitivity (Low/Medium/High)
- `[m]` - Toggle máscaras de movimento
- `[p]` - Toggle pixel difference mask
- `[b]` - Toggle background subtraction mask
- `[s]` - Salvar configuração no banco
- `[r]` - Resetar detector
- `[q/ESC]` - Sair

### 3. Debug Mode

Ative debug mode para salvar frames e logs detalhados:

```python
detector = MotionDetector.from_sensitivity(
    "medium",
    threshold=10.0,
    debug=True,
    debug_dir="/tmp/motion_debug"
)
```

**Debug salva**:
- `01_preprocessed.png`: Frame após preprocessing
- `02_pixel_diff.png`: Diferença de pixels
- `03_pixel_thresh.png`: Threshold binário da diferença
- `04_bg_sub_raw.png`: Máscara do background subtractor
- `05_bg_sub_thresh.png`: Threshold binário da máscara

Logs incluem todos os parâmetros e scores individuais.

## Troubleshooting

### Problema: Carros/pessoas não são detectados

**Sintomas**: Motion scores muito baixos (0-5%) quando há movimento real.

**Soluções**:
1. Aumentar sensitivity para HIGH:
   ```bash
   python adjust_threshold.py
   # Escolha opção 1 (HIGH Sensitivity)
   ```

2. Reduzir threshold:
   ```bash
   python adjust_threshold.py
   # Escolha opção 4 e digite 5.0 ou menos
   ```

3. Usar ferramenta de visualização para diagnosticar:
   ```bash
   python tools/visualize_motion.py --video gravacao_problema.mp4
   ```

4. Calibrar ao vivo:
   ```bash
   python tools/calibrate_motion.py --camera <camera-id>
   ```

### Problema: Muitos falsos positivos

**Sintomas**: Frames estáticos sendo detectados como movimento (árvores, chuva, luz).

**Soluções**:
1. Diminuir sensitivity para LOW:
   ```bash
   python adjust_threshold.py
   # Escolha opção 3 (LOW Sensitivity)
   ```

2. Aumentar threshold:
   ```bash
   python adjust_threshold.py
   # Escolha opção 4 e digite 15.0 ou mais
   ```

### Problema: Performance lenta

**Sintomas**: Processamento de frames > 50ms.

**Diagnóstico**:
```python
pytest tests/test_motion_benchmark.py::test_performance_benchmark -v
```

**Soluções**:
- Verifique resolução da câmera (> 1920x1080 pode ser lento)
- Monitore CPU usage
- Considere GPU acceleration (futuro)

## Scores Esperados

### Com MEDIUM Sensitivity

| Cenário | Expected Score | Status |
|---------|---------------|--------|
| Cena estática | 0-5% | ⏸️ Filtrado |
| Árvores balançando | 5-10% | ⏸️ Filtrado |
| Pessoa caminhando | 15-30% | ✅ Detectado |
| Veículo passando (lateral) | 20-50% | ✅ Detectado |
| Veículo passando (frontal) | 10-25% | ✅ Detectado |
| Mudança de luz brusca | 5-15% | ⏸️/✅ Depende |

### Ajuste Baseado em Scores

Se você vê nos logs:

```
Motion detection: score=3.5%, threshold=10.0%, has_motion=False
```

Mas esperava detecção → **Aumentar sensitivity ou diminuir threshold**

```
Motion detection: score=25.0%, threshold=10.0%, has_motion=True
```

Detecção OK → **Configuração adequada**

## Testes Automatizados

### Executar Testes de Motion Detection

```bash
# Todos os testes
pytest tests/test_motion_detection.py -v

# Testes de sensitivity melhorada
pytest tests/test_motion_detection.py::test_improved_sensitivity -v

# Benchmark com vídeos reais (requer vídeos em tests/fixtures/videos/)
pytest tests/test_motion_benchmark.py -v -m benchmark
```

### Adicionar Vídeos de Teste

1. Grave vídeos curtos (5-15s) de cenários específicos
2. Salve em `tests/fixtures/videos/`
3. Anote eventos esperados em `tests/fixtures/videos/ground_truth.json`
4. Execute testes

Veja `tests/fixtures/videos/README.md` para detalhes.

## API Reference

### MotionDetector

```python
from src.capture.motion_detector import MotionDetector

# Criar com sensitivity preset
detector = MotionDetector.from_sensitivity("medium", threshold=10.0)

# Criar com parâmetros customizados
detector = MotionDetector(
    threshold=10.0,
    blur_kernel=(2, 2),
    pixel_threshold=10,
    pixel_scale=15.0,
    bg_var_threshold=10,
    bg_history=500,
    debug=False
)

# Detectar movimento
motion_score, has_motion = detector.detect_motion(frame)

# Atualizar threshold
detector.update_threshold(5.0)

# Resetar estado
detector.reset()
```

### Sensitivity Presets

```python
from src.capture.motion_detector import SENSITIVITY_PRESETS

# Ver parâmetros
params = SENSITIVITY_PRESETS["medium"]
print(params)
# {
#   "blur_kernel": (2, 2),
#   "pixel_threshold": 10,
#   "pixel_scale": 15.0,
#   "bg_var_threshold": 10,
#   "bg_history": 500
# }
```

## Best Practices

1. **Sempre teste primeiro**: Use `visualize_motion.py` ou `calibrate_motion.py` antes de aplicar em produção

2. **Start com MEDIUM**: É balanceado para maioria dos casos

3. **Monitore logs**: Observe motion scores nos primeiros dias

4. **Ajuste incremental**: Mude de MEDIUM → HIGH se precisar, não pule direto

5. **Outdoor usa HIGH**: Ruas, estacionamentos, áreas abertas se beneficiam de HIGH sensitivity

6. **Indoor usa LOW/MEDIUM**: Ambientes controlados raramente precisam de HIGH

7. **Hot-reload funciona**: Não precisa reiniciar a aplicação após mudanças

8. **Debug quando necessário**: Se comportamento estranho, ative debug mode

## Histórico de Melhorias

### v2 (atual) - Improved Sensitivity
- Reduzido blur: (3,3) → (2,2)
- Reduzido pixel threshold: 15 → 10
- Aumentado pixel scale: 10 → 15
- Ajustado MOG2: varThreshold 16 → 10, history 200 → 500
- **Resultado**: Detecção de veículos laterais: 0-3% → 20-50%

### v1 (original)
- Blur (3,3), threshold 15, scale 10
- Problemas com detecção outdoor
- Muitos falsos negativos em ruas

## Suporte

Problemas? Abra uma issue com:
- Logs de motion detection
- Vídeo ou screenshot do cenário
- Sensitivity e threshold usados
- Output de `visualize_motion.py` se possível
