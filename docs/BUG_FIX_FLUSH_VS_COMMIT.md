# Bug Fix: SQLAlchemy flush() vs commit()

## Problema Identificado

O método `update()` e outros métodos em `repository.py` estavam usando `flush()` em vez de `commit()`.

### O Que Acontecia?

```python
# Código ANTES (INCORRETO)
await self.session.flush()  # ❌ Apenas envia SQL, não faz commit!
```

**Flush vs Commit:**
- `flush()`: Envia o SQL para o driver do banco, mas **NÃO faz commit** da transação
- `commit()`: Envia o SQL **E faz commit** da transação

**Resultado:** As mudanças nunca eram persistidas no banco!

## Arquivo Corrigido

**`src/storage/repository.py`**

### Todas as 9 ocorrências corrigidas:

| Linha | Método                      | Descrição                          |
|--------|------------------------------|-------------------------------------|
| 51     | `create()`                   | Cria nova câmera             |
| 117    | `update()`                   | Atualiza câmera             |
| 126    | `update()`                   | Atualiza câmera             |
| 159    | `update_decoder_stats()`       | Atualiza estatísticas          |
| 257    | `create_rule()`              | Cria regra de alerta        |
| 322    | `update_rule()`              | Atualiza regra de alerta        |
| 331    | `update_rule()`              | Atualiza regra de alerta        |
| 353    | `delete_rule()`              | Remove regra de alerta        |
| 397    | `create_log()`               | Cria log de alerta          |

### Comando Aplicado

```bash
# Substituiu todos os flush() por commit()
sed -i 's/await self\.session\.flush()/await self.session.commit()/g' repository.py
```

## Como Testar

### 1. Verifique se o problema está corrigido

```bash
# Ative o ambiente virtual (se necessário)
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Execute o script
python adjust_threshold.py

# Verifique no banco que o threshold mudou
# Deveria aparecer o NOVO valor
```

### 2. Consulte diretamente no banco (opcional)

```bash
# Conecte ao PostgreSQL
psql -d camopsai

# Consulte o threshold atual
SELECT name, motion_threshold FROM cameras;
```

## Esperado

Após rodar `adjust_threshold.py`:

1. **Banco de dados**: O `motion_threshold` deve ter o **NOVO valor** selecionado
2. **Aplicação em execução**: O grabber deve ser atualizado com hot-reload
3. **Logs**: Deve aparecer "Configuration updated" e "Motion detector reinitialized"

## Se Ainda Não Funcionar

Se o banco ainda mostrar 10.0, verifique:

1. **SQLAlchemy está instalado**: `pip install sqlalchemy`
2. **Venv está ativado**: Confirme que está usando o ambiente virtual correto
3. **Permissões de escrita**: Confirme que o aplicativo tem acesso ao banco
4. **Banco está correto**: Verifique a string de conexão em `.env`

## Status

✅ **Bug identificado**: `flush()` vs `commit()`  
✅ **Fix aplicado**: Todos os 9 casos corrigidos  
✅ **Pronto para testes**: Execute `python adjust_threshold.py`

---

**Nota:** Este bug afetava TODAS as operações de escrita no banco, não apenas o threshold!
