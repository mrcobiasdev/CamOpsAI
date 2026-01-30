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
python tools/update_sensitivity.py <camera-id> high
```

Ou use o script interativo:

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
curl -X PATCH http://localhost:8000/api/v1/cameras/{camera_id} \
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

# Ativar debug mode (salva frames intermediários)
python tools/visualize_motion.py --video test.mp4 --debug
```

**Output:**
- `test_video_frames/` - Frames capturados
- `test_video_motion/` - Máscaras de movimento
- `test_video_annotated/` - Frames anotados com score

### 2. Calibração em Tempo Real

Ajuste sensitivity enquanto observa a câmera em tempo real:

```bash
# Calibrar câmera específica
python tools/calibrate_motion.py --camera <camera-id>

# Especificar sensitivity inicial
python tools/calibrate_motion.py --camera <camera-id> --sensitivity high
```

**Funcionalidades:**
- Ajuste sensitivity presets (LOW/MEDIUM/HIGH)
- Ajuste threshold manual
- Preview do motion score em tempo real
- Histórico de scores (últimos 30 segundos)

### 3. Verificação de Configuração

Verifique todas as câmeras e suas configurações:

```bash
python tools/check_cameras.py
```

**Output:**
```
Camera: Entrada Principal
  ID: d3002080-1234-5678-9abc-123456789012
  Sensitivity: HIGH
  Threshold: 10.0%
  Motion Detection: Enabled
  Status: Capturing

Camera: Garagem
  ID: e4003190-2345-6789-abcd-234567890123
  Sensitivity: MEDIUM
  Threshold: 5.0%
  Motion Detection: Enabled
  Status: Stopped
```

## Hot-Reload de Configuração

O sistema suporta atualização de configuração em tempo real sem reiniciar a aplicação.

### Como Funciona

```python
# 1. Atualiza banco de dados
repo.update(camera_id, motion_threshold=10.0)

# 2. Atualiza grabber em execução
camera_manager.update_camera_config(camera_id)

# 3. Reinicializa MotionDetector com novo threshold
grabber.update_config(new_config)
```

### Ajuste Imediato

```bash
# Execute o script de ajuste
python adjust_threshold.py

# Selecione nova sensitivity/threshold

# As mudanças entram em vigor IMEDIATAMENTE!
# Não precisa reiniciar a aplicação.
```

### Logs Esperados

```
Configuration updated: camera=d3002080..., field=motion_threshold, old=5.0, new=10.0
Motion detector reinitialized with new threshold: 10.0%
Motion detection: score=18.50%, threshold=10.00%, has_motion=True
```

## Solução de Problemas

### Problema: Motion Score Sempre 0.0

**Causas Possíveis:**

1. **Threshold muito sensível (1.0%)** - Cenas com pouca variação resultam em scores < 1.0%
2. **Thresholds internos do OpenCV muito altos** - `cv2.threshold` com valor 15+ filtra tudo
3. **Câmera estática** - Background subtraction não detecta foreground

**Soluções:**

```bash
# Aumente threshold para pelo menos 3.0% ou 5.0%
python adjust_threshold.py
# Escolha opção 3 (5.0%) ou 4 (10.0%)
```

### Problema: Carros/Pessoas Não Detectados

**Causa:** Threshold muito conservador para cena outdoor

**Solução:**

```bash
# Use sensitivity HIGH para ruas
python tools/update_sensitivity.py <camera-id> high

# Ou ajuste threshold manual
python adjust_threshold.py
# Escolha opção 2 (3.0%) ou 1 (1.0%)
```

**Resultado esperado:**
- Detecta 25-50% de veículos passando com HIGH sensitivity
- Detecta 5-15% com MEDIUM sensitivity
- Detecta 0-3% com LOW sensitivity

### Problema: Muitos Falsos Positivos

**Causas:**
- Árvores movendo ao vento
- Luzes piscando
- Threshold muito baixo

**Soluções:**

```bash
# Aumente threshold
python adjust_threshold.py
# Escolha opção 4 (10.0%)

# Ou use sensitivity LOW
python tools/update_sensitivity.py <camera-id> low
```

## Diagnóstico Avançado

### Debug em Tempo Real

Adicione logs detalhados para entender os scores:

```bash
# Em adjust_threshold.py, escolha uma opção
# Observe os logs por 5-10 minutos
```

**Logs esperados:**

```
✅ MOTION DETECTED - motion_score=18.50%, threshold=3.00%
Motion detection: score=18.50%, pixel_diff=15.30%, bg_sub=20.70%
```

### Comparação de Thresholds

| Threshold | Pessoa Rápida | Carro | Pessoa Parada | Câmera Parada |
|-----------|---------------|--------|---------------|----------------|
| 1.0% | ✅ Detecta | ✅ Detecta | ✅ Detecta | ✅ Detecta |
| 3.0% | ✅ Detecta | ✅ Detecta | ⚠️ Depende | ✅ Detecta |
| 5.0% | ✅ Detecta | ✅ Detecta | ❌ Não | ✅ Detecta |
| 10.0% | ❌ Não | ❌ Não | ❌ Não | ✅ Detecta |

## Histórico de Melhorias

### Melhorias Implementadas

1. **Sensitivity Presets (2026-01-22)**
   - LOW/MEDIUM/HIGH presets otimizados
   - Campo `motion_sensitivity` no banco de dados
   - Hot-reload de configuração

2. **Hot-Reload de Threshold (2026-01-22)**
   - Método `update_config()` em FrameGrabber
   - Método `update_camera_config()` em CameraManager
   - Atualização em tempo real sem reiniciar

3. **Algoritmo Otimizado (2026-01-22)**
   - GaussianBlur kernel: (5,5)/(3,3) (ímpares)
   - Pixel threshold reduzido: 15 → 10 (MEDIUM), 5 (HIGH)
   - Pixel scale aumentado: 10 → 15 (MEDIUM), 20 (HIGH)
   - MOG2 parameters otimizados

4. **Bug Fix: SQLAlchemy flush vs commit (2026-01-22)**
   - Corrigidos todos os 9 casos de `flush()` → `commit()`
   - Agora as mudanças são persistidas corretamente

### Documentos Consolidados

Este documento consolida informações de:
- `docs/MOTION_DETECTION.md` - Guia original de motion detection
- `docs/MOTION_DETECTION_FIX.md` - Ajuste de sensibilidade
- `docs/DIAGNOSTICO_MOTION_SCORE_ZERO.md` - Diagnóstico de score zero
- `docs/IMPLEMENTACAO_THRESHOLD_HOT_RELOAD.md` - Hot-reload de configuração

## Referências

- **API Endpoints:** `/api/v1/cameras/{id}` - Atualizar configuração
- **Database Schema:** `cameras` table - `motion_detection_enabled`, `motion_threshold`, `motion_sensitivity`
- **Source Code:** `src/capture/motion_detector.py` - Implementação do detector
