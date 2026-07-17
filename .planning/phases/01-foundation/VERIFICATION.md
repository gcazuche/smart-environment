# Fase 1 — Verificação

Status: **aprovada com ressalvas operacionais; FND-01-01..05 concluídas**.

## Implementação verificada

Foram verificados configuração tipada, CLI somente leitura, logging JSON seguro,
fronteira global de exceções, empacotamento e ambiente reproduzível. O lock principal
não contém OpenCV, modelo facial, cliente Supabase nem dado biométrico.

## Comandos executados

```powershell
uv lock --offline --cache-dir .uv-cache
uv sync --extra dev --locked --offline --cache-dir .uv-cache
.\.venv\Scripts\python.exe -m pytest -q
uv run --python 3.11 --isolated --extra dev --locked --offline `
  --cache-dir .uv-cache python -m pytest -q
.\.venv\Scripts\ruff.exe check app main.py tests
.\.venv\Scripts\ruff.exe format --check app main.py tests
.\.venv\Scripts\mypy.exe app main.py tests
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q app main.py tests
.\.venv\Scripts\python.exe -m app doctor --json
uv build --offline --cache-dir .uv-cache --no-progress
uv --cache-dir .uv-cache pip check --python .\.venv\Scripts\python.exe
$highConfidenceSecretPatterns = (@(
  '-----BEGIN ' + '(RSA |EC |OPENSSH )?' + 'PRIVATE KEY-----',
  'AKIA' + '[0-9A-Z]{16}',
  'sk_' + 'live_[0-9A-Za-z]+',
  'service_' + 'role\s*[=:]\s*[0-9A-Za-z._-]+'
)) -join '|'
rg -n --hidden --glob '!.git/**' --glob '!.venv/**' --glob '!.uv-cache/**' `
  --glob '!dist/**' --glob '!build/**' --glob '!*.egg-info/**' `
  $highConfidenceSecretPatterns .
```

O wheel também foi instalado a partir de `%TEMP%`, fora do checkout, com:

```powershell
$wheel = (Resolve-Path '.\dist\multicam_inteligente-0.1.0-py3-none-any.whl').Path
$cache = (Resolve-Path '.\.uv-cache').Path
Push-Location $env:TEMP
uv run --isolated --python 3.11 --offline --cache-dir $cache `
  --with $wheel multicam version
uv run --isolated --python 3.11 --offline --cache-dir $cache `
  --with $wheel multicam doctor --json
Pop-Location
```

Na busca passiva, a variável representou os quatro padrões efetivamente procurados:
cabeçalho de chave privada PEM (RSA/EC/OpenSSH), access key AWS `AKIA` seguida de 16
caracteres maiúsculos/dígitos, token `sk_live_` e atribuição `service_role`. Exit code
1 do `rg` significou nenhum match no escopo após as exclusões acima. Isso não equivale
a SAST/SCA ou scanner de segredos dedicado.

## Evidências automatizadas

- Python 3.12.13: **28 testes, 28 aprovados**.
- Python 3.11.15 gerenciado pelo `uv`: **28 testes, 28 aprovados**.
- `unittest`: **28/28**; `compileall`: exit code 0.
- Ruff lint e format-check: aprovados em 13 arquivos.
- mypy strict: aprovado em 13 arquivos.
- `uv.lock`: 16 pacotes resolvidos; sync e lock offline aprovados.
- Build reproduzível com `setuptools==83.0.0` e `wheel==0.47.0`: sdist e wheel
  gerados; wheel contém somente `app` e metadados.
- Instalação limpa do wheel: versão `0.1.0`; `doctor` sem falhas e sem depender de
  `tests/` ou `.planning`.
- Compatibilidade do ambiente: 15 pacotes verificados, sem conflito.
- Busca passiva local por quatro famílias de padrões de segredo: nenhum match.
- `doctor --json`, CLI humana, versão, configuração inválida, redaction, correlação,
  rotação, fallback e fronteira fatal aprovados.

## Erros corrigidos

- O capturador do pytest adicionava um handler ao logger reservado; a configuração
  agora destaca handlers externos sem fechá-los e mantém `propagate=False`, evitando
  encaminhar exceções brutas. Nomes fora de `multicam`/`multicam.*` são recusados antes
  de tocar handlers do host.
- A anotação de `_SecureRotatingFileHandler._open` foi ajustada para `TextIOWrapper`.
- O falso positivo S105 de `CheckStatus.PASS` recebeu supressão local justificada.
- Imports/formatação foram normalizados pelo Ruff.
- O cache do pytest foi desativado porque a troca de identidade entre sandbox e
  usuário Windows produzia ACL incompatível em `.pytest_cache`.
- Logging em arquivo no Windows agora falha fechado: não cria diretório/arquivo e usa
  somente stderr até existir um adaptador DACL validado.

Detalhes de causa e regressão estão em
`.planning/debugging/2026-07-17-fnd01-quality-gates.md`.

## Smoke autorizado da primeira câmera

Em 2026-07-17 foi executado um spike diagnóstico efêmero com
`opencv-python-headless==4.13.0.92`, índice 0 e timeout rígido de oito segundos:

- câmera PnP observada: `USB2.0 HD UVC WebCam`;
- MSMF: não abriu; fallback DirectShow: abriu;
- um frame válido em memória: 640×480, três canais, `uint8`;
- duração: 2.247 ms; array recebido sobrescrito com zeros best-effort e `release()`
  executado, sem garantia sobre cópias internas do driver;
- nenhum preview, hash, arquivo, modelo facial, reconhecimento ou upload;
- imagens/arquivos em `data/`: 5 antes, 5 depois, **0 novos**.

A primeira invocação do wrapper falhou com `NameError` antes de abrir a câmera por
perda de aspas na passagem PowerShell → Python. A passagem foi corrigida com Base64 e
o teste foi repetido com sucesso. O spike confirma o hardware inicial, mas não conclui
CAM-007 nem antecipa a implementação de captura da Fase 4.

## Ressalvas não bloqueantes

- O arquivo de log persistente continua desabilitado no Windows; DACL, rotação real e
  diretório em `%LOCALAPPDATA%` serão validados antes de uso comercial.
- OpenCV ainda não pertence ao ambiente da aplicação; entra apenas na Fase 4 após
  fonte simulada e testes de ciclo de vida.
- Nenhum GPU, modelo facial, PostgreSQL/Supabase, rede externa ou GUI foi exercitado.
- Retenção, base legal, região/plano do Supabase, escala e licença dos pesos continuam
  abertos e bloqueiam biometria comercial real.

## Resultado final

FND-01-05 e a Fase 1 estão concluídas. TEST-001 e o baseline de SEC-001 foram
atendidos. PRIV-001 foi atendido como gate negativo: nenhuma biometria real pode operar
enquanto finalidade detalhada, responsáveis, aviso e base legal estiverem abertos.
SEC-007 permanece em andamento porque novas camadas ainda deverão integrar o mesmo
contrato e arquivo persistente no Windows segue proibido até o gate DACL.
