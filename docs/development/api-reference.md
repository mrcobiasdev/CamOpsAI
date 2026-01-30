# Referência da API REST

## Visão Geral

O CamOpsAI expõe uma API REST completa via FastAPI. A documentação interativa (Swagger UI) está disponível em `http://localhost:8000/docs` quando a aplicação está rodando.

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### Sistema

#### Health Check

Verifica se o sistema está operacional.

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "whatsapp_authenticated": true,
  "database_connected": true,
  "active_cameras": 2
}
```

#### Estatísticas

Retorna estatísticas agregadas do sistema.

```http
GET /api/v1/stats
```

**Response:**
```json
{
  "cameras": {
    "total": 5,
    "active": 2,
    "stopped": 3
  },
  "frames": {
    "captured": 1234,
    "processed": 567,
    "discarded": 667,
    "motion_detection_rate": 45.9
  },
  "decoder": {
    "total_errors": 15,
    "avg_error_rate": 1.2
  },
  "alerts": {
    "sent": 23,
    "failed": 2,
    "success_rate": 92.0
  }
}
```

### Câmeras

#### Listar Câmeras

Retorna todas as câmeras cadastradas.

```http
GET /api/v1/cameras
```

**Query Parameters:**
- `enabled` (optional): `true` ou `false` - Filtra por status

**Response:**
```json
[
  {
    "id": "d3002080-1234-5678-9abc-123456789012",
    "name": "Entrada Principal",
    "url": "rtsp://admin:senha@192.168.1.100:554/stream",
    "source_type": "rtsp",
    "enabled": true,
    "frame_interval": 10,
    "motion_detection_enabled": true,
    "motion_threshold": 5.0,
    "motion_sensitivity": "medium",
    "created_at": "2026-01-01T12:00:00Z",
    "updated_at": "2026-01-15T14:30:00Z"
  }
]
```

#### Criar Câmera

Cria uma nova câmera.

```http
POST /api/v1/cameras
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Entrada Principal",
  "url": "rtsp://admin:senha@192.168.1.100:554/stream",
  "source_type": "rtsp",
  "enabled": true,
  "frame_interval": 10,
  "motion_detection_enabled": true,
  "motion_threshold": 5.0,
  "motion_sensitivity": "medium"
}
```

**Response:** 201 Created
```json
{
  "id": "d3002080-1234-5678-9abc-123456789012",
  "name": "Entrada Principal",
  "url": "rtsp://admin:senha@192.168.1.100:554/stream",
  "source_type": "rtsp",
  "enabled": true,
  "frame_interval": 10,
  "motion_detection_enabled": true,
  "motion_threshold": 5.0,
  "motion_sensitivity": "medium",
  "created_at": "2026-01-30T10:00:00Z",
  "updated_at": "2026-01-30T10:00:00Z"
}
```

#### Detalhes da Câmera

Retorna detalhes de uma câmera específica.

```http
GET /api/v1/cameras/{camera_id}
```

#### Atualizar Câmera

Atualiza configuração de uma câmera.

```http
PATCH /api/v1/cameras/{camera_id}
Content-Type: application/json
```

**Request Body (todos os campos opcionais):**
```json
{
  "name": "Entrada Principal (Atualizado)",
  "frame_interval": 15,
  "motion_threshold": 10.0,
  "motion_sensitivity": "high"
}
```

**Response:** 200 OK

#### Deletar Câmera

Remove uma câmera e para captura se ativa.

```http
DELETE /api/v1/cameras/{camera_id}
```

**Response:** 204 No Content

#### Iniciar Captura

Inicia captura de uma câmera.

```http
POST /api/v1/cameras/{camera_id}/start
```

**Response:** 200 OK
```json
{
  "status": "capturing",
  "message": "Camera started successfully"
}
```

#### Parar Captura

Para captura de uma câmera.

```http
POST /api/v1/cameras/{camera_id}/stop
```

**Response:** 200 OK
```json
{
  "status": "stopped",
  "message": "Camera stopped successfully"
}
```

#### Status da Câmera

Retorna status atual e estatísticas da câmera.

```http
GET /api/v1/cameras/{camera_id}/status
```

**Response:**
```json
{
  "status": "capturing",
  "enabled": true,
  "frame_interval": 10,
  "motion_detection_enabled": true,
  "motion_threshold": 5.0,
  "motion_sensitivity": "medium",
  "frames_captured": 1234,
  "frames_processed": 567,
  "frames_sent": 500,
  "motion_detection_rate": 45.9,
  "decoder_total_errors": 10,
  "decoder_avg_error_rate": 0.8,
  "current_frame_number": 150,
  "total_frames": 900,
  "progress_percentage": 16.67,
  "source_type": "rtsp"
}
```

**Nota:** Campos `current_frame_number`, `total_frames`, e `progress_percentage` são presentes apenas para `source_type=video_file`.

### Eventos

#### Listar Eventos

Retorna eventos com filtros opcionais.

```http
GET /api/v1/events
```

**Query Parameters:**
- `camera_id` (optional): Filtrar por câmera
- `start_date` (optional): Data inicial (ISO 8601)
- `end_date` (optional): Data final (ISO 8601)
- `limit` (optional): Máximo de resultados (default: 100)
- `offset` (optional): Pular N resultados (para paginação)

**Response:**
```json
[
  {
    "id": "e4003190-2345-6789-abcd-234567890123",
    "camera_id": "d3002080-1234-5678-9abc-123456789012",
    "timestamp": "2026-01-30T12:15:30Z",
    "description": "Uma pessoa caminhando pela entrada principal",
    "keywords": ["pessoa", "entrada", "caminhando"],
    "frame_path": "./frames/camera_d300..._e400..._1706608530.jpg",
    "confidence": 0.95,
    "llm_provider": "openai",
    "llm_model": "gpt-4o",
    "processing_time_ms": 2500
  }
]
```

#### Timeline de Eventos

Retorna timeline cronológica por câmera.

```http
GET /api/v1/events/timeline
```

**Query Parameters:**
- `camera_id` (optional): Filtrar por câmera
- `limit` (optional): Máximo de resultados (default: 50)

**Response:** Mesmo formato que `/api/v1/events`

#### Detalhes do Evento

Retorna detalhes de um evento específico.

```http
GET /api/v1/events/{event_id}
```

**Response:** Mesmo formato que `/api/v1/events`

#### Download do Frame

Baixa o frame do evento.

```http
GET /api/v1/events/{event_id}/frame
```

**Response:** Arquivo de imagem (JPEG)

#### Buscar por Keywords

Busca eventos que contêm keywords específicas.

```http
GET /api/v1/events/search/keywords
```

**Query Parameters:**
- `q` (required): Keywords para buscar (separadas por espaço ou vírgula)
- `camera_id` (optional): Filtrar por câmera
- `limit` (optional): Máximo de resultados (default: 100)

**Response:** Mesmo formato que `/api/v1/events`

### Alertas

#### Listar Regras de Alerta

Retorna todas as regras de alerta.

```http
GET /api/v1/alerts/rules
```

**Response:**
```json
[
  {
    "id": "a5004290-3456-789a-bcde-345678901234",
    "name": "Detecção de Pessoas",
    "keywords": ["pessoa", "pessoas", "indivíduo", "homem", "mulher"],
    "camera_ids": [],
    "phone_numbers": ["5511999999999"],
    "enabled": true,
    "priority": "normal",
    "cooldown_seconds": 300,
    "created_at": "2026-01-20T10:00:00Z",
    "updated_at": "2026-01-20T10:00:00Z"
  }
]
```

#### Criar Regra de Alerta

Cria uma nova regra de alerta.

```http
POST /api/v1/alerts/rules
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Detecção de Pessoas",
  "keywords": ["pessoa", "pessoas"],
  "camera_ids": [],
  "phone_numbers": ["5511999999999"],
  "enabled": true,
  "priority": "normal",
  "cooldown_seconds": 300
}
```

**Response:** 201 Created

#### Detalhes da Regra

Retorna detalhes de uma regra específica.

```http
GET /api/v1/alerts/rules/{rule_id}
```

#### Atualizar Regra

Atualiza configuração de uma regra.

```http
PATCH /api/v1/alerts/rules/{rule_id}
Content-Type: application/json
```

**Request Body (todos os campos opcionais):**
```json
{
  "name": "Detecção de Pessoas (Atualizado)",
  "enabled": false
}
```

**Response:** 200 OK

#### Deletar Regra

Remove uma regra de alerta.

```http
DELETE /api/v1/alerts/rules/{rule_id}
```

**Response:** 204 No Content

#### Histórico de Alertas

Retorna log de alertas enviados.

```http
GET /api/v1/alerts/logs
```

**Query Parameters:**
- `rule_id` (optional): Filtrar por regra
- `start_date` (optional): Data inicial
- `end_date` (optional): Data final
- `status` (optional): `pending`, `sent`, ou `failed`
- `limit` (optional): Máximo de resultados (default: 100)

**Response:**
```json
[
  {
    "id": "l6005390-4567-89ab-cdef-456789012345",
    "event_id": "e4003190-2345-6789-abcd-234567890123",
    "alert_rule_id": "a5004290-3456-789a-bcde-345678901234",
    "keywords_matched": ["pessoa"],
    "sent_to": ["5511999999999"],
    "sent_at": "2026-01-30T12:16:00Z",
    "status": "sent",
    "error_message": null
  }
]
```

#### Testar Regra

Envia alerta de teste para uma regra.

```http
POST /api/v1/alerts/test/{rule_id}
```

**Response:** 200 OK
```json
{
  "status": "sent",
  "sent_to": ["5511999999999"],
  "message": "Test alert sent successfully"
}
```

## Códigos de Status

| Código | Significado |
|--------|-------------|
| 200 | OK - Requisição bem-sucedida |
| 201 | Created - Recurso criado |
| 204 | No Content - Recurso deletado ou atualizado sem conteúdo |
| 400 | Bad Request - Parâmetros inválidos |
| 404 | Not Found - Recurso não encontrado |
| 422 | Unprocessable Entity - Validação falhou |
| 500 | Internal Server Error - Erro no servidor |

## Formatos de Data

Todas as datas seguem ISO 8601:

```
2026-01-30T12:15:30Z
YYYY-MM-DDTHH:MM:SSZ
```

## Autenticação

Atualmente, a API não exige autenticação. Para produção, considere implementar:

- JWT tokens
- OAuth2
- API keys

## Rate Limiting

Atualmente, não há rate limiting. Para produção, considere implementar:

- Limites por endpoint
- Limites por IP
- Limites por usuário

## Exemplos de Uso

### Criar Câmera

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

### Criar Regra de Alerta

```bash
curl -X POST "http://localhost:8000/api/v1/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Detecção de Pessoas",
    "keywords": ["pessoa", "pessoas"],
    "phone_numbers": ["5511999999999"],
    "enabled": true,
    "priority": "normal",
    "cooldown_seconds": 300
  }'
```

### Consultar Timeline

```bash
curl "http://localhost:8000/api/v1/events/timeline?limit=50"
```

### Buscar por Keywords

```bash
curl "http://localhost:8000/api/v1/events/search/keywords?q=pessoa+entrada"
```

## Referências

- **Swagger UI:** `http://localhost:8000/docs` - Documentação interativa
- **Source Code:** `src/api/routes/` - Implementação dos endpoints
- **Schemas:** `src/api/schemas.py` - Pydantic schemas
