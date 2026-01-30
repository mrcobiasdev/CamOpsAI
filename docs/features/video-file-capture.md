# Captura de Arquivos de Vídeo

## Visão Geral

O CamOpsAI suporta o uso de arquivos de vídeo como fonte de câmera, permitindo:
- Testar e validar o pipeline completo sem hardware de câmera
- Reproduzir cenários específicos com conteúdo de vídeo conhecido
- Desenvolvimento e debug sem streams RTSP ativos
- Validar parâmetros de detecção de movimento em cenários reais

## Diferenças Entre RTSP e Arquivo de Vídeo

| Característica | RTSP | Arquivo de Vídeo |
|--------------|-------|------------------|
| **Fonte** | Stream de câmera IP | Arquivo local (.mp4, .avi, etc.) |
| **Reconexão** | Sim, automática | Não, para ao final |
| **Comportamento final** | Reconecta continuamente | Para captura gracefully |
| **Validação de URL** | Básica (formato RTSP) | Verifica existência e formato |
| **Progresso** | N/A | Sim, `current_frame_number`, `total_frames`, `progress_percentage` |
| **Uso recomendado** | Produção | Testes/Desenvolvimento |

## Formatos Suportados

- `.mp4` (recomendado)
- `.avi`
- `.mov`
- `.mkv`
- `.webm`
- `.flv`
- `.m4v`

## Criar Câmera de Arquivo de Vídeo

### Via API

```bash
curl -X POST "http://localhost:8000/api/v1/cameras" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Câmera de Teste",
    "url": "/path/to/video.mp4",
    "source_type": "video_file",
    "enabled": true,
    "frame_interval": 1,
    "motion_detection_enabled": true,
    "motion_threshold": 10.0
  }'
```

### Campos Importantes

- `source_type`: Deve ser `"video_file"` (o sistema detecta automaticamente se a URL começa com `rtsp://`)
- `url`: Caminho absoluto ou relativo ao arquivo de vídeo
- `frame_interval`: Segundos entre capturas (recomendado 1 segundo para testes)

## Consultar Status de Arquivo de Vídeo

```bash
curl -X GET "http://localhost:8000/api/v1/cameras/{camera_id}/status"
```

**Resposta inclui informações de progresso:**
```json
{
  "status": "capturing",
  "current_frame_number": 150,
  "total_frames": 900,
  "progress_percentage": 16.67,
  "source_type": "video_file",
  "frames_captured": 50,
  "frames_sent": 45,
  "motion_detection_rate": 90.0,
  ...
}
```

## Comportamento Ao Final do Arquivo

Quando o arquivo de vídeo termina:

1. **Câmera muda para status "disconnected"**
2. **FrameGrabber para captura gracefully** (sem reconexão)
3. **Estatísticas são mantidas** (frames capturados, processados, etc.)
4. **Para reiniciar:** Chamar `POST /api/v1/cameras/{id}/start` novamente

## Cenários de Uso

### 1. Testar Pipeline Completo

Validar todo o fluxo: captura → motion detection → LLM → armazenamento → alertas

**Passos:**
1. Crie câmera de arquivo de vídeo
2. Configure detecção de movimento e sensitivity
3. Inicie captura
4. Crie regra de alerta
5. Monitore eventos e alertas

**Benefícios:**
- Não precisa de hardware
- Reprodutível (mesmo vídeo sempre produz mesmos resultados)
- Rápido para validar mudanças

### 2. Calibrar Detecção de Movimento

Ajustar sensitivity presets e threshold com vídeo conhecido.

**Passos:**
1. Use vídeo com movimento conhecido (ex: pessoas andando)
2. Crie câmera com diferentes sensitivities:
   ```bash
   # LOW
   python adjust_threshold.py
   # Escolha opção 3

   # MEDIUM
   python adjust_threshold.py
   # Escolha opção 2

   # HIGH
   python adjust_threshold.py
   # Escolha opção 1
   ```
3. Compare motion scores e detecções
4. Escolha melhor configuração

**Benefícios:**
- Teste controlado
- Comparação direta entre configurações
- Sem variáveis externas (iluminação, etc.)

### 3. Validar Análise LLM

Testar qualidade de descrição e extração de keywords.

**Passos:**
1. Use vídeo com conteúdo conhecido
2. Desabilite detecção de movimento (todos os frames processados)
3. Consulte eventos após processamento
4. Verifique descrições e keywords

**Benefícios:**
- Validação de modelo LLM
- Ajuste de prompts de análise
- Comparação entre provedores (OpenAI vs Anthropic vs Google)

### 4. Reproduzir Bugs

Isolar problemas com vídeo que reproduz o erro.

**Passos:**
1. Salve vídeo que mostra o comportamento anormal
2. Crie câmera com esse vídeo
3. Habilite logging detalhado
4. Analise logs para identificar a causa

**Benefícios:**
- Cenário reproduzível
- Fácil compartilhamento para suporte
- Validação de correção

## Ferramentas de Visualização

### Visualizar Motion Detection

Processar vídeo e gerar visualizações de detecção:

```bash
python tools/visualize_motion.py --video test.mp4 --sensitivity high
```

**Saída:**
- `test_video_frames/` - Frames capturados
- `test_video_motion/` - Máscaras de movimento
- `test_video_annotated/` - Frames anotados com score

### Calibrar com Vídeo Específico

Ajustar sensitivity enquanto processa vídeo:

```bash
python tools/calibrate_motion.py --video test.mp4
```

**Funcionalidades:**
- Preview em tempo real do motion score
- Ajuste de sensitivity presets
- Histórico de scores (últimos 30 segundos)

## Observações Importantes

### 1. Caminhos de Arquivo

Use caminhos absolutos ou relativos ao diretório raiz do projeto:

```bash
# Absoluto
/video/teste.mp4

# Relativo
./videos/teste.mp4
videos/teste.mp4
```

Para variáveis de ambiente:
```bash
# No .env
VIDEOS_DIR=/path/to/videos

# Ao criar câmera
curl -X POST "http://localhost:8000/api/v1/cameras" \
  -d '{"url": "$VIDEOS_DIR/teste.mp4", ...}'
```

### 2. Arquivos Não Encontrados

O sistema valida a existência do arquivo ao criar a câmera:

**Erro 422:**
```json
{
  "detail": "Video file not found: /path/to/video.mp4"
}
```

**Verificações:**
- Caminho está correto
- Arquivo existe
- Permissões de leitura
- Caminho foi expandido corretamente (se usando variáveis)

### 3. Formato Não Suportado

Se o arquivo não tiver um codec suportado pelo OpenCV:

**Comportamento:**
- FrameGrabber falha ao conectar
- Logs mostram erro do OpenCV

**Solução:**
- Use formato `.mp4` (mais compatível)
- Converta com FFmpeg:
  ```bash
  ffmpeg -i input.avi -c:v libx264 -c:a aac output.mp4
  ```

### 4. Performance

Arquivos de vídeo podem processar mais rápido que RTSP:

**Vantagens:**
- Sem latência de rede
- Sem reconexões
- Streaming do disco (mais rápido)

**Desvantagens:**
- Contúdo estático (reprodução em loop)
- Não representa cenário de produção real

## Comparação de Workflows

### Workflow de Produção (RTSP)

```
1. Configurar câmera RTSP
2. Iniciar captura
3. Ajustar sensitivity ao vivo
4. Monitorar em tempo real
5. Ajustar conforme necessário
```

### Workflow de Teste (Arquivo de Vídeo)

```
1. Preparar vídeo de teste
2. Criar câmera de arquivo
3. Processar vídeo completo
4. Analisar resultados
5. Ajustar configuração
6. Reprocessar para validar
```

## Exemplos de Vídeos de Teste

### Vídeo de Alta Qualidade

```
Resolução: 1920x1080
FPS: 30
Codec: H.264
Duração: 5-10 minutos
Conteúdo: Movimento variado (pessoas, veículos, estático)
```

### Vídeo de Curta Duração (Loop)

```
Resolução: 1280x720
FPS: 30
Codec: H.264
Duração: 30-60 segundos (loop)
Conteúdo: Movimento específico para testar (ex: pessoa passando)
```

### Vídeo com Ground Truth

```
Resolução: Qualidade da câmera real
FPS: 30
Codec: H.264
Duração: Variável
Conteúdo: Marcações temporais de eventos conhecidos
```

## Referências

- **API Reference:** `docs/development/api-reference.md` - Endpoint de câmeras
- **Motion Detection:** `docs/features/motion-detection.md` - Sensitivity presets
- **Architecture:** `docs/architecture/system-architecture.md` - FrameGrabber details
- **Source Code:** `src/capture/frame_grabber.py` - Implementação de vídeo

## Histórico

### Mudanças Implementadas (2026-01-30)

**Proposta:** `2026-01-30-add-video-file-capture`

**Funcionalidades Adicionadas:**
- Campo `source_type` em configuração de câmera
- Detecção automática de tipo de fonte (RTSP vs arquivo)
- Validação de existência de arquivo
- Progresso de processamento (frame atual, total, porcentagem)
- Parada graciosa ao final do arquivo
- Suporte a múltiplos formatos de vídeo

**Benefícios:**
- Facilita testes e desenvolvimento
- Permite validação sem hardware
- Reprodutibilidade de cenários
- Calibração controlada de parâmetros
