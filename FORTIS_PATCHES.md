# Fortis patches — ZWCAD-MCP

Alterações sobre o commit `49883a9` (dalingo81/ZWCAD-MCP, 24/07/2026).
Todas as linhas alteradas estão marcadas com `[Fortis]` no código.

Data: 14/11/2026

## 1. Acentos e caracteres especiais (Windows PT-BR)

**Problema:** o código original foi feito para Windows chinês (GBK). No Windows
brasileiro (cp1252), qualquer texto acentuado vindo do desenho quebrava o JSON
de resposta (tempo esgotado), e texto acentuado enviado ao ZWCAD chegava corrompido.

**Correção:**
- LISP → Python: `mcp-write-result` passa o payload e o erro por `mcp-ascii-json`,
  que escreve todo caractere não-ASCII como `\uXXXX`. O arquivo de resposta fica
  100% ASCII.
- Python → LISP (parâmetros): `mcp-json-get-string` agora decodifica `\uXXXX`,
  `\n`, `\"`, `\\` etc. (`mcp-json-unescape`). Também corrigido: string vazia `""`
  não era lida corretamente.
- `execute_lisp`: o Python grava o código só em ASCII, trocando cada caractere
  não-ASCII por `{{U+XXXX}}`; o LISP (`mcp-decode-markers`) restaura com `(chr)`
  antes de executar.

## 2. Leader sem travar

**Problema:** `(command "_.LEADER" ...)` no ZWCAD 2026 tem outra sequência de
prompts; o desenho saía certo, mas o comando ficava esperando e a resposta não voltava.

**Correção:** `mcp-cmd-create-leader` usa ActiveX (`vla-AddMText` + `vla-AddLeader`,
seta `acLineWithArrow`). Altura do texto = `DIMTXT × DIMSCALE`. Texto alinhado à
esquerda ou à direita conforme o último segmento. Retorna `handle` do leader e
`text_handle` do MText.

## 3. Comandos na janela certa

**Problema:** com vários desenhos abertos, os comandos iam para a primeira janela
de desenho encontrada, não necessariamente a ativa.

**Correção:**
- A cada comando, o Python localiza o desenho **ativo** (`WM_MDIGETACTIVE`) e
  envia as teclas para a vista dele. Se não achar a estrutura de janelas, volta
  ao comportamento original.
- Nova operação `system set_target {drawing}`: fixa um desenho alvo. O servidor
  ativa a aba desse desenho antes de enviar e grava `expect_dwg` no comando.
- Trava no LISP: se `expect_dwg` não bater com `DWGNAME`, o comando é recusado
  sem executar nada ("Wrong drawing ...").
- Nova operação `system list_windows`: diagnóstico das janelas de desenho abertas.
- A janela principal do ZWCAD é procurada de novo se o ZWCAD for reaberto.

## 4. Sem roubar foco e sem o retângulo branco

**Problema:** o disparo por teclas fazia aparecer a caixa da Entrada Dinâmica
(DYNMODE) perto do cursor, e o ZWCAD às vezes vinha para a frente enquanto o
usuário trabalhava em outro programa.

**Correção:**
- Disparo pela API COM do ZWCAD (`ZWCAD.Application` → `ActiveDocument.SendCommand`),
  sem teclas. Roda numa thread com espera máxima de 3 s, para um ZWCAD ocupado
  não travar o servidor.
- As teclas (com ESC antes) ficam como reserva: se o COM falhar ou se a primeira
  tentativa não tiver resposta em 2 s.
- Guarda de foco: se o ZWCAD tomar a frente enquanto o usuário está em outro
  programa, o servidor devolve o foco para a janela anterior. Se o usuário já
  estava no ZWCAD, nada é mexido.
- `ZWCAD_MCP_TRIGGER=keys` no `env` volta ao disparo original só por teclas.

## Arquivos alterados

- `lisp-code/zwcad_mcp_dispatch.lsp`
- `src/zwcad_mcp/backends/file_ipc.py`
- `src/zwcad_mcp/server.py`
- `tests/test_fortis_patch.py` (novo)

## Testes

- Suíte original do projeto: 123 testes passando.
- Funções LISP novas testadas ao vivo no ZWCAD 2026 (acentos, ≥, aspas, barra,
  string vazia, marcadores, nome do desenho).
- Leader via ActiveX testado ao vivo no ZWCAD 2026.
- Janela certa testada ao vivo com 2 desenhos abertos (alvo inativo ativado e
  comando executado nele; trava recusou alvo inexistente).
- Disparo por COM testado ao vivo: nenhuma janela pisca e o foco fica no programa em uso.
- 5 testes novos em `tests/test_fortis_patch.py` (128 no total).
