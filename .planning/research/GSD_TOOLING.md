# Ferramenta GSD

## Situação em 2026-07-17

Há uma implementação pública do fluxo Get Shit Done com suporte declarado ao Codex:
<https://github.com/gsd-build/get-shit-done>. O README oficial documenta instalação
interativa via:

```powershell
npx get-shit-done-cc@latest
```

Instalação local e específica para Codex, conforme a mesma fonte:

```powershell
npx get-shit-done-cc@latest --codex --local
```

Após reiniciar o Codex, a documentação orienta verificar com `$gsd-help` e iniciar
um projeto com `$gsd-new-project` (a grafia exata pode mudar; conferir a referência de
comandos da versão instalada).

## Decisão desta sessão

O instalador **não foi executado**. Já existe uma skill GSD DevSecOps disponível e o
fluxo está sendo reproduzido em `.planning`. Executar `npx ...@latest` baixa e executa
código remoto; antes de usar em ambiente sensível, revisar repositório/release, fixar
uma versão aprovada e preferir instalação local. Não usar modos que desabilitem
permissões/sandbox neste projeto biométrico.

## Fluxo manual equivalente

1. Ler `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `DECISIONS.md`.
2. Discutir e pesquisar a fase.
3. Executar uma tarefa atômica de `PLAN.md`.
4. Rodar os comandos de validação e registrar evidências.
5. Atualizar `VERIFICATION.md`, `SUMMARY.md`, `STATE.md` e `CHANGELOG.md`.
6. Fazer commit atômico somente após revisão e quando autorizado.

## Fonte primária

- Repositório e instruções oficiais: <https://github.com/gsd-build/get-shit-done>
- Referência de comandos: <https://github.com/gsd-build/get-shit-done/blob/main/docs/COMMANDS.md>
