# Visão Geral do CamOpsAI

## O Que É o CamOpsAI

O CamOpsAI é um sistema de monitoramento inteligente de câmeras IP com análise de vídeo por inteligência artificial. O sistema captura streams de vídeo de câmeras em rede local, processa frames selecionados através de modelos LLM (Large Language Models) para descrever eventos em tempo real, e armazena uma timeline de acontecimentos em banco de dados. O sistema também permite configurar alertas baseados em palavras-chave que são enviados via WhatsApp.

## Problema Solucionado

Monitoramento tradicional de vídeo exige:
- Supervisão humana constante (custosa e impraticável 24/7)
- Análise manual de longas gravações para encontrar eventos
- Dificuldade em identificar padrões ou anomalias
- Ausência de alertas em tempo real

O CamOpsAI automatiza esse processo:
- Detecta movimento automaticamente
- Descreve eventos usando inteligência artificial
- Envia alertas em tempo real via WhatsApp
- Mantém timeline pesquisável de todos os eventos

## Casos de Uso

### Segurança Residencial

- Monitorar entrada principal, quintal, garagem
- Receber alertas quando pessoas forem detectadas
- Revisar eventos por palavra-chave (ex: "intruso", "estranho")

### Segurança Comercial

- Monitorar lojas, escritórios, estacionamentos
- Detectar atividade fora do horário comercial
- Receber alertas para eventos específicos

### Monitoramento de Infraestrutura

- Câmeras em ruas, áreas públicas, instalações industriais
- Detectar veículos ou atividades anormais
- Compatível com múltiplas câmeras simultaneamente

### Testes e Validação

- Usar arquivos de vídeo para validar o pipeline completo
- Testar diferentes parâmetros de detecção de movimento
- Desenvolver sem necessidade de hardware de câmera

## Stack Tecnológica

### Backend

- **Python 3.10+** - Linguagem principal
- **FastAPI** - Framework web assíncrono
- **PostgreSQL 14+** - Banco de dados relacional
- **SQLAlchemy** - ORM assíncrono
- **Alembic** - Migrações de banco de dados

### Processamento de Vídeo

- **OpenCV** - Captura e processamento de frames
- **Algoritmo Híbrido** - Detecção de movimento (pixel difference + background subtraction)

### Inteligência Artificial

- **OpenAI GPT-4V** - Provedor LLM Vision
- **Anthropic Claude Vision** - Provedor LLM Vision
- **Google Gemini Vision** - Provedor LLM Vision

### Notificações

- **WhatsApp Business API** - Modo produção
- **WhatsApp Web + Playwright** - Modo teste

### Ferramentas de Desenvolvimento

- **OpenCode** - Assistente de IA para desenvolvimento
- **OpenSpec** - Workflow de desenvolvimento dirigido por especificações

## Funcionalidades Principais

### 1. Captura de Vídeo

- Conexão com câmeras IP via protocolo RTSP
- Suporte a múltiplas câmeras simultaneamente
- Captura assíncrona com reconexão automática
- Intervalo de captura configurável por câmera
- Suporte a arquivos de vídeo para testes

### 2. Detecção de Movimento

- Algoritmo híbrido (pixel difference + background subtraction)
- Sensitivity presets (LOW/MEDIUM/HIGH)
- Hot-reload de configuração (sem reiniciar aplicação)
- Ferramentas de calibração e visualização
- Reduz custos de API LLM filtrando frames estáticos

### 3. Processamento com IA

- Suporte a múltiplos provedores LLM
- Descrição automática de eventos e atividades
- Extração de palavras-chave estruturada
- Taxa de processamento configurável

### 4. Armazenamento e Timeline

- Banco de dados PostgreSQL para registro de eventos
- Timeline cronológica de acontecimentos por câmera
- Histórico pesquisável por palavras-chave e filtros
- Armazenamento de frames em disco

### 5. Sistema de Alertas

- Definição de regras com palavras-chave
- Suporte a dois modos de envio (API e Web)
- Sessão persistente do WhatsApp Web
- Cooldown configurável para evitar spam
- Níveis de prioridade (low, normal, high)

### 6. API REST

- Endpoints completos para câmeras, eventos e alertas
- Documentação interativa (Swagger UI)
- Health checks e estatísticas
- Suporte para testes via arquivos de vídeo

## Benefícios

### Automação

- Monitoramento 24/7 sem supervisão humana
- Detecção automática de eventos relevantes
- Alertas em tempo real

### Eficiência

- Filtragem de frames irrelevantes via detecção de movimento
- Redução de custos de API LLM
- Timeline pesquisável facilita revisão

### Flexibilidade

- Suporte a múltiplos provedores LLM
- Configuração por câmera
- Sensitivity presets para diferentes cenários

### Facilidade de Uso

- Interface REST completa
- Documentação detalhada
- Ferramentas de calibração
- Modo teste com arquivos de vídeo

## Limitações Conhecidas

- Latência dependente da velocidade da API do LLM
- Custos de API proporcional ao volume de análises
- Qualidade da descrição dependente do modelo LLM utilizado
- WhatsApp Business API requer conta aprovada (produção)
- WhatsApp Web adequado para testes, não alta escala

## Próximos Passos

Ver "Roadmap Futuro" no README para funcionalidades planejadas.

## Referências

- **README.md** - Documentação completa do sistema
- **docs/features/motion-detection.md** - Detecção de movimento detalhada
- **docs/features/whatsapp-notifications.md** - Sistema de alertas
- **docs/guides/troubleshooting.md** - Solução de problemas
