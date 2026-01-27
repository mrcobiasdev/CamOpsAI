# CamOpsAI

Sistema de monitoramento inteligente de câmeras IP com análise de vídeo por IA.

## Visão Geral

O CamOpsAI é uma aplicação que captura streams de vídeo de câmeras IP em rede local, processa frames selecionados através de modelos LLM (Large Language Models) para descrever eventos em tempo real, e armazena uma timeline de acontecimentos em banco de dados. O sistema também permite configurar alertas baseados em palavras-chave que são enviados via WhatsApp.

## Stack Tecnológica

- **Backend**: Python 3.10+ com FastAPI
- **Banco de Dados**: PostgreSQL 14+ com SQLAlchemy (async)
- **Migrações**: Alembic
- **Processamento de Vídeo**: OpenCV
- **LLM Vision**: OpenAI GPT-4V, Anthropic Claude Vision, Google Gemini Vision (configurável)
- **Notificações**: WhatsApp Business API

## Funcionalidades Principais

### 1. Captura de Vídeo
- Conexão com câmeras IP via protocolo RTSP
- Suporte a múltiplas câmeras simultaneamente
- Captura assíncrona com reconexão automática
- Intervalo de captura configurável por câmera

### 2. Processamento com IA
- Suporte a múltiplos provedores LLM (OpenAI, Anthropic, Google)
- Descrição automática de eventos e atividades nas imagens
- Extração de palavras-chave estruturada
- Taxa de processamento configurável

### 3. Armazenamento e Timeline
- Banco de dados PostgreSQL para registro de eventos
- Timeline cronológica de acontecimentos por câmera
- Histórico pesquisável por palavras-chave e filtros
- Armazenamento de frames em disco

### 4. Sistema de Alertas
- Definição de regras com palavras-chave para monitoramento
- Suporte a dois modos de envio: WhatsApp Business API e WhatsApp Web
- Automação de WhatsApp Web com Playwright para testes
- Sessão persistente do WhatsApp Web
- Cooldown configurável para evitar spam
- Níveis de prioridade (low, normal, high)

## Arquitetura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Câmeras IP    │────▶│  Frame Grabber   │────▶│  Frame Queue    │
│     (RTSP)      │     │    (OpenCV)      │     │   (asyncio)     │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│    WhatsApp     │◀────│  Alert Detector  │◀────│   LLM Vision    │
│   Business API  │     │   (Keywords)     │     │    Analysis     │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │    FastAPI       │◀───▶│   PostgreSQL    │
                        │   REST API       │     │   (SQLAlchemy)  │
                        └──────────────────┘     └─────────────────┘
```

## Estrutura do Projeto

```
CamOpsAI/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Entry point FastAPI + orquestração
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py            # Configurações Pydantic Settings
│   ├── capture/
│   │   ├── __init__.py
│   │   ├── camera.py              # Modelo de câmera e estados
│   │   ├── frame_grabber.py       # Captura RTSP com OpenCV
│   │   └── queue.py               # Fila de processamento async
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── base.py                # Interface base LLM Vision
│   │   ├── openai_vision.py       # Provider OpenAI GPT-4V
│   │   ├── anthropic_vision.py    # Provider Anthropic Claude
│   │   ├── gemini_vision.py       # Provider Google Gemini
│   │   └── factory.py             # Factory pattern para providers
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py            # Conexão PostgreSQL async
│   │   ├── models.py              # SQLAlchemy models
│   │   └── repository.py          # CRUD operations
│   ├── alerts/
│   │   ├── __init__.py
│   │   ├── detector.py            # Detector de keywords com regex
│   │   └── whatsapp.py            # Cliente WhatsApp Business API
│   └── api/
│       ├── __init__.py
│       ├── schemas.py             # Pydantic schemas para API
│       └── routes/
│           ├── __init__.py
│           ├── cameras.py         # Endpoints de câmeras
│           ├── events.py          # Endpoints de eventos
│           └── alerts.py          # Endpoints de alertas
├── alembic/
│   ├── env.py                     # Configuração Alembic async
│   ├── script.py.mako
│   └── versions/
│       ├── 001_initial_schema.py          # Migração inicial
│       ├── 002_add_motion_detection.py    # Detecção de movimento
│       └── 003_add_motion_sensitivity.py  # Sensitivity presets
├── tools/
│   ├── visualize_motion.py        # Visualizar motion detection em vídeos
│   ├── calibrate_motion.py        # Calibração interativa em tempo real
│   ├── check_cameras.py           # Verificar configuração das câmeras
│   ├── update_sensitivity.py      # Atualizar sensitivity no banco
│   └── set_high_sensitivity.py    # Atualizar + hot-reload
├── tests/
│   ├── __init__.py
│   ├── test_motion_detection.py   # Testes de motion detection
│   ├── test_motion_benchmark.py   # Benchmark com vídeos reais
│   └── fixtures/
│       └── videos/                # Vídeos de teste + ground truth
├── docs/
│   ├── MOTION_DETECTION.md        # Guia completo de motion detection
│   └── ...                        # Outras documentações
├── frames/                        # Diretório para frames salvos
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

## Requisitos do Sistema

### Hardware
- Computador com acesso à rede local das câmeras
- Mínimo 8GB RAM (recomendado 16GB para múltiplas câmeras)
- Armazenamento adequado para frames e banco de dados

### Software
- Python 3.10+
- PostgreSQL 14+
- Acesso à API de LLM com suporte a visão

### Rede
- Acesso às câmeras IP na rede local (RTSP)
- Conexão com internet para API do LLM e WhatsApp

## Instalação e Configuração

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

# WhatsApp Business API
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_ID=your-phone-number-id

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

O CamOpsAI suporta dois modos de envio de alertas via WhatsApp:

#### Modo API (Produção)
Usa a WhatsApp Business API oficial. Configure as seguintes variáveis de ambiente:

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
Usa WhatsApp Web com automação via Playwright. Ideal para testes iniciais com seu número pessoal:

```env
WHATSAPP_SEND_MODE=web
WHATSAPP_SESSION_DIR=./sessions/whatsapp/
WHATSAPP_HEADLESS=true
```

**Instalação adicional:**
```bash
# Após instalar dependências, instale os binários do navegador
playwright install chromium
```

**Fluxo de Autenticação:**
1. Primeira execução: Inicie a aplicação com `WHATSAPP_SEND_MODE=web` e `WHATSAPP_HEADLESS=false`
2. O sistema abrirá o navegador e exibirá um QR code
3. Escaneie o QR code com seu aplicativo WhatsApp
4. A sessão será salva automaticamente em `{WHATSAPP_SESSION_DIR}/browser_profile/`
5. Nas reinicializações, a sessão será carregada automaticamente (sem precisar escanear QR code)
6. Após configurar, pode usar `WHATSAPP_HEADLESS=true` para rodar em segundo plano

**Persistência de Sessão:**
O WhatsApp Web usa um contexto persistente que salva automaticamente:
- Cookies de autenticação
- localStorage e sessionStorage
- Estado da aplicação

**Importante:**
- O QR code precisa ser escaneado apenas uma vez
- A sessão expira naturalmente após 14-30 dias (comportamento do WhatsApp)
- Se o QR code aparecer novamente, exclua `sessions/whatsapp/browser_profile/` e comece do zero

**Testando a Persistência:**
Use o script de teste para verificar se a sessão está funcionando:
```bash
python test_session_persistence.py
```

**Dica:** Para testes, use `WHATSAPP_HEADLESS=false` para ver o navegador aberto.

### 5. Iniciar a Aplicação

```bash
# Modo desenvolvimento
uvicorn src.main:app --reload

# Modo produção
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## API REST

Acesse `http://localhost:8000/docs` para a documentação interativa (Swagger UI).

### Endpoints Disponíveis

#### Sistema
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Informações da API |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/stats` | Estatísticas do sistema |

#### Câmeras
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/cameras` | Lista todas as câmeras |
| POST | `/api/v1/cameras` | Cria nova câmera |
| GET | `/api/v1/cameras/{id}` | Detalhes da câmera |
| PUT | `/api/v1/cameras/{id}` | Atualiza câmera |
| DELETE | `/api/v1/cameras/{id}` | Remove câmera |
| POST | `/api/v1/cameras/{id}/start` | Inicia captura |
| POST | `/api/v1/cameras/{id}/stop` | Para captura |
| GET | `/api/v1/cameras/{id}/status` | Status da captura |

#### Eventos
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/events` | Lista eventos (com filtros) |
| GET | `/api/v1/events/timeline` | Timeline de eventos |
| GET | `/api/v1/events/{id}` | Detalhes do evento |
| GET | `/api/v1/events/{id}/frame` | Download do frame |
| GET | `/api/v1/events/search/keywords` | Busca por keywords |

#### Alertas
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/alerts/rules` | Lista regras de alerta |
| POST | `/api/v1/alerts/rules` | Cria regra de alerta |
| GET | `/api/v1/alerts/rules/{id}` | Detalhes da regra |
| PUT | `/api/v1/alerts/rules/{id}` | Atualiza regra |
| DELETE | `/api/v1/alerts/rules/{id}` | Remove regra |
| GET | `/api/v1/alerts/logs` | Histórico de alertas |
| POST | `/api/v1/alerts/test/{id}` | Testa regra de alerta |

## Modelo de Dados

### Tabela: cameras
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | UUID | Identificador único |
| name | VARCHAR(255) | Nome da câmera |
| url | VARCHAR(512) | URL de conexão RTSP |
| enabled | BOOLEAN | Status ativo/inativo |
| frame_interval | INTEGER | Intervalo entre capturas (segundos) |
| motion_detection_enabled | BOOLEAN | Habilita filtro de movimento |
| motion_threshold | FLOAT | Threshold de detecção (%) |
| motion_sensitivity | VARCHAR(20) | Preset de sensibilidade (low/medium/high) |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Data de atualização |

### Tabela: events
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | UUID | Identificador único |
| camera_id | UUID | Referência à câmera |
| timestamp | TIMESTAMP | Momento do evento |
| description | TEXT | Descrição gerada pelo LLM |
| keywords | TEXT[] | Palavras-chave extraídas |
| frame_path | VARCHAR(512) | Caminho do frame salvo |
| confidence | FLOAT | Nível de confiança da análise |
| llm_provider | VARCHAR(50) | Provedor LLM utilizado |
| llm_model | VARCHAR(100) | Modelo utilizado |
| processing_time_ms | INTEGER | Tempo de processamento |

### Tabela: alert_rules
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | UUID | Identificador único |
| name | VARCHAR(255) | Nome da regra |
| keywords | TEXT[] | Palavras-chave para match |
| camera_ids | TEXT[] | Câmeras aplicáveis (null = todas) |
| phone_numbers | TEXT[] | Números para notificação |
| enabled | BOOLEAN | Status ativo/inativo |
| priority | VARCHAR(20) | Prioridade (low/normal/high) |
| cooldown_seconds | INTEGER | Cooldown entre alertas |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Data de atualização |

### Tabela: alert_logs
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | UUID | Identificador único |
| event_id | UUID | Referência ao evento |
| alert_rule_id | UUID | Referência à regra |
| keywords_matched | TEXT[] | Keywords que dispararam |
| sent_to | TEXT[] | Números notificados |
| sent_at | TIMESTAMP | Momento do envio |
| status | VARCHAR(20) | Status (pending/sent/failed) |
| error_message | TEXT | Mensagem de erro (se houver) |

## Fluxo de Processamento

1. **Captura**: O sistema conecta às câmeras via RTSP e captura frames no intervalo configurado
2. **Detecção de Movimento**: Frames são filtrados usando algoritmo híbrido (pixel difference + background subtraction)
3. **Fila**: Apenas frames com movimento significativo são enfileirados para processamento assíncrono
4. **Análise**: LLM Vision analisa cada frame e gera descrição + keywords em JSON
5. **Armazenamento**: Frame salvo em disco, evento salvo no banco de dados
6. **Detecção de Alertas**: Sistema verifica match das keywords com regras de alerta
7. **Notificação**: Se houver match e cooldown permitir, envia alerta via WhatsApp

### Detecção de Movimento

O sistema inclui detecção de movimento para reduzir custos de API LLM:

- **Algoritmo Híbrido**: Combina pixel difference (50%) e background subtraction MOG2 (50%)
- **Sensitivity Presets**: LOW, MEDIUM, HIGH (configurável por câmera)
- **Hot-Reload**: Mudanças de configuração aplicadas sem reiniciar
- **Ferramentas de Calibração**: Visualização de vídeos e calibração em tempo real

**Configurar Sensitivity:**
```bash
python adjust_threshold.py
# Escolha: LOW (indoor), MEDIUM (geral), HIGH (outdoor/ruas)
```

**Documentação completa**: [docs/MOTION_DETECTION.md](docs/MOTION_DETECTION.md)

## Exemplos de Uso

### Criar uma Câmera via API

```bash
curl -X POST "http://localhost:8000/api/v1/cameras" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Entrada Principal",
    "url": "rtsp://admin:senha@192.168.1.100:554/stream",
    "enabled": true,
    "frame_interval": 10
  }'
```

### Criar uma Regra de Alerta

```bash
curl -X POST "http://localhost:8000/api/v1/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Detecção de Pessoas",
    "keywords": ["pessoa", "pessoas", "indivíduo", "homem", "mulher"],
    "phone_numbers": ["+5511999999999"],
    "enabled": true,
    "priority": "normal",
    "cooldown_seconds": 300
  }'
```

### Consultar Timeline de Eventos

```bash
curl "http://localhost:8000/api/v1/events/timeline?limit=50"
```

### Calibrar Detecção de Movimento

```bash
# Visualizar motion detection em vídeo gravado
python tools/visualize_motion.py --video test.mp4 --sensitivity high

# Calibrar interativamente com câmera ao vivo
python tools/calibrate_motion.py --camera <camera-id>

# Verificar configuração das câmeras
python tools/check_cameras.py

# Atualizar sensitivity de uma câmera
python tools/update_sensitivity.py <camera-id> high
```

## Solução de Problemas (Troubleshooting)

### WhatsApp Web

#### QR Code não aparece
- Verifique se o navegador está aberto (use `WHATSAPP_HEADLESS=false` durante a configuração)
- Aguarde alguns segundos para o QR code carregar
- Verifique logs para mensagens de autenticação

#### Sessão expirou
- Se a sessão expirar, exclua o arquivo `sessions/whatsapp/state.json`
- Reinicie a aplicação e escaneie o QR code novamente

#### Erro "Playwright not found"
```bash
pip install playwright
playwright install chromium
```

#### Erro ao enviar mensagem
- Verifique se o número está no formato internacional: 5511999999999
- Confirme que a sessão está autenticada (check `/api/v1/health`)
- Revise logs para mensagens de erro específicas

### Banco de Dados

#### Erro de conexão
- Verifique se o PostgreSQL está rodando: `pg_isready`
- Confirme as credenciais no arquivo `.env`
- Verifique se o banco de dados existe: `createdb camopsai`

#### Erro de migração
```bash
# Verifique status das migrações
alembic current

# Recrie o banco se necessário
dropdb camopsai
createdb camopsai
alembic upgrade head
```

### Câmeras RTSP

#### Erro de conexão
- Verifique se a câmera está acessível na rede
- Teste a URL RTSP com um player de vídeo (VLC, ffplay)
- Verifique credenciais de autenticação

#### Frames não estão sendo capturados
- Verifique logs do sistema: `tail -f logs/camopsai.log`
- Confirme que a câmera está iniciada: `GET /api/v1/cameras/{id}/status`
- Ajuste `FRAME_INTERVAL_SECONDS` se necessário

### Dependências Principais

```
fastapi>=0.104.0          # Framework web
uvicorn[standard]>=0.24.0 # Servidor ASGI
sqlalchemy>=2.0.0         # ORM
alembic>=1.12.0           # Migrações
asyncpg>=0.29.0           # Driver PostgreSQL async
pydantic>=2.5.0           # Validação de dados
pydantic-settings>=2.1.0  # Configurações
opencv-python>=4.8.0      # Processamento de vídeo
openai>=1.3.0             # API OpenAI
anthropic>=0.7.0          # API Anthropic
google-generativeai>=0.3.0 # API Google
playwright>=1.40.0         # Automação de navegador (WhatsApp Web)
httpx>=0.25.0             # Cliente HTTP async
Pillow>=10.1.0            # Processamento de imagens
```

## Considerações de Segurança

- Credenciais de câmeras armazenadas em variáveis de ambiente
- API keys não expostas em logs
- Suporte a HTTPS para produção
- Validação de entrada em todos os endpoints

## Limitações Conhecidas

- Latência dependente da velocidade da API do LLM
- Custos de API proporcional ao volume de análises
- Qualidade da descrição dependente do modelo LLM utilizado
- WhatsApp Business API requer conta aprovada (para produção)
- WhatsApp Web é adequado para testes, mas não recomendado para alta escala
- WhatsApp Web pode ser desconectado se o número for usado em múltiplos dispositivos simultaneamente

## Roadmap Futuro

- [ ] Interface web para visualização em tempo real
- [ ] Suporte a detecção de objetos local (YOLO)
- [ ] Integração com Telegram e Email
- [ ] Dashboard de analytics
- [ ] Autenticação JWT na API
- [ ] Docker e docker-compose
- [ ] Testes automatizados
- [ ] Exportação de relatórios

## Licença

Este projeto é de uso privado.

## Contato

Para suporte ou dúvidas sobre o projeto, entre em contato com a equipe de desenvolvimento.
