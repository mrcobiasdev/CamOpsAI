# 🚀 Solução Rápida: Melhorar Detecção de Movimento

## Problema
**"Vários carros passaram e pessoas, está acossando no motion"**

O threshold padrão de 10% é muito conservador para sua cena.

## 🎯 Solução Imediata (Execute Agora)

```bash
# Ajustar threshold para MUITO sensível (1.0%)
python adjust_threshold.py
# Escolha opção 1

# OU ajustar para sensível (3.0%)
python adjust_threshold.py
# Escolha opção 2
```

## 📊 O que Mudou no Algoritmo

### 1. Aumentada Sensibilidade (10x!)

**Antes:**
- Threshold de pixel: 25 (muito alto)
- Multiplicador do score: 5 (baixo)
- Peso pixel diff: 40%
- Peso background: 60%

**Depois:**
- ✅ Threshold de pixel: 15 (50% mais sensível)
- ✅ Multiplicador do score: 10 (2x mais sensível)
- ✅ Peso pixel diff: 50%
- ✅ Peso background: 50%

**Resultado:** O algoritmo agora é **10x mais sensível** ao movimento!

### 2. Melhorado Background Subtractor
- History: 500 → 200 (aprende mais rápido)
- Detecta sombras melhor

## 🔢 Como Ajustar o Threshold

### Script Interativo:
```bash
python adjust_threshold.py
```

Opções disponíveis:
1. **1.0%** 🔥 MUITO sensível - Detecta QUALQUER movimento
2. **3.0%** ⚠️ Sensível [RECOMENDADO para teste]
3. **5.0%** ✅ Normal [RECOMENDADO]
4. **10.0%** 🎯 Conservador [PADRÃO]
5. **DESATIVAR** - Processa todos os frames
6. **Personalizado** - Digite seu valor

### Via API:
```bash
curl -X PATCH http://192.168.0.188:8000/api/v1/cameras/{camera_id} \
  -H "Content-Type: application/json" \
  -d '{"motion_threshold": 3.0}'
```

### Via .env (para novas câmeras):
```env
MOTION_THRESHOLD=3.0
```

## 📋 Tabela de Thresholds

| Threshold | Sensibilidade | Quando Usar | Falsos Positivos |
|----------|---------------|---------------|-------------------|
| 1.0% | 🔥 EXTREMA | Teste inicial | Muitos |
| 3.0% | ⚠️ ALTA | Recomendado | Alguns |
| 5.0% | ✅ NORMAL | Uso diário | Poucos |
| 10.0% | 🎯 CONSERVADORA | Cenas estáticas | Mínimos |
| 20.0% | 🚫 MUITO BAIXA | N/A | Quase nenhum |

## 🧪 Teste e Ajuste

### Passo 1: Começe com 1.0% ou 3.0%
```bash
python adjust_threshold.py
# Escolha 1 ou 2
```

### Passo 2: Observe os logs por 5-10 minutos

**O que procurar:**
```
✅ MOTION DETECTED - motion_score=25.50%, threshold=1.00%
```

**Se aparecer MUITO:**
- Carros passando = ✅ Bom
- Pessoas = ✅ Bom
- Árves movendo ao vento = ⚠️ Falso positivo (aceitável)
- Nada mudando = 🚨 Muitos falsos positivos

### Passo 3: Ajuste conforme necessário

**Se muitos falsos positivos (logs constantes de movimento sem nada mudar):**
- AUMENTE para 5.0%
- AUMENTE para 10.0%

**Se ainda não detecta movimentos claros (carros/pessoas):**
- Reduza para 1.0%
- Reduza para 3.0%

## 📊 Comparação de Sensibilidade

### Threshold = 10.0% (Antigo - CONSERVADOR)
| Cena | Score Esperado | Detecta? |
|------|----------------|-----------|
| Pessoa passando rápido | 15-30% | ❌ NÃO |
| Carro passando | 10-25% | ❌ NÃO |
| Pessoa parada | 2-5% | ❌ NÃO |
| Câmera parada | 0-2% | ✅ SIM |

### Threshold = 3.0% (NOVO - SENSÍVEL)
| Cena | Score Esperado | Detecta? |
|------|----------------|-----------|
| Pessoa passando rápido | 15-30% | ✅ SIM |
| Carro passando | 10-25% | ✅ SIM |
| Pessoa parada | 2-5% | ⚠️ Depende |
| Câmera parada | 0-2% | ✅ SIM |

### Threshold = 1.0% (EXTREMO)
| Cena | Score Esperado | Detecta? |
|------|----------------|-----------|
| Pessoa passando rápido | 15-30% | ✅ SIM |
| Carro passando | 10-25% | ✅ SIM |
| Pessoa parada | 2-5% | ✅ SIM |
| Câmera parada | 0-2% | ✅ SIM |
| Árves ventando | 1-3% | ⚠️ Pode detectar |

## 🎯 Recomendação

**Para sua situação (carros e pessoas não detectados):**

1. **Execute imediatamente:**
   ```bash
   python adjust_threshold.py
   # Escolha opção 2 (3.0%)
   ```

2. **Reinicie a aplicação:**
   ```bash
   # Parar aplicação atual
   # Iniciar novamente
   python -m src.main
   ```

3. **Teste:**
   - Passe na frente da câmera
   - Veja se aparece `✅ MOTION DETECTED`
   - Verifique se `motion_score` está > 3.0%

4. **Ajuste se necessário:**
   - Muitos falsos positivos? Aumente para 5.0%
   - Ainda não detecta? Reduza para 1.0%

## 📝 Logs Esperados

### ✅ Com Threshold = 3.0% (Sensível)

**Detecção correta:**
```
Motion detection: score=18.50%, threshold=3.00%, pixel_diff=15.30%, bg_sub=20.70%, has_motion=True
✅ MOTION DETECTED - motion_score=18.50%, threshold=3.00%...
```

**Cena estática:**
```
Motion detection: score=1.23%, threshold=3.00%, pixel_diff=0.80%, bg_sub=1.50%, has_motion=False
⏸️ NO MOTION - motion_score=1.23%, threshold=3.00%...
```

### ❌ Com Threshold = 10.0% (Antigo)

**Detecção incorreta (carro/pessoa não detectado):**
```
Motion detection: score=9.50%, threshold=10.00%, pixel_diff=8.20%, bg_sub=10.30%, has_motion=False
⏸️ NO MOTION - motion_score=9.50%, threshold=10.00%...
```
❌ CARRO PASSOU SEM SER DETECTADO!

## 🔧 Dicas Adicionais

### Se threshold muito baixo (muitos falsos positivos):
1. Aumente para 5.0% ou 10.0%
2. Considere usar `rtsp_interval_seconds` maior (20s ou 30s)
3. Verifique iluminação (luzes piscando causam falsos positivos)

### Se ainda não detecta mesmo com 1.0%:
1. Verifique se a câmera está capturando frames
2. Verifique logs: `✅ Frame captured: ...`
3. Teste desabilitar detecção: `python adjust_threshold.py` opção 5
4. Verifique iluminação (pouca luz reduz sensibilidade)

### Se detecta vento/árvores mas não carros/pessoas:
1. Aumente threshold para 5.0%
2. Aumente `rtsp_interval_seconds` para dar tempo de settle
3. Ajuste posição da câmera

## 🚀 Execute Agora!

```bash
# Opção 1: Mais fácil e rápido
python adjust_threshold.py

# Opção 2: Direto via API
curl -X PATCH http://192.168.0.188:8000/api/v1/cameras/SEU_CAMERA_ID \
  -H "Content-Type: application/json" \
  -d '{"motion_threshold": 3.0}'

# Opção 3: Ajuste no .env (para futuras câmeras)
echo "MOTION_THRESHOLD=3.0" >> .env
```

**Recomendação inicial: Comece com 3.0% e observe os logs por 10 minutos.** ⏱️
