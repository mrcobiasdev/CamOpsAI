# Clear Processing Queue on Startup

## Summary
Adicionar método para limpar explicitamente a fila de processamento (contadores) ao iniciar o programa, garantindo que os contadores de frames processados e descartados iniciem zerados.

## Motivation
Embora a instância de `FrameQueue` seja recriada a cada inicialização do programa (o que já zera os contadores), é importante tornar este comportamento explícito no código através de um método dedicado `clear()`. Isso:

1. Torna a intenção clara no código
2. Fornece um método que pode ser chamado durante o runtime se necessário
3. Facilita testes e manutenção futura
4. Documenta claramente o comportamento esperado

## Scope
- Adicionar método `clear()` na classe `FrameQueue`
- Chamar o método `clear()` explicitamente durante a inicialização do aplicativo
- Não afeta arquivos de frames armazenados em disco
- Não afeta eventos no banco de dados

## Out of Scope
- Persistência da fila entre reinicializações
- Limpeza de arquivos de frames
- Modificação de comportamentos existentes de processamento

## Success Criteria
- [x] Contador `_processed_count` é zero ao iniciar
- [x] Contador `_dropped_count` é zero ao iniciar
- [x] Método `clear()` disponível para reset durante runtime
- [x] Documentação atualizada
- [x] Testes existentes continuam passando
