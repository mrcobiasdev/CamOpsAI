# Design: Clear Processing Queue on Startup

## Current Implementation
Atualmente, a classe `FrameQueue` (em `src/capture/queue.py`) inicializa os contadores como zero no método `__init__`:

```python
def __init__(self, ...):
    ...
    self._processed_count = 0
    self._dropped_count = 0
```

Quando o programa inicia, uma nova instância de `FrameQueue` é criada em `src/main.py:346`:
```python
frame_queue = FrameQueue(processor=process_frame, num_workers=2)
```

Isso significa que os contadores já são zero ao iniciar, mas o comportamento não é explícito.

## Proposed Changes

### 1. Adicionar método `clear()` em `FrameQueue`

```python
def clear(self):
    """Reseta os contadores da fila de processamento."""
    self._processed_count = 0
    self._dropped_count = 0
```

**Rationale**: 
- Fornece uma API clara para resetar os contadores
- Útil para testes e cenários onde o queue precisa ser resetado durante runtime
- Torna a intenção explícita no código

### 2. Chamar `clear()` na inicialização

Em `src/main.py`, após criar o `FrameQueue`:

```python
# Inicializa fila de processamento
frame_queue = FrameQueue(processor=process_frame, num_workers=2)
frame_queue.clear()  # Reseta contadores explicitamente
camera_manager.set_frame_queue(frame_queue)
```

**Rationale**:
- Documenta explicitamente o comportamento desejado
- Garante que mesmo se a implementação interna mudar (ex: se os contadores forem persistidos), eles serão resetados
- Torna o comportamento visível no código de inicialização

## Impact Analysis

### Positive Impact
- Intenção do código mais clara
- API mais útil para testes e runtime
- Comportamento documentado explicitamente

### Negative Impact
- Uma chamada de método adicional (negligenciável)
- Código ligeiramente mais verboso

### Risk Assessment
- **Risk Level**: Baixo
- **Reasoning**: Adição de método simples sem modificar lógica existente

## Alternatives Considered

### Alternative 1: Não fazer nada
- **Pros**: Funciona atualmente, não adiciona código
- **Cons**: Comportamento não explícito, menos claro para manutenção
- **Decision**: Rejeitado - usuário solicitou explicitamente o comportamento

### Alternative 2: Persistir contadores e carregar ao iniciar
- **Pros**: Permite histórico entre reinicializações
- **Cons**: Adiciona complexidade não solicitada
- **Decision**: Rejeitado - fora do escopo

## Implementation Notes

O método `clear()` não precisa ser assíncrono pois apenas reseta variáveis de instância numéricas. A fila interna `asyncio.Queue` já é limpa automaticamente ao criar uma nova instância.
