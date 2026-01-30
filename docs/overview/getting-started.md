# Guia de Introdução Rápida

## Pré-requisitos

### Hardware

- Computador com acesso à rede local das câmeras
- Mínimo 8GB RAM (recomendado 16GB para múltiplas câmeras)
- Armazenamento adequado para frames e banco de dados

### Software

- Python 3.10+
- PostgreSQL 14+
- Acesso à API de LLM com suporte a visão (OpenAI, Anthropic, ou Google)

### Rede

- Acesso às câmeras IP na rede local (RTSP)
- Conexão com internet para API do LLM e WhatsApp

## Instalação

### 1. Clonar e Criar Ambiente Virtual

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente (Windows)
.\venv\Scripts\activate

# Ativar ambiente (Linux/Mac)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure:

```env
# Banco de Dados PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/camopsai

# Provedor LLM (openai, anthropic, gemini)
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Google Gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-pro-vision

# WhatsApp Business API (produção)
WHATSAPP_SEND_MODE=api
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_ID=your-phone-number-id

# Ou WhatsApp Web (testes)
WHATSAPP_SEND_MODE=web
WHATSAPP_SESSION_DIR=./sessions/whatsapp/
WHATSAPP_HEADLESS=true

# Processamento
FRAME_INTERVAL_SECONDS=10
FRAMES_STORAGE_PATH=./frames
MAX_QUEUE_SIZE=100

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Logging
LOG_LEVEL=INFO
```

### 3. Configurar Banco de Dados

```bash
# Criar banco de dados PostgreSQL
createdb camopsai

# Executar migrações
alembic upgrade head
```

### 4. Configurar WhatsApp

#### Modo API (Produção)

Configure as variáveis de ambiente:

```env
WHATSAPP_SEND_MODE=api
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_ID=your-phone-number-id
```

**Requisitos:**
- Conta Business do WhatsApp aprovada
- Token de acesso à API
- Phone Number ID

#### Modo Web (Testes/Desenvolvimento)

```env
WHATSAPP_SEND_MODE=web
WHATSAPP_SESSION_DIR=./sessions/whatsapp/
WHATSAPP_HEADLESS=false  # Use false na primeira configuração
```

**Instalação adicional:**
```bash
playwright install chromium
```

**Fluxo de Autenticação:**
1. Primeira execução com `WHATSAPP_HEADLESS=false`
2. O sistema abrirá o navegador e exibirá um QR code
3. Escaneie o QR code com seu aplicativo WhatsApp
4. A sessão será salva automaticamente
5. Nas reinicializações, a sessão será carregada automaticamente
6. Após configurar, pode usar `WHATSAPP_HEADLESS=true`

## Executar a Aplicação

### Modo Desenvolvimento

```bash
uvicorn src.main:app --reload
```

### Modo Produção

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Verificar Instalação

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Acessar Documentação da API

Abra no navegador: `http://localhost:8000/docs`

### Verificar Estatísticas

```bash
curl http://localhost:8000/api/v1/stats
```

## Criar Primeira Câmera

### Câmera RTSP

```bash
curl -X POST "http://localhost:8000/api/v1/cameras" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Entrada Principal",
    "url": "rtsp://admin:senha@192.168.1.100:554/stream",
    "source_type": "rtsp",
    "enabled": true,
    "frame_interval": 10,
    "motion_detection_enabled": true,
    "motion_sensitivity": "medium",
    "motion_threshold": 5.0
  }'
```

### Câmera de Arquivo de Vídeo (Testes)

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

## Criar Primeira Regra de Alerta

```bash
curl -X POST "http://localhost:8000/api/v1/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Detecção de Pessoas",
    "keywords": ["pessoa", "pessoas", "indivíduo"],
    "phone_numbers": ["5511999999999"],
    "enabled": true,
    "priority": "normal",
    "cooldown_seconds": 300
  }'
```

## Ajustar Detecção de Movimento

```bash
# Script interativo
python adjust_threshold.py

# Ou via API
curl -X PATCH http://localhost:8000/api/v1/cameras/{camera_id} \
  -H "Content-Type: application/json" \
  -d '{"motion_sensitivity": "high", "motion_threshold": 10.0}'
```

## Consultar Timeline de Eventos

```bash
curl "http://localhost:8000/api/v1/events/timeline?limit=50"
```

## Testar com Arquivos de Vídeo

O CamOpsAI suporta arquivos de vídeo para testes:

```bash
# Visualizar motion detection em vídeo
python tools/visualize_motion.py --video test.mp4 --sensitivity high

# Calibrar com vídeo específico
python tools/calibrate_motion.py --video test.mp4
```

## Solução de Problemas

### Não Consigo Conectar ao Banco de Dados

```bash
# Verifique se PostgreSQL está rodando
pg_isready

# Crie o banco se não existir
createdb camopsai

# Execute migrações
alembic upgrade head
```

### QR Code do WhatsApp Não Aparece

```bash
# Desative headless mode
export WHATSAPP_HEADLESS=false

# Reinicie a aplicação
python -m src.main
```

### Frames Não São Capturados

```bash
# Verifique status da câmera
curl http://localhost:8000/api/v1/cameras/{camera_id}/status

# Verifique logs
tail -f logs/camopsai.log
```

Para mais problemas, consulte `docs/guides/troubleshooting.md`.

## Próximos Passos

1. Configure suas câmeras RTSP
2. Ajuste sensibilidade de detecção de movimento
3. Crie regras de alerta para suas necessidades
4. Monitore os eventos através da timeline ou API
5. Ajuste configurações conforme necessário

## Referências

- **README.md** - Documentação completa
- **docs/overview/project-overview.md** - Visão geral do sistema
- **docs/features/motion-detection.md** - Detecção de movimento
- **docs/guides/troubleshooting.md** - Troubleshooting detalhado
- **docs/architecture/system-architecture.md** - Arquitetura do sistema
