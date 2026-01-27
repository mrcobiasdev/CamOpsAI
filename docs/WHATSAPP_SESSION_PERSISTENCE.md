# Melhorias na Persistência de Sessão do WhatsApp Web

## Problema Original
A funcionalidade de envio de mensagens via WhatsApp Web exigia escanear o QR code toda vez que o navegador era fechado e reiniciado, mesmo que a sessão tivesse sido salva anteriormente.

## Solução Implementada

### 1. Uso de Contexto Persistente (`launch_persistent_context`)
A principal mudança foi a implementação de um contexto persistente do Playwright usando `launch_persistent_context`. Isso permite que:

- O perfil do navegador (incluindo cookies, localStorage, sessionStorage) seja salvo no disco
- A sessão seja recuperada automaticamente nas próximas execuções
- O QR code precise ser escaneado apenas uma vez

**Local do perfil persistente:** `{WHATSAPP_SESSION_DIR}/browser_profile/`

### 2. Melhorias na Lógica de Autenticação
O código agora:

- Verifica se já está na página do WhatsApp Web antes de navegar
- Aguarda menos tempo para carregar a sessão (15s → 5s)
- Usa múltiplos seletores para verificar se a sessão está ativa
- Salva a sessão após cada mensagem enviada

### 3. Backup de Sessão
Além do contexto persistente, o código também salva um backup da sessão em `state.json` para compatibilidade.

## Como Funciona

### Primeira Execução
1. O navegador é iniciado com um contexto persistente
2. O QR code é exibido no navegador
3. O usuário escaneia o QR code com o WhatsApp
4. A sessão é autenticada e salva automaticamente

### Execuções Posteriores
1. O navegador é iniciado com o contexto persistente anterior
2. A sessão é carregada automaticamente dos arquivos salvos
3. O WhatsApp Web inicia diretamente autenticado
4. **Nenhum QR code é exibido**

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

## Testando a Funcionalidade

Use o script de teste incluído:

```bash
python test_session_persistence.py
```

O script:
1. Inicia o WhatsApp e pede para escanear o QR code
2. Envia uma mensagem de teste (Execução 1)
3. Fecha o navegador
4. Reabre o navegador com o mesmo perfil
5. Envia outra mensagem (Execução 2)
6. Se a segunda mensagem for enviada sem pedir QR code, a persistência está funcionando!

## Troubleshooting

### QR code aparece novamente após reiniciar
Se o QR code continuar aparecendo:

1. **Verifique o diretório de sessão:**
   ```bash
   ls -la sessions/whatsapp/browser_profile/
   ```
   
2. **Verifique se há permissões de escrita:**
   ```bash
   chmod -R 755 sessions/whatsapp/
   ```

3. **Exclua o perfil e comece do zero:**
   ```bash
   rm -rf sessions/whatsapp/browser_profile/
   ```

4. **Verifique o log para erros:**
   - O log indicará se o perfil persistente está sendo usado
   - Verifique por erros de permissão ou disco cheio

### Sessão expira após alguns dias
O WhatsApp Web tem um tempo de expiração natural para sessões:
- Normalmente, a sessão expira após 14-30 dias
- Após a expiração, você precisará escanear o QR code novamente
- Isso é um comportamento normal do WhatsApp Web e não um bug

### Erro ao carregar contexto persistente
Se ocorrer erro ao carregar o contexto persistente, o código automaticamente:
- Fallback para o modo normal (não persistente)
- Tenta carregar a sessão do arquivo `state.json`
- Cria uma nova sessão se necessário

## Benefícios

✅ **QR code escaneado apenas uma vez**
✅ **Automação completa após primeira configuração**
✅ **Redução de tempo de inicialização**
✅ **Maior confiabilidade no envio de alertas**
✅ **Backup automático da sessão**

## Código Modificado

- `src/alerts/whatsapp_web.py`:
  - Adicionado `launch_persistent_context`
  - Melhorada lógica de autenticação
  - Adicionado método `_save_session()`
  - Melhorado método `close()`
