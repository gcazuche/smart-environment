# Estratégia de testes

## Princípios

- Testar regra de negócio sem câmera, rede, GUI ou modelo real.
- Usar câmera simulada determinística e relógio/UUID injetáveis.
- Separar unitário, integração, contrato, desempenho, segurança e hardware manual.
- Nunca usar rostos reais no repositório; fixtures sintéticas/licenciadas e autorizadas.
- Registrar comando, ambiente, resultado e lacunas em `VERIFICATION.md`.

## Pirâmide e escopo

| Tipo | Cobertura planejada |
|---|---|
| Unitário | configuração, filas, limiar, deduplicação, permissões, retenção |
| Integração | Supabase/PostgreSQL/pgvector, Storage privado, Alembic, filesystem e fila offline |
| API | autenticação, autorização, validação, paginação, idempotência |
| Interface | modelos/view-models, sinais e smoke test Qt offscreen |
| Câmeras | fonte simulada, webcam integrada, arquivo, ESP32 simulado, desconexão/reconexão; hardware manual |
| Reconhecimento | conhecidos/desconhecidos, limiar, margem, falso positivo/negativo |
| Sincronização | offline, retry, ordem, conflito e duplicação |
| Carga | múltiplas fontes, filas limitadas, CPU/RAM, latência e descarte |
| Segurança | SAST, SCA, secrets, RBAC, uploads, brute force, logs |
| Encerramento | liberação de câmera, workers, transações e fila |

## Comandos padrão

```powershell
python -m unittest discover -s tests -v
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy app tests
python -m compileall -q app main.py
python -m app doctor --json
```

Nesta primeira fase, somente `unittest`, `compileall` e o smoke test não requerem
downloads. Pytest/Ruff/mypy são gates assim que o ambiente de desenvolvimento for
instalado.

## Critérios para reconhecimento

- Conjunto autorizado separado em cadastro, calibração e teste.
- Métricas por grupo relevante e condições de câmera/iluminação.
- Reportar FAR/FMR, FRR/FNMR e curvas por limiar; não apenas “acurácia”.
- Teste negativo deve demonstrar que o melhor candidato abaixo do limiar é desconhecido.
- Mudança de modelo invalida comparação direta e exige re-embedding/calibração.

## Testes manuais obrigatórios

- Descoberta/liberação de cada modelo de câmera real.
- RTSP interrompido e retomado.
- CPU e cada configuração GPU suportada.
- Cadastro guiado com consentimento e descarte de imagem rejeitada.
- Tela cheia/grade e encerramento da GUI.
- Backup e restauração em ambiente isolado.

Hardware real permanece pendente até o usuário executar e fornecer evidências.
