# Diagnóstico: Motion Score = 0.0

## Situação Reportada

- **Threshold**: 1.0% (muito sensível)
- **Frame interval**: 1 segundo
- **Motion score**: Sempre 0.0
- **Resultado**: TODOS os frames são enviados (nenhum filtrado)

## Causas Possíveis

### 1. Threshold Muito Sensível (1.0%)
Com threshold=1.0%, o sistema exige MUÍTO pouca mudança para não considerar como movimento.
- Em cenas com pequenas variações (iluminação, ruído do sensor), o score pode ficar abaixo de 1.0%
- Isso faz o score parecer 0.0 mesmo com movimento
- **Recomendação**: Aumente threshold para pelo menos 3.0% ou 5.0%

### 2. Problema nos Cálculos de Detecção

O método `detect_motion` combina dois scores:
```python
motion_score = (
    pixel_diff_score * 0.5 +
    bg_sub_score * 0.5
)
```

#### A. `_calculate_pixel_difference`
- Se threshold=1.0% e o movimento for pequeno (<10% de mudança), retorna ~0-15%
- Com threshold de 15 no `cv2.threshold`, pixels com pouca mudança são considerados estáticos
- **Problema**: Pode estar subestimando o movimento real

#### B. `_calculate_background_subtraction`
- Usa `createBackgroundSubtractorMOG2` com `history=200, varThreshold=16`
- Aplica `fg_percentage * 3` no retorno
- **Problema**: Se a câmera for muito estática, background subtraction pode não detectar nada
- Resulta em score ~0.0%

### 3. Problema com `cv2.absdiff`

```python
diff = cv2.absdiff(self._previous_frame, frame)

_, thresh = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)
```

**O threshold de 15** pode estar muito alto para o seu caso:
- Se `diff` tiver valores muito baixos (ruído, pequenas variações), o threshold de 15 faz todos serem 0
- Isso resulta em `changed_pixels = 0` → `diff_percentage = 0.0%`

## Soluções Sugeridas

### Solução Imediata: Aumentar Threshold

Use o `adjust_threshold.py` para aumentar o threshold:

```bash
python adjust_threshold.py
# Escolha opção 3 (Normal - 5.0%) ou 4 (Conservador - 10.0%)
```

**Por que 5.0% ou 10.0% funcionam melhor:**
- Mais tolerante a variações normais
- Apenas detecta movimentos significativos
- Reduz false positives de ruído/iluminação

### Solução II: Ajustar Threshold no MotionDetector

Os thresholds internos do OpenCV podem estar muito agressivos para seu caso:

#### 1. Pixel Difference (linha 30)
```python
# ATUAL: (muito alto)
_, thresh = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)

# SUUGESTÃO: Mais sensível
_, thresh = cv2.threshold(diff, 5, 255, cv2.THRESH_BINARY)
```

#### 2. Background Subtraction (linhas 29-30)
```python
# ATUAL
self._background_subtractor = cv2.createBackgroundSubtractorMOG2(
    history=200, varThreshold=16, detectShadows=True
)

# SUUGESTÃO: Mais sensível
self._background_subtractor = cv2.createBackgroundSubtractorMOG2(
    history=200, varThreshold=8, detectShadows=True
)
```

### Solução III: Debug em Tempo Real

Adicione logs mais detalhados para entender os scores:

**Em `motion_detector._calculate_pixel_difference`:**
```python
logger.debug(
    f"Pixel diff: changed={changed_pixels}/{total_pixels}="
    f"({diff_percentage:.2f}%) -> score={min(diff_percentage*10, 100.0):.2f}%"
)
```

**Em `motion_detector._calculate_background_subtraction`:**
```python
logger.debug(
    f"BG sub: fg={foreground_pixels}/{total_pixels}="
    f"({fg_percentage:.2f}%) -> score={min(fg_percentage*3, 100.0):.2f}%"
)
```

### Solução IV: Ajustar Pesos do Algoritmo Híbrido

O algoritmo usa pesos iguais (0.5 cada):
```python
PIXEL_DIFF_WEIGHT = 0.5
BACKGROUND_SUB_WEIGHT = 0.5
```

Se **background subtraction** não estiver funcionando bem, você pode:
```python
PIXEL_DIFF_WEIGHT = 0.7  # Mais peso para pixel diff
BACKGROUND_SUB_WEIGHT = 0.3  # Menos peso para BG sub
```

## Teste Recomendado

### Passo 1: Teste com Cenário Controlado

1. **Fique parado** em frente da câmera por 10 segundos
2. **Execute** `adjust_threshold.py` e escolha threshold=5.0%
3. **Levante-se** e caminhe pela área de visão
4. **Verifique** nos logs:
   - Deve detectar movimento (motion_score >= 5.0%)
   - Deve mostrar "MOTION DETECTED"
5. **Repita** com threshold=10.0% e veja a diferença

### Passo 2: Teste com Threshold Progressivo

```bash
# Teste 1.0%
python adjust_threshold.py
# Escolha opção 1 (MUITO sensível)

# Teste 3.0% (RECOMENDADO)
python adjust_threshold.py
# Escolha opção 3 (Normal)

# Teste 5.0% (PADRÃO)
python adjust_threshold.py
# Escolha opção 4 (Conservador)
```

## Checklist de Diagnóstico

- [ ] Verifique se a câmera está capturando frames corretos
- [ ] Verifique se há iluminação adequada na cena
- [ ] Teste com diferentes thresholds (1.0%, 3.0%, 5.0%, 10.0%)
- [ ] Adicione logs de debug para entender os scores
- [ ] Verifique se o background subtraction está funcionando
- [ ] Compare logs de pixel_diff vs background_subtraction

## Conclusão

O problema **NÃO** é necessariamente um bug de código, mas uma **configuração inadequada** para o seu ambiente de teste:

1. **Threshold de 1.0%** é extremamente sensível para testes com movimento real
2. **Frame interval de 1 segundo** gera muitas capturas, aumentando carga de processamento
3. **Thresholds internos do OpenCV** podem estar muito altos para sua cena

**Ação Imediata:**
```bash
# Ajuste para um threshold mais razoável
python adjust_threshold.py
# Escolha opção 3 (5.0%) ou 4 (10.0%)
```
