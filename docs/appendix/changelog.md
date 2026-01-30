# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [Unreleased]

### Adicionado
- **Motion Detection Sensitivity Presets**: Sistema de sensibilidade configurável (LOW/MEDIUM/HIGH)
  - Presets otimizados para diferentes cenários (indoor/outdoor/ruas)
  - Campo `motion_sensitivity` adicionado ao modelo de câmera (migração 003)
  - Hot-reload: mudanças aplicadas sem reiniciar a aplicação
  - Ferramentas de calibração e visualização:
    - `tools/visualize_motion.py` - Processar vídeos e gerar visualizações
    - `tools/calibrate_motion.py` - Calibração interativa em tempo real
    - `tools/check_cameras.py` - Verificar configuração das câmeras
    - `tools/update_sensitivity.py` - Atualizar sensitivity no banco
  - Debug mode com salvamento de frames intermediários
  - Testes automatizados com benchmark de vídeos reais
  - Documentação completa: `docs/MOTION_DETECTION.md` (300+ linhas)

- **Persistência de Sessão do WhatsApp Web**: Implementado contexto persistente do Playwright usando `launch_persistent_context`
  - O QR code agora precisa ser escaneado apenas uma vez
  - Sessão salva automaticamente em `{WHATSAPP_SESSION_DIR}/browser_profile/`
  - Recuperação automática da sessão nas reinicializações
  - Melhorias na lógica de autenticação e verificação de sessão ativa
  - Salvamento automático da sessão após cada mensagem enviada
  - Script de teste `test_session_persistence.py` para validar persistência de sessão
  - Documentação `docs/WHATSAPP_SESSION_PERSISTENCE.md` com instruções detalhadas

### Alterado
- **Motion Detection Algorithm**: Parâmetros otimizados para outdoor
  - GaussianBlur kernel: (5,5)/(3,3) dependendo do preset (FIXADO para usar valores ÍMPARES)
  - Pixel threshold reduzido: 15 → 10 (MEDIUM), 5 (HIGH)
  - Pixel scale aumentado: 10 → 15 (MEDIUM), 20 (HIGH)
  - MOG2 background subtractor: varThreshold 16→10 (MEDIUM), 8 (HIGH); history 200→500 (MEDIUM), 700 (HIGH)
  - **Resultado**: Detecção de veículos em ruas melhorada de 0-3% para 25-50%

- **WhatsApp Web**: Melhorado método `initialize()` para usar contexto persistente
- **WhatsApp Web**: Otimizado método `_authenticate()` para verificar autenticação mais rapidamente
- **WhatsApp Web**: Atualizado método `close()` para lidar corretamente com contexto persistente
- **WhatsApp Web**: Adicionado método `_save_session()` para salvamento de backup

- **API Schemas**: Adicionado suporte para `motion_sensitivity` em CameraCreate/Update/Response
- **Repository**: CRUD completo para campo `motion_sensitivity`
- **FrameGrabber**: Integração com sensitivity presets e hot-reload
- **adjust_threshold.py**: Nova UI para selecionar sensitivity presets

### Corrigido
- **CRÍTICO**: GaussianBlur kernel usando valores PARES causava erro no OpenCV (fixado para ÍMPARES)
- **Motion Detection**: Detecção muito conservadora para cenários outdoor
  - Veículos passando em ruas não eram detectados (0-3% score)
  - Agora detecta corretamente com 25-50% score em HIGH sensitivity
- **QR code**: Era exibido em todas as execuções, mesmo com sessão salva anteriormente
- **WhatsApp Web**: Tempo de espera desnecessário ao carregar sessão (15s → 5s)
- **WhatsApp Web**: Perda de sessão ao fechar e reabrir o navegador

### Banco de Dados
- **Migração 003**: `alembic/versions/003_add_motion_sensitivity.py`
  - Adiciona coluna `motion_sensitivity` (String(20), default="medium")
  - Compatível com migrações anteriores
  - Aplicar com: `python -m alembic upgrade head`

---

## [1.0.0] - 2025-01-XX

### Adicionado
- Sistema de monitoramento de câmeras IP com captura RTSP
- Processamento de frames com LLM Vision (OpenAI, Anthropic, Google)
- Sistema de alertas baseado em palavras-chave
- Envio de alertas via WhatsApp (Business API e Web)
- API REST com FastAPI
- Armazenamento de eventos e timeline em PostgreSQL
- Interface Swagger para documentação da API
- Detecção de movimento com OpenCV
- Fila de processamento assíncrona

### Estrutura
- Captura de vídeo via RTSP
- Processamento com múltiplos provedores LLM
- Sistema de alertas configurável
- Persistência em PostgreSQL
- API REST completa

---

## Notas de Versão

### Formato de Versão
- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Funcionalidades adicionadas de forma compatível
- **PATCH**: Correções de bugs compatíveis

### Tipos de Mudanças
- `Adicionado`: novas funcionalidades
- `Alterado`: modificações em funcionalidades existentes
- `Removido`: funcionalidades removidas
- `Corrigido`: correções de bugs
- `Segurança`: correções de segurança
