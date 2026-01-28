# Tasks

## Implementation

- [x] **1. Adicionar método `clear()` na classe FrameQueue**
   - [x] Implementar método que zera `_processed_count` e `_dropped_count`
   - [x] Adicionar docstring explicativo
   - [x] Não modificar outros atributos (queue, workers, running)

- [x] **2. Chamar `clear()` explicitamente na inicialização**
   - [x] Modificar `src/main.py` para chamar `frame_queue.clear()` após criar o FrameQueue
   - [x] Adicionar comentário explicando o propósito

- [x] **3. Adicionar testes para o método `clear()`**
   - [x] Testar que `clear()` zera os contadores
   - [x] Testar que `clear()` não afeta conteúdo da fila
   - [x] Testar que `clear()` não afeta status dos workers

- [x] **4. Atualizar documentação**
   - [x] Documentar o método `clear()` no docstring da classe FrameQueue
   - [x] Adicionar comentário no código de inicialização explicando o comportamento

## Validation

- [x] **5. Verificar que testes existentes continuam passando**
   - [x] Executar `pytest tests/` para garantir regressão
   - [x] Verificar que não há erros de tipo

- [x] **6. Validar manualmente o comportamento**
   - [x] Iniciar a aplicação e verificar que contadores iniciam em 0
   - [x] Processar alguns frames e verificar que contadores incrementam
   - [x] Reiniciar a aplicação e verificar que contadores voltam a 0

## Dependencies
- Task 1 deve ser completado antes da Task 2
- Task 2 deve ser completado antes da Task 5
- Task 3 pode ser feito em paralelo com Task 1 e 2
- Task 4 pode ser feito em paralelo com Task 1 e 2
