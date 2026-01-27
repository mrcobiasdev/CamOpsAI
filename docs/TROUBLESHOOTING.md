# Guia de Troubleshooting: Erros H.264 em Câmeras RTSP

## Sintomas

Você está vendo mensagens como estas nos logs:

```
[NULL @ 00000249b325fa40] missing picture in access unit with size 27
[h264 @ 00000249b31f6f00] no frame!
```

## O que isso significa?

**Estas mensagens são NORMAIS** quando usando RTSP com códificação H.264. Elas indicam que:

1. O stream de vídeo enviou pacotes corrompidos ou incompletos
2. O decoder FFmpeg não conseguiu decodificar um frame específico
3. Isso é **esperado** em redes instáveis ou streams RTSP não ideais

## O que o CamOpsAI faz agora?

O sistema foi atualizado para:

✅ **Ignorar erros ocasionais**: Não reconecta imediatamente a cada erro
✅ **Continuar operando**: Mantém captura mesmo com alguns frames perdidos
✅ **Rastrear estatísticas**: Conta erros e taxa de erro via API
✅ **Reconectar apenas quando necessário**: Só reconecta após N erros consecutivos (padrão: 10)

## Como verificar se está funcionando?

### 1. Verifique se frames estão sendo processados

Procure no logs por mensagens de sucesso:

```
Frame processado: câmera=d3002080..., keywords=[...], alertas=0/1
```

Se você ver estas mensagens, **o sistema está funcionando corretamente**.

### 2. Acesse as estatísticas

```bash
curl http://192.168.0.188:8000/api/v1/stats
```

Procure por:
- `decoder_total_errors`: Número total de erros de decoder
- `decoder_avg_error_rate`: Taxa média de erro (em %)
- `motion_detection_rate`: Porcentagem de frames com movimento

### 3. Acesse o status da câmera

```bash
curl http://192.168.0.188:8000/api/v1/cameras/{camera_id}/status
```

Procure por:
- `frames_captured`: Total de frames capturados
- `frames_sent`: Frames enviados para análise (com movimento)
- `frames_filtered`: Frames filtrados (sem movimento)
- `decoder_error_count`: Erros de decoder para esta câmera
- `decoder_error_rate`: Taxa de erro (em %)

## Quando se preocupar?

### ✅ NORMAL (Não precisa fazer nada)
- `decoder_error_rate` < 5%: Sistema saudável
- Mensagens "[NULL @ ...] missing picture" aparecem ocasionalmente
- Detecção de movimento está funcionando

### ⚠️ ATENÇÃO (Ajustar configurações)
- `decoder_error_rate` entre 5-10%: Monitorar
- Muitas mensagens de erro em curto período

**Ajustes possíveis:**

1. **Ajustar limiar de movimento** (motion_threshold)
   ```bash
   # No .env ou atualize a câmera via API
   RTSP_MAX_CONSECUTIVE_ERRORS=5  # Reconecta mais rápido
   ```

2. **Ajustar intervalo de captura** (frame_interval)
   - Maior intervalo = menos chance de capturar frames corrompidos
   - Ex: De 10s para 20s ou 30s

### 🚨 PROBLEMA (Investigar)
- `decoder_error_rate` > 10%: Alta taxa de erro
- Frames não estão sendo processados (nenhuma mensagem "Frame processado")
- Câmera não conecta

**Ações:**

1. **Verificar conexão de rede**
   - Teste ping: `ping 192.168.0.233`
   - Verifique latência e packet loss
   - Considere usar cabo de rede em vez de Wi-Fi

2. **Mudar protocolo de transporte**
   ```bash
   # No .env
   RTSP_TRANSPORT=udp  # Pode ser melhor que tcp em alguns casos
   ```

3. **Verificar configuração da câmera**
   - Reduza resolução da câmera (ex: 1080p → 720p)
   - Ajuste bitrate da câmera para menor
   - Verifique encoding: H.264 é recomendado (evite H.265)

4. **Reiniciar câmera**
   - Desligue e ligue novamente
   - Isso pode limpar problemas de buffer

## Como testar detecção de movimento?

1. Mova-se na frente da câmera
2. Aguarde o intervalo de captura (padrão: 10 segundos)
3. Verifique nos logs:

**Sucesso:**
```
Frame sent: camera=d3002080..., motion_score=15.23, threshold=10.0
Frame processado: câmera=d3002080..., keywords=['pessoa', ...], alertas=1
```

**Sem movimento (esperado):**
```
Frame filtered: camera=d3002080..., motion_score=2.15, threshold=10.0
```

**Erro de decoder (normal, não se preocupe):**
```
[NULL @ ...] missing picture in access unit with size 27
Frame decode failed for camera Entrada Principal (normal with RTSP streams, will retry)
Decoder error skipped for camera Entrada Principal: no frame!
```

## Diferença entre erros

| Erro | Significado | Ação | Severidade |
|-------|-------------|--------|------------|
| `[NULL @ ...] missing picture` | Pacote H.264 incompleto | Ignorar e continuar | Baixa |
| `[h264 @ ...] no frame!` | Falha na decodificação | Ignorar e continuar | Baixa |
| `Too many consecutive errors` | Muitos erros seguidos | Tentar reconectar | Média |
| `ConnectionError` ou `Timeout` | Problema de conexão | Tentar reconectar | Alta |
| `Frame validation failed` | Frame corrompido após decoder | Ignorar e continuar | Baixa |

## Configurações de Ambiente

Todas as configurações estão em `.env`:

```env
# RTSP Configuration
RTSP_TRANSPORT=tcp              # tcp (mais confiável) ou udp (menor latência)
RTSP_ERROR_RECOVERY=true         # Ativa tratamento de erros
RTSP_MAX_CONSECUTIVE_ERRORS=10  # Erros consecutivos antes de reconectar
```

**Recomendações:**
- `RTSP_TRANSPORT=tcp`: Use para melhor confiabilidade (padrão)
- `RTSP_TRANSPORT=udp`: Use apenas se tiver muita latência com TCP
- `RTSP_MAX_CONSECUTIVE_ERRORS=5-15`: Ajuste conforme necessário

## FAQ

### Q: Os erros H.264 significam que meu sistema não está funcionando?
**R:** Não! Se você ver "Frame processado" nos logs, o sistema está funcionando. Os erros do decoder são esperados com streams RTSP/H.264 instáveis.

### Q: Por que vejo esses erros se movo a câmera?
**R:** O stream RTSP pode enviar pacotes corrompidos, especialmente quando:
- Rede está instável
- Câmera está sobrecarregada
- Muitos dispositivos na mesma rede
- Conexão Wi-Fi (use cabo se possível)

### Q: Como sei se a detecção de movimento está funcionando?
**R:** Movimento a câmera e verifique os logs:
- **Com movimento**: `Frame sent: motion_score=15.23`
- **Sem movimento**: `Frame filtered: motion_score=2.15`
- **Processado**: `Frame processado: keywords=['pessoa']`

### Q: Onde vejo o número de erros?
**R:** Acesse `/api/v1/stats` ou `/api/v1/cameras/{id}/status`:
```bash
curl http://192.168.0.188:8000/api/v1/stats
```

Procure por:
- `decoder_total_errors`
- `decoder_avg_error_rate`

### Q: A taxa de erro aceitável?
**R:**
- ✅ < 5%: Excelente
- ⚠️ 5-10%: Aceitável, monitorar
- 🚨 > 10%: Alta, investigar

## Contato

Se após seguir estes passos ainda tiver problemas:
1. Verifique se há mensagens de "Frame processado" nos logs
2. Acesse `/api/v1/stats` e verifique as estatísticas
3. Forneça estas informações ao suporte:
   - URL da câmera
   - `decoder_total_errors`
   - `decoder_avg_error_rate`
   - Exemplos de logs recentes
