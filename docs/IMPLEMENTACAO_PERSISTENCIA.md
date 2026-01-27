# Implementação de Persistência de Sessão do WhatsApp Web

## Resumo da Implementação

### Problema Original
A funcionalidade de envio de mensagens via WhatsApp Web exigia escanear o QR code **em toda execução**, mesmo que a sessão tivesse sido salva anteriormente.

### Solução Implementada
Implementado **contexto persistente** do Playwright (`launch_persistent_context`), que salva todo o perfil do navegador no disco, permitindo recuperação automática da sessão.

**Resultado**: QR code precisa ser escaneado apenas **uma vez**!

---

## Arquivos Modificados

### 1. `src/alerts/whatsapp_web.py`
**Principais mudanças:**

- ✅ Implementado uso de `launch_persistent_context` para persistência de sessão
- ✅ Adicionado `_user_data_dir` para armazenar perfil do navegador
- ✅ Melhorado método `initialize()` com lógica de contexto persistente
- ✅ Otimizado método `_authenticate()`:
  - Verifica se já está na página do WhatsApp Web
  - Reduz tempo de espera (15s → 5s)
  - Usa múltiplos seletores para verificação
- ✅ Adicionado método `_save_session()` para salvamento automático
- ✅ Atualizado método `close()` para lidar com contexto persistente
- ✅ Adicionado salvamento após cada mensagem enviada

**Código-chave:**
```python
# Linha 55: launch_persistent_context
self._context = await self._playwright.chromium.launch_persistent_context(
    user_data_dir=str(self._user_data_dir),
    headless=self.headless,
    # ...
)
```

### 2. `README.md`
- Atualizada seção "Modo Web" com detalhes sobre persistência
- Adicionada informação sobre expiração de sessão (14-30 dias)
- Adicionada instrução para testar persistência

### 3. `CHANGELOG.md`
- Criado changelog documentando mudanças
- Categorizado como "Adicionado" e "Corrigido"

---

## Arquivos Criados

### 1. `docs/WHATSAPP_SESSION_PERSISTENCE.md`
Documentação técnica completa com:
- Explicação da solução implementada
- Como funciona a persistência
- Configuração necessária
- Script de teste
- Troubleshooting
- Benefícios

### 2. `tests/test_session_persistence.py`
Script de teste para validar persistência:
- Envia mensagem na primeira execução
- Fecha navegador
- Reabre navegador
- Envia segunda mensagem (sem QR code)
- Reporta sucesso ou falha

**Como usar:**
```bash
python tests/test_session_persistence.py
```

### 3. `CHANGELOG.md`
Registro histórico de mudanças do projeto

---

## Como Funciona

### Primeira Execução
1. Navegador iniciado com contexto persistente
2. QR code exibido
3. Usuário escaneia QR code
4. Sessão autenticada e salva em `{WHATSAPP_SESSION_DIR}/browser_profile/`

### Execuções Posteriores
1. Navegador iniciado com contexto persistente anterior
2. Sessão carregada automaticamente dos arquivos salvos
3. WhatsApp Web inicia autenticado
4. **QR code não é exibido**

---

## Estrutura de Diretórios Após Implementação

```
CamOpsAI/
├── sessions/
│   └── whatsapp/
│       ├── browser_profile/          # Perfil persistente (NOVO)
│       │   ├── cookies/
│       │   ├── localStorage/
│       │   ├── sessionStorage/
│       │   └── ...
│       └── state.json                 # Backup da sessão
├── docs/
│   └── WHATSAPP_SESSION_PERSISTENCE.md  # Documentação técnica (NOVO)
├── tests/
│   └── test_session_persistence.py      # Script de teste (NOVO)
├── src/
│   └── alerts/
│       └── whatsapp_web.py               # Modificado
├── CHANGELOG.md                         # Criado (NOVO)
└── README.md                            # Atualizado
```

---

## Configuração

### Variáveis de Ambiente (.env)
```env
# Diretório para salvar a sessão do WhatsApp
WHATSAPP_SESSION_DIR=./sessions/whatsapp/

# Executar em modo headless (true = sem visualizar navegador)
WHATSAPP_HEADLESS=false  # Use false na primeira configuração
```

### Importante
- **Primeira execução:** Configure `WHATSAPP_HEADLESS=false` para visualizar e escanear o QR code
- **Execuções posteriores:** Pode usar `WHATSAPP_HEADLESS=true` para executar em segundo plano

---

## Testando

### Teste Manual
```bash
# 1. Configure headless=false
WHATSAPP_HEADLESS=false

# 2. Inicie a aplicação
python src/main.py

# 3. Escaneie o QR code

# 4. Feche a aplicação (Ctrl+C)

# 5. Inicie novamente - NÃO precisa escanear QR code!
python src/main.py
```

### Teste Automatizado
```bash
python tests/test_session_persistence.py
```

---

## Troubleshooting

### QR code aparece novamente
Se o QR code continuar aparecendo:
1. Exclua o perfil: `rm -rf sessions/whatsapp/browser_profile/`
2. Reinicie e escaneie novamente
3. Verifique permissões de escrita no diretório

### Sessão expira após alguns dias
Comportamento normal do WhatsApp Web (14-30 dias). Escanee o QR code novamente.

### Verifique os logs
```bash
# O log indicará se o perfil persistente está sendo usado
# Procure por: "Usando perfil persistente em: ..."
```

---

## Benefícios

✅ **QR code escaneado apenas uma vez**
✅ **Automação completa após primeira configuração**
✅ **Redução de tempo de inicialização**
✅ **Maior confiabilidade no envio de alertas**
✅ **Backup automático da sessão**
✅ **Ambiente isolado (não conflita com outras sessões)**

---

## Próximos Passos

1. **Monitore a expiração de sessão:** Implementar notificação quando a sessão estiver próxima de expirar
2. **Refresh automático:** Implementar renovação automática antes da expiração
3. **Monitoramento de saúde:** Endpoint para verificar se a sessão ainda é válida

---

## Suporte

Para mais informações, consulte:
- `docs/WHATSAPP_SESSION_PERSISTENCE.md` - Documentação técnica detalhada
- `CHANGELOG.md` - Histórico de mudanças
- `README.md` - Documentação geral do projeto
