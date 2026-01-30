# WhatsApp Notifications

## Visão Geral

O CamOpsAI suporta envio de alertas via WhatsApp em dois modos:
1. **WhatsApp Business API** - Modo produção (requer conta aprovada)
2. **WhatsApp Web** - Modo teste (usando Playwright, ideal para desenvolvimento)

## Modos de Operação

### Modo API (Produção)

Usa a WhatsApp Business API oficial para envio de alertas.

**Requisitos:**
- Conta Business do WhatsApp aprovada
- Token de acesso à API
- Phone Number ID

**Configuração:**

```env
WHATSAPP_SEND_MODE=api
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_ID=your-phone-number-id
```

**Funcionalidades:**
- Envio direto via API REST
- Alta confiabilidade
- Suporta múltiplos destinatários
- Rastreamento de status de envio

### Modo Web (Testes/Desenvolvimento)

Usa WhatsApp Web com automação via Playwright para testes.

**Requisitos:**
- Navegador Chromium instalado
- Número WhatsApp pessoal para testes
- Primeira autenticação via QR code

**Configuração:**

```env
WHATSAPP_SEND_MODE=web
WHATSAPP_SESSION_DIR=./sessions/whatsapp/
WHATSAPP_HEADLESS=true
```

**Instalação:**
```bash
# Após instalar dependências do projeto
playwright install chromium
```

## Persistência de Sessão (WhatsApp Web)

### Como Funciona

O WhatsApp Web usa um contexto persistente que salva automaticamente:
- Cookies de autenticação
- LocalStorage e sessionStorage
- Estado da aplicação

### Primeira Execução

1. Configure `WHATSAPP_HEADLESS=false` para visualizar o navegador
2. Inicie a aplicação
3. O sistema abrirá o navegador e exibirá um QR code
4. Escaneie o QR code com seu aplicativo WhatsApp
5. A sessão será salva automaticamente em `{WHATSAPP_SESSION_DIR}/browser_profile/`

### Execuções Posteriores

1. Configure `WHATSAPP_HEADLESS=true` para execução em segundo plano
2. Inicie a aplicação
3. A sessão será carregada automaticamente (sem precisar escanear QR code)
4. Alertas serão enviados normalmente

### Expiração de Sessão

A sessão expira naturalmente após 14-30 dias (comportamento do WhatsApp).

**Se o QR code aparecer novamente:**
```bash
# Exclua o perfil antigo
rm -rf sessions/whatsapp/browser_profile/

# Reinicie e escaneie novamente
```

## Criando Regras de Alerta

### Via API

```bash
curl -X POST "http://localhost:8000/api/v1/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Detecção de Pessoas",
    "keywords": ["pessoa", "pessoas", "indivíduo", "homem", "mulher"],
    "camera_ids": [],
    "phone_numbers": ["5511999999999"],
    "enabled": true,
    "priority": "normal",
    "cooldown_seconds": 300
  }'
```

### Campos da Regra

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | String | Nome da regra |
| `keywords` | String[] | Lista de palavras-chave para match |
| `camera_ids` | String[] | IDs de câmeras (vazio = todas) |
| `phone_numbers` | String[] | Números para notificação |
| `enabled` | Boolean | Status ativo/inativo |
| `priority` | String | `low`, `normal`, ou `high` |
| `cooldown_seconds` | Integer | Tempo mínimo entre alertas |

## Testando WhatsApp Web

### Teste Manual

```bash
# 1. Configure headless=false
export WHATSAPP_HEADLESS=false

# 2. Inicie a aplicação
python -m src.main

# 3. Escaneie o QR code

# 4. Crie uma regra de alerta
curl -X POST "http://localhost:8000/api/v1/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Teste",
    "keywords": ["teste"],
    "phone_numbers": ["5511999999999"],
    "enabled": true,
    "cooldown_seconds": 60
  }'

# 5. Dispare um alerta (via evento com palavra-chave "teste")
```

### Teste Automatizado

```bash
python tests/test_session_persistence.py
```

**O script faz:**
1. Envia mensagem na primeira execução
2. Fecha navegador
3. Reabre navegador
4. Envia segunda mensagem (sem QR code)
5. Reporta sucesso ou falha

## Troubleshooting

### QR Code Não Aparece

- Verifique se o navegador está aberto (use `WHATSAPP_HEADLESS=false`)
- Aguarde alguns segundos para o QR code carregar
- Verifique logs para mensagens de autenticação

### Sessão Expirou

```bash
# Exclua o perfil
rm -rf sessions/whatsapp/browser_profile/

# Reinicie a aplicação
python -m src.main

# Escanee o QR code novamente
```

### Erro "Playwright not found"

```bash
pip install playwright
playwright install chromium
```

### Erro ao Enviar Mensagem

**Verificações:**
- Formato do número internacional: 5511999999999
- Sessão autenticada (check `/api/v1/health`)
- Logs para mensagens de erro específicas

### WhatsApp Web Desconectado

Se o número for usado em múltiplos dispositivos simultaneamente:
- Use apenas um dispositivo por vez
- Aguarde o WhatsApp Web reconectar
- Se persistir, exclua o perfil e reautentique

## Modo API vs Modo Web

| Característica | API (Produção) | Web (Testes) |
|----------------|-----------------|----------------|
| **Requisitos** | Conta Business aprovada | Número pessoal |
| **Instalação** | Configuração de API | Playwright + Chromium |
| **Primeira execução** | Configuração via API | QR code |
| **Persistência** | Estado via API | Sessão do navegador |
| **Confiabilidade** | Alta | Média |
| **Custo** | Taxas da API | Gratuito |
| **Uso recomendado** | Produção | Desenvolvimento/Tests |
| **Escala** | Alta | Baixa/Média |

## Melhorias Implementadas

### Persistência de Sessão (2026-01-22)

**Problema original:**
- QR code precisava ser escaneado em toda execução
- Mesmo com sessão salva anteriormente

**Solução:**
- Implementado `launch_persistent_context` do Playwright
- Perfil do navegador salvo em disco
- Recuperação automática da sessão

**Benefícios:**
- ✅ QR code escaneado apenas uma vez
- ✅ Automação completa após primeira configuração
- ✅ Redução de tempo de inicialização
- ✅ Maior confiabilidade

## Referências

- **API Endpoints:** `/api/v1/alerts/rules` - Criar/gerenciar regras
- **Health Check:** `/api/v1/health` - Status do WhatsApp
- **Source Code:** `src/alerts/whatsapp.py` - Cliente WhatsApp API, `src/alerts/whatsapp_web.py` - Cliente Web
- **Documentation Original:** Consolidado de `docs/WHATSAPP_SESSION_PERSISTENCE.md` e seções do README.md
