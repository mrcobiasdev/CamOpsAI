# Sumário de Propostas Arquivadas (OpenSpec)

## Visão Geral

O CamOpsAI utiliza OpenSpec (workflow de desenvolvimento dirigido por especificações) para gerenciar mudanças no sistema. Cada nova funcionalidade, bug fix ou melhoria passa por um processo de três estágios:

1. **Criar Proposta** - Documentação do que será mudado, por que, impacto
2. **Implementar** - Desenvolvimento seguindo a proposta aprovada
3. **Arquivar** - Mover para histórico após deployment

Este documento resume todas as propostas arquivadas, mostrando a evolução do projeto.

## Histórico de Propostas

### Tabela Resumida

| ID da Proposta | Data | Título | Status | Motivo do Arquivamento |
|---------------|------|---------|---------|-------------------------|
| 2026-01-19-update-frame-interval-defaults | 2026-01-19 | Implementado | Funcionalidade completada e mesclada |
| 2026-01-20-fix-h264-decoding-errors | 2026-01-20 | Implementado | Tratamento de erros melhorado |
| 2026-01-20-implement-motion-detection | 2026-01-20 | Implementado | Detecção de movimento implementada |
| 2026-01-22-add-whatsapp-web-automation | 2026-01-22 | Implementado | WhatsApp Web implementado |
| 2026-01-22-fix-threshold-update | 2026-01-22 | Implementado | Hot-reload implementado |
| 2026-01-22-improve-motion-sensitivity | 2026-01-22 | Implementado | Sensitivity presets otimizados |
| 2026-01-27-add-gitignore | 2026-01-27 | Implementado | Segurança do repositório |
| 2026-01-27-add-openspec-archive-commit-workflow | 2026-01-27 | Implementado | Workflow de commits definido |
| 2026-01-27-initialize-git-repository | 2026-01-27 | Implementado | Repositório Git inicializado |
| 2026-01-28-add-frame-annotation | 2026-01-28 | Cancelado | Não implementado (baixa prioridade) |
| 2026-01-28-clear-queue-on-startup | 2026-01-28 | Implementado | Limpeza explícita de fila |
| 2026-01-28-discard-initial-frames | 2026-01-28 | Implementado | Descarte de frames iniciais |
| 2026-01-30-add-video-file-capture | 2026-01-30 | Implementado | Suporte a arquivos de vídeo |

## Detalhes das Propostas

### 1. Update Frame Interval Defaults (2026-01-19)

**Objetivo:** Usar `FRAME_INTERVAL_SECONDS` do ambiente como default para novas câmeras.

**Problema:** Variável de ambiente existia mas não era usada. Cada câmera tinha seu próprio default hardcoded (10 segundos).

**Solução:**
- Atualizar `CameraConfig.frame_interval` para ler de settings
- Atualizar defaults no banco de dados, API, e repository
- Garantir consistência em todas as camadas

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Configuração global mais fácil
- Consistência garantida

**Especificações Afetadas:** `camera-config`

---

### 2. Fix H.264 Decoding Errors (2026-01-20)

**Objetivo:** Tratar erros de decoder H.264 em streams RTSP sem falhar completamente.

**Problema:** Streams RTSP enviam pacotes corrompidos ocasionalmente. O decoder falhava e causava reconexão constante, perdendo eventos.

**Solução:**
- Configurar FFmpeg para recovery automático
- Ignorar erros ocasionais (reconectar apenas após N erros consecutivos)
- Rastrear estatísticas de erros
- Validar frames antes de motion detection

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Menos reconexões
- Menos eventos perdidos
- Monitoramento de saúde do decoder

**Especificações Afetadas:** `rtsp-stream-reliability`, `frame-processing-queue`

---

### 3. Implement Motion Detection (2026-01-20)

**Objetivo:** Adicionar detecção de movimento para filtrar frames antes do processamento LLM.

**Problema:** Todos os frames eram enviados ao LLM, incluindo cenas estáticas, desperdiçando API quota.

**Solução:**
- Algoritmo híbrido (pixel difference + background subtraction)
- Database migration para settings de motion detection
- Integração com FrameGrabber
- Estatísticas e logging

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Redução de custos de API (70-90% de frames filtrados)
- Melhor latência (menos frames na fila)
- Apenas conteúdo relevante processado

**Especificações Afetadas:** `camera-config` (extendido), `motion-detection` (nova)

---

### 4. Add WhatsApp Web Automation (2026-01-22)

**Objetivo:** Adicionar suporte a WhatsApp Web para testes sem conta Business.

**Problema:** WhatsApp Business API requer aprovação, dificultando testes iniciais.

**Solução:**
- Automação via Playwright
- Autenticação via QR code
- Sessão persistente
- Modo API vs Web configurável

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Testes sem aprovação de conta
- Rápido ciclo de desenvolvimento
- Automação completa após primeira configuração

**Especificações Afetadas:** `whatsapp-notifications` (nova)

---

### 5. Fix Threshold Update (2026-01-22)

**Objetivo:** Corrigir problema onde `adjust_threshold.py` atualizava banco mas FrameGrabber não refletia mudanças.

**Problema:** `FrameGrabber` usava config estática passado na inicialização. Atualização no banco não afetava runtime.

**Solução:**
- Método `update_config()` em FrameGrabber
- Método `update_camera_config()` em CameraManager
- Reinicialização de MotionDetector quando threshold muda
- Thread-safety com lock

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Hot-reload de configuração
- Sem necessidade de reiniciar aplicação
- Melhor UX para ajustes

**Especificações Afetadas:** Nenhuma (hot-reload é feature, não spec change)

**Bug Fix Relacionado:** SQLAlchemy flush vs commit (2026-01-22)

---

### 6. Improve Motion Sensitivity (2026-01-22)

**Objetivo:** Otimizar algoritmo de detecção de movimento para cenários outdoor.

**Problema:** Veículos em ruas não eram detectados (motion score 0-3% mesmo com movimento claro).

**Solução:**
- Sensitivity presets (LOW/MEDIUM/HIGH)
- Otimização de parâmetros OpenCV
- Kernel GaussianBlur ímpares (bug fix)
- Redução de thresholds internos
- Aumento de escala de pixel diff

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Detecção de veículos outdoor: 0-3% → 25-50%
- Configuração mais fácil (presets)
- Adequação para diferentes cenários

**Especificações Afetadas:** `camera-config`, `motion-detection`

---

### 7. Add .gitignore (2026-01-27)

**Objetivo:** Proteger informações sensíveis de serem commitadas ao repositório Git.

**Problema:** Repositório não tinha .gitignore, arriscando expor: .env, frames/, sessions/, venv/, etc.

**Solução:**
- Criar .gitignore com padrões Python
- Excluir arquivos sensíveis
- Excluir conteúdo gerado

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Segurança do repositório
- Prevenção de commits acidentais

**Especificações Afetadas:** `repository-security` (nova)

---

### 8. Add OpenSpec Archive Commit Workflow (2026-01-27)

**Objetivo:** Definir workflow para commits após arquivamento de propostas.

**Problema:** Arquivar propostas não incluía commits automáticos, arriscando trabalho perdido.

**Solução:**
- Definir workflow de três estágios em AGENTS.md
- Documentar processo de commit após arquivamento
- Opcional: script de automação

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Trabalho preservado
- Histórico consistente
- Processo claro para desenvolvedores

**Especificações Afetadas:** `git-workflow`

---

### 9. Initialize Git Repository (2026-01-27)

**Objetivo:** Inicializar repositório Git com estrutura de commits organizada.

**Problema:** Repositório tinha arquivos staged mas nenhum commit, sem histórico claro.

**Solução:**
- Inicializar repositório Git
- Commits lógicos por funcionalidade
- Configurar remoto GitHub
- Push inicial

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Histórico organizado
- Colaboração facilitada
- Deploy tracking

**Especificações Afetadas:** `git-workflow` (nova)

---

### 10. Add Frame Annotation (2026-01-28)

**Objetivo:** Adicionar visualização anotada de frames para auditiamento humano.

**Motivação:** Facilitar revisão de eventos mostrando o que foi detectado e onde.

**Solução Proposta:**
- Gerar versões anotadas de frames
- Overlay de motion detection (score, threshold, máscara)
- Overlay de LLM analysis (keywords, confiança)
- Armazenamento separado (ex: `*_annotated.jpg`)
- API para retrieve anotados

**Status:** ❌ Cancelado (não implementado)

**Motivo do Cancelamento:**
- Baixa prioridade em relação a outras funcionalidades
- Aumento de uso de armazenamento
- Overhead de processamento adicional

**Especificações Afetadas:** Nenhuma (não implementado)

---

### 11. Clear Queue on Startup (2026-01-28)

**Objetivo:** Tornar explícito a limpeza da fila de processamento ao iniciar.

**Motivação:** Embora a fila fosse recriada a cada inicialização (zerando contadores), era importante tornar isso explícito no código.

**Solução:**
- Método `clear()` em FrameQueue
- Chamada explícita durante startup
- Documentação clara de comportamento

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Código mais legível
- Intenção clara
- Facilita testes

**Especificações Afetadas:** `frame-processing-queue`

---

### 12. Discard Initial Frames (2026-01-28)

**Objetivo:** Descartar frames iniciais após conexão para evitar processamento instável.

**Motivação:** Frames logo após conexão podem ser instáveis ou incompletos, causando falsos positivos de motion detection.

**Solução:**
- Variável `INITIAL_FRAMES_TO_DISCARD` (default: 5)
- Descarte após conexão inicial e reconexões
- Frames descartados usados para estabilizar baseline de motion detector
- Logging e estatísticas

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Menos falsos positivos de startup
- Processamento mais confiável
- Baseline estabilizado

**Especificações Afetadas:** `camera-config`, `rtsp-stream-reliability`, `frame-processing-queue`

---

### 13. Add Video File Capture (2026-01-30)

**Objetivo:** Adicionar suporte a arquivos de vídeo como fonte de câmera.

**Motivação:** Facilitar testes, validação e desenvolvimento sem necessidade de hardware de câmera.

**Solução:**
- Campo `source_type` em configuração de câmera
- Detecção automática de tipo (RTSP vs arquivo)
- Validação de existência de arquivo
- Parada graciosa ao final do arquivo
- Progresso de processamento (frame atual, total, porcentagem)

**Status:** ✅ Implementado e arquivado

**Impacto:**
- Testes sem hardware
- Validação de parâmetros controlada
- Desenvolvimento mais rápido
- Reprodutibilidade de bugs

**Especificações Afetadas:** `camera-config`, `motion-detection`, `frame-processing-queue`

## Evolução do Projeto

### Por Categoria

#### Funcionalidades Core
1. **Captura de Vídeo** (Inicial) - RTSP + arquivos de vídeo
2. **Detecção de Movimento** (2026-01-20) - Filtragem eficiente
3. **Processamento LLM** (Inicial) - Múltiplos provedores
4. **Armazenamento** (Inicial) - PostgreSQL + frames

#### Sistema de Alertas
1. **WhatsApp API** (Inicial) - Modo produção
2. **WhatsApp Web** (2026-01-22) - Modo teste
3. **Sessão Persistente** (2026-01-22) - QR code único

#### Melhorias de Confiabilidade
1. **Tratamento H.264** (2026-01-20) - Menos reconexões
2. **Discarte de Frames Iniciais** (2026-01-28) - Menos falsos positivos
3. **Hot-Reload de Configuração** (2026-01-22) - Sem reinícios

#### Ferramentas de Desenvolvimento
1. **OpenCode** (Inicial) - IA coding assistant
2. **OpenSpec** (Inicial) - Spec-driven development
3. **Git Workflow** (2026-01-27) - Estrutura de commits
4. **Git Repository** (2026-01-27) - Histórico organizado

#### Calibração e Testes
1. **Sensitivity Presets** (2026-01-22) - LOW/MEDIUM/HIGH
2. **Visualização de Motion** (Inicial) - Ferramentas de debug
3. **Arquivos de Vídeo para Testes** (2026-01-30) - Testes controlados

### Por Especificação

| Especificação | Propostas | Status |
|--------------|-----------|---------|
| `camera-config` | 5 (update-frame-interval, implement-motion, improve-sensitivity, discard-initial-frames, add-video-file) | ✅ Ativa |
| `motion-detection` | 3 (implement-motion, improve-sensitivity, discard-initial-frames) | ✅ Ativa |
| `rtsp-stream-reliability` | 2 (fix-h264-errors, discard-initial-frames) | ✅ Ativa |
| `frame-processing-queue` | 3 (fix-h264-errors, clear-queue, discard-initial-frames) | ✅ Ativa |
| `whatsapp-notifications` | 1 (add-whatsapp-web) | ✅ Ativa |
| `git-workflow` | 2 (add-commit-workflow, initialize-git) | ✅ Ativa |
| `repository-security` | 1 (add-gitignore) | ✅ Ativa |
| `frame-annotation` | 1 (add-frame-annotation) | ❌ Cancelado |

## Lições Aprendidas

### Sucesso do OpenSpec

O workflow de OpenSpec proporcionou:
1. **Clareza de Escopo** - Cada mudança tinha objetivos claros
2. **Planejamento** - Tasks detalhadas antes de implementar
3. **Traceabilidade** - Histórico completo de decisões
4. **Qualidade** - Validação antes de aprovar

### Melhores Práticas Identificadas

1. **Spec-Driven** - Escrever spec antes de código reduz rework
2. **Small Changes** - Mudanças pequenas e testáveis são mais fáceis
3. **Iteração** - Melhorias incrementais funcionam melhor que grandes refactors
4. **Documentação** - Documentar "por que" é tão importante quanto "o que"

## Referências

- **OpenSpec AGENTS.md** - `openspec/AGENTS.md` - Workflow completo
- **Specs Atuais** - `openspec/specs/` - Especificações ativas
- **Propostas Arquivadas** - `openspec/changes/archive/` - Propostas detalhadas
- **CHANGELOG** - `docs/appendix/changelog.md` - Histórico de mudanças

## Conclusão

O CamOpsAI evoluiu de um MVP básico para um sistema robusto através de 13 propostas OpenSpec. Cada proposta representou uma mudança significativa, com documentação clara, implementação focada, e validação adequada. O processo resultou em:

- **12 propostas implementadas** (92% taxa de sucesso)
- **1 proposta cancelada** (prioridade ajustada)
- **Especificações bem-definidas** para todas as funcionalidades core
- **Workflow claro** para desenvolvimento futuro

O uso de OpenCode e OpenSpec acelerou significativamente o desenvolvimento, permitindo iterações rápidas sem comprometer qualidade.
