# Guia de Troubleshooting

## Visão Geral

Este guia cobre problemas comuns e suas soluções no CamOpsAI, organizados por categoria.

## WhatsApp Web

### QR Code Não Aparece

**Sintoma:** QR code não é exibido ao iniciar a aplicação.

**Causas:**
- Navegador não está visível (headless mode ativado)
- Navegador ainda está carregando
- Erro de inicialização do Playwright

**Soluções:**

1. **Desative headless mode:**
```bash
export WHATSAPP_HEADLESS=false
```

2. **Aguarde alguns segundos:**
```bash
# O QR code pode levar 5-10 segundos para carregar
```

3. **Verifique logs:**
```bash
# Procure por mensagens de autenticação
tail -f logs/camopsai.log | grep -i whatsapp
```

### Sessão Expirou

**Sintoma:** QR code aparece novamente após dias de uso normal.

**Causa:** WhatsApp Web expira sessão após 14-30 dias (comportamento padrão).

**Solução:**

```bash
# 1. Exclua o perfil antigo
rm -rf sessions/whatsapp/browser_profile/

# 2. Reinicie a aplicação
python -m src.main

# 3. Escanee o QR code novamente
```

### Erro "Playwright not found"

**Sintoma:** `ModuleNotFoundError: No module named 'playwright'` ou similar.

**Solução:**

```bash
pip install playwright
playwright install chromium
```

### Erro ao Enviar Mensagem

**Sintoma:** Mensagem não é enviada, log mostra erro.

**Verificações:**

1. **Formato do número:**
```bash
# Deve ser internacional: código país + DDD + número (sem + ou espaços)
5511999999999  # ✅ Correto
+55 11 99999-9999  # ❌ Incorreto
```

2. **Status da sessão:**
```bash
curl http://localhost:8000/api/v1/health
# Procure por "whatsapp_web_authenticated": true
```

3. **Logs de erro:**
```bash
tail -f logs/camopsai.log | grep -i error
```

### WhatsApp Web Desconectado

**Sintoma:** Alertas não são enviados, logs mostram desconexão.

**Causa:** Número usado em múltiplos dispositivos simultaneamente.

**Solução:**

1. Desconecte de outros dispositivos (web, desktop, celular)
2. Aguarde o WhatsApp Web reconectar
3. Se persistir, exclua o perfil e reautentique:
```bash
rm -rf sessions/whatsapp/browser_profile/
```

## Banco de Dados

### Erro de Conexão

**Sintoma:** `connection refused`, `could not connect`, ou similar.

**Soluções:**

1. **Verifique se PostgreSQL está rodando:**
```bash
pg_isready
# Ou verifique o serviço
# Windows: Get-Service postgresql*
# Linux: systemctl status postgresql
```

2. **Verifique string de conexão no .env:**
```bash
# Exemplo correto:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/camopsai
```

3. **Verifique se o banco existe:**
```bash
psql -U postgres -l
# Se não existir, crie:
createdb camopsai
```

### Erro de Migração

**Sintoma:** `alembic upgrade head` falha.

**Soluções:**

1. **Verifique status das migrações:**
```bash
alembic current
```

2. **Recrie o banco se necessário:**
```bash
dropdb camopsai
createdb camopsai
alembic upgrade head
```

3. **Verifique conflito de migrações:**
```bash
alembic heads
alembic branches
```

### Mudanças Não São Persistidas

**Sintoma:** `adjust_threshold.py` atualiza banco, mas mudanças não são salvas.

**Causa:** Bug SQLAlchemy - `flush()` ao invés de `commit()` (corrigido).

**Solução:**

1. **Verifique se o bug foi corrigido:**
```bash
grep "await self.session.commit()" src/storage/repository.py
```

2. **Se ainda usa flush(), aplique correção:**
```bash
# Correção aplicada em 2026-01-22
# Verifique CHANGELOG.md para detalhes
```

## Câmeras RTSP

### Erro de Conexão

**Sintoma:** `Connection refused`, `Unable to open RTSP stream`, ou similar.

**Soluções:**

1. **Teste a URL com VLC ou ffplay:**
```bash
ffplay rtsp://admin:senha@192.168.1.100:554/stream
```

2. **Verifique se a câmera está acessível:**
```bash
ping 192.168.1.100
```

3. **Verifique credenciais:**
```bash
# Teste diferentes formatos de URL:
rtsp://admin:senha@192.168.1.100:554/stream1
rtsp://admin:senha@192.168.1.100:554/h264
```

### Erros H.264 no Decoder

**Sintoma:**
```
[NULL @ 0x...] missing picture in access unit with size 27
[h264 @ 0x...] no frame!
```

**Explicação:** Mensagens normais em RTSP com H.264. Indicam pacotes corrompidos, mas o sistema já trata isso.

**Solução:** O sistema já ignora erros ocasionais. Verifique se:

1. **Frames estão sendo processados:**
```bash
tail -f logs/camopsai.log | grep "Frame processado"
```

2. **Taxa de erro aceitável:**
```bash
curl http://localhost:8000/api/v1/stats
# Procure por "decoder_avg_error_rate"
# < 5% é aceitável
```

3. **Se muitos erros (>10%):**
- Verifique estabilidade da rede
- Reduza resolução do stream da câmera
- Aumente `FRAME_INTERVAL_SECONDS`

### Frames Não São Capturados

**Sintoma:** Nenhum frame sendo capturado, logs sem mensagens de captura.

**Soluções:**

1. **Verifique se a câmera está iniciada:**
```bash
curl http://localhost:8000/api/v1/cameras/{camera_id}/status
# Procure por "status": "capturing"
```

2. **Ajuste intervalo de captura:**
```bash
curl -X PATCH http://localhost:8000/api/v1/cameras/{camera_id} \
  -H "Content-Type: application/json" \
  -d '{"frame_interval": 10}'
```

3. **Verifique logs:**
```bash
tail -f logs/camopsai.log
# Procure por mensagens de erro específicas
```

## Detecção de Movimento

### Motion Score Sempre 0.0

**Sintoma:** `motion_score=0.0%` em todos os frames, todos enviados ao LLM.

**Causas:**
1. Threshold muito baixo (1.0%)
2. Thresholds internos do OpenCV muito altos
3. Câmera estática (background subtraction não detecta nada)

**Soluções:**

1. **Aumente threshold:**
```bash
python adjust_threshold.py
# Escolha opção 3 (5.0%) ou 4 (10.0%)
```

2. **Use sensitivity presets:**
```bash
python tools/update_sensitivity.py <camera-id> high
```

### Carros/Pessoas Não Detectados

**Sintoma:** Motion score baixo (0-5%) mesmo com movimento claro.

**Causa:** Threshold muito conservador para cena outdoor.

**Solução:**

```bash
# Use sensitivity HIGH
python tools/update_sensitivity.py <camera-id> high

# Ou ajuste threshold manualmente para 1.0% ou 3.0%
python adjust_threshold.py
```

### Muitos Falsos Positivos

**Sintoma:** Alertas constantes mesmo sem movimento real.

**Causas:**
- Árvores movendo ao vento
- Luzes piscando
- Threshold muito baixo

**Solução:**

```bash
# Aumente threshold
python adjust_threshold.py
# Escolha opção 4 (10.0%) ou 5 (conservador)

# Ou use sensitivity LOW
python tools/update_sensitivity.py <camera-id> low
```

## Sistema Geral

### Aplicação Não Inicia

**Sintoma:** Erro ao executar `python -m src.main`.

**Soluções:**

1. **Verifique ambiente virtual:**
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

2. **Verifique dependências:**
```bash
pip install -r requirements.txt
```

3. **Verifique variáveis de ambiente:**
```bash
cat .env
# Certifique-se que DATABASE_URL e outras variáveis estão configuradas
```

### Alto Uso de CPU/Memória

**Sintoma:** Sistema consome muitos recursos.

**Causas:**
- Múltiplas câmeras capturando
- Intervalo de captura muito baixo
- Muitos frames sendo processados

**Soluções:**

1. **Aumente intervalo de captura:**
```bash
curl -X PATCH http://localhost:8000/api/v1/cameras/{camera_id} \
  -H "Content-Type: application/json" \
  -d '{"frame_interval": 20}'
```

2. **Habilite detecção de movimento:**
```bash
curl -X PATCH http://localhost:8000/api/v1/cameras/{camera_id} \
  -H "Content-Type: application/json" \
  -d '{"motion_detection_enabled": true}'
```

3. **Use threshold mais conservador:**
```bash
python adjust_threshold.py
# Escolha opção 4 (10.0%)
```

### Custo Alto de LLM API

**Sintoma:** Gastos elevados com API do LLM.

**Causas:**
- Todos os frames sendo enviados (motion detection desabilitado)
- Threshold muito baixo
- Intervalo de captura muito curto

**Soluções:**

1. **Habilite detecção de movimento:**
```bash
curl -X PATCH http://localhost:8000/api/v1/cameras/{camera_id} \
  -H "Content-Type: application/json" \
  -d '{"motion_detection_enabled": true, "motion_threshold": 10.0}'
```

2. **Aumente threshold:**
```bash
python adjust_threshold.py
# Escolha opção 4 (10.0%)
```

3. **Aumente intervalo de captura:**
```bash
curl -X PATCH http://localhost:8000/api/v1/cameras/{camera_id} \
  -H "Content-Type: application/json" \
  -d '{"frame_interval": 20}'
```

## Logs e Diagnóstico

### Habilitar Logs Detalhados

```bash
# No .env
LOG_LEVEL=DEBUG
```

### Ver Logs em Tempo Real

```bash
# Todos os logs
tail -f logs/camopsai.log

# Apenas erros
tail -f logs/camopsai.log | grep ERROR

# Apenas motion detection
tail -f logs/camopsai.log | grep -i motion

# Apenas alertas WhatsApp
tail -f logs/camopsai.log | grep -i whatsapp
```

### Estatísticas do Sistema

```bash
curl http://localhost:8000/api/v1/stats
```

**Resposta inclui:**
- Contagem de câmeras ativas
- Frames processados/descartados
- Taxa de detecção de movimento
- Erros de decoder
- Alertas enviados

## Documentos Consolidados

Este guia consolida informações de:
- `docs/TROUBLESHOOTING.md` - Guia original de troubleshooting
- `docs/BUG_FIX_FLUSH_VS_COMMIT.md` - Bug fix de SQLAlchemy
- `docs/IMPLEMENTACAO_PERSISTENCIA.md` - Implementação de persistência
- Seções de troubleshooting do README.md

## Referências

- **Health Check:** `/api/v1/health` - Status do sistema
- **Stats:** `/api/v1/stats` - Estatísticas detalhadas
- **Camera Status:** `/api/v1/cameras/{id}/status` - Status de câmera específica
