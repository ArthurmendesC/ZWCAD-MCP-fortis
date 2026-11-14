# ZWCAD-MCP-fortis

[English](README.md) · **Português** · [中文 (original)](README.zh-CN.md)

Servidor MCP que permite a um cliente de IA (Claude Desktop, Cursor etc.) ler e desenhar no **ZWCAD** sem aparecer nada na tela, enquanto você trabalha em outro programa.

Este é um fork de [dalingo81/ZWCAD-MCP](https://github.com/dalingo81/ZWCAD-MCP) (commit `49883a9`), que por sua vez se baseia em [puran-water/autocad-mcp](https://github.com/puran-water/autocad-mcp). O original foi feito para Windows chinês. Este fork corrige o funcionamento em Windows de outros idiomas (português, inglês, espanhol…) e tira toda interferência na tela. Todas as alterações estão marcadas com `[Fortis]` no código e descritas em [FORTIS_PATCHES.md](FORTIS_PATCHES.md).

Testado no ZWCAD 2026 em Windows em português.

## O que muda em relação ao original

| Problema no original | Neste fork |
| --- | --- |
| Texto acentuado lido do desenho quebrava a resposta (tempo esgotado) | Acentos e símbolos (ç, ã, é, ≥, Ø) vão e voltam certos, em qualquer página de código do Windows |
| Código do `execute_lisp` gravado em GBK: acentos corrompidos fora da China | Código gravado só em ASCII, com os caracteres restaurados dentro do ZWCAD |
| `create_leader` usava o comando LEADER, que no ZWCAD 2026 deixa o comando esperando | Leader criado via ActiveX; devolve o handle do leader e do texto |
| Com vários desenhos abertos, o comando ia para a primeira janela encontrada | Vai para o desenho ativo; `set_target` fixa um desenho e o LISP recusa rodar em outro |
| Disparo por teclas: caixa da Entrada Dinâmica perto do cursor e ZWCAD vindo para a frente | Disparo pela API COM do ZWCAD, sem teclas; o foco fica onde você está |
| ZWCAD reaberto exigia reiniciar o servidor | O servidor reencontra a janela sozinho |
| String vazia `""` nos parâmetros não era lida | Corrigido |

## Requisitos

- Windows 10/11.
- ZWCAD 2020 ou mais novo, com AutoLISP (Profissional ou Standard). Testado no 2026.
- Python 3.10 ou mais novo, **versão Windows** (não a do WSL).
- Git (opcional; dá para baixar o ZIP).

## Instalação

### 1. Conferir o Python

No PowerShell:

```powershell
python --version
```

Se não aparecer 3.10 ou superior, instale pelo python.org marcando **"Add python.exe to PATH"**. Feche e reabra o PowerShell depois.

### 2. Baixar e instalar o servidor

Escolha uma pasta para os seus servidores MCP. O exemplo usa `C:\mcp`:

```powershell
mkdir C:\mcp; cd C:\mcp
git clone https://github.com/ArthurmendesC/ZWCAD-MCP-fortis.git ZWCAD-MCP
cd ZWCAD-MCP
python -m venv .venv
.venv\Scripts\pip install -e .
```

O `ZWCAD-MCP` no fim do `git clone` define o nome da pasta, que é o usado nos caminhos deste guia.

Sem git: baixe o ZIP pelo GitHub (Code → Download ZIP), extraia em `C:\mcp\ZWCAD-MCP` (renomeie para `ZWCAD-MCP`; o ZIP vem como `ZWCAD-MCP-fortis-main`), entre na pasta e rode só as duas últimas linhas.

### 3. Carregar o LISP no ZWCAD

1. Abra o ZWCAD com um desenho e digite `APPLOAD`.
2. Adicione `C:\mcp\ZWCAD-MCP\lisp-code\zwcad_mcp_dispatch.lsp`, selecione o arquivo e clique em **Load**.
3. Com o arquivo ainda selecionado, clique em **Add to Startup Suite**. Assim ele carrega sozinho em todo desenho aberto depois.
4. Clique em **OK**. Enquanto essa janela estiver aberta, o ZWCAD não aceita comandos.
5. Confira na linha de comando: `=== ZWCAD-MCP Dispatch v1.0 + Fortis patch loaded ===`.

Cada desenho tem a sua própria memória de LISP. Um desenho que já estava aberto antes de configurar o Startup Suite não tem o dispatcher. Nele, cole na linha de comando (barras normais, `/`):

```
(load "C:/mcp/ZWCAD-MCP/lisp-code/zwcad_mcp_dispatch.lsp")
```

### 4. Configurar o cliente MCP

No Claude Desktop: Configurações → Desenvolvedor → **Editar configuração**. O arquivo `claude_desktop_config.json` fica assim, troque o caminho se usou outra pasta:

```json
{
  "mcpServers": {
    "zwcad-mcp": {
      "command": "C:\\mcp\\ZWCAD-MCP\\.venv\\Scripts\\python.exe",
      "args": ["-m", "zwcad_mcp"],
      "env": {
        "ZWCAD_MCP_BACKEND": "file_ipc",
        "ZWCAD_MCP_IPC_TIMEOUT": "30"
      }
    }
  }
}
```

Se o arquivo já tiver outros servidores ou outras chaves, siga estas regras (são onde os erros costumam acontecer):

- O arquivo começa com `{` sozinha na primeira linha.
- Cada servidor fica **dentro** das chaves de `"mcpServers"`.
- Entre um servidor e outro vai vírgula; depois do último, não.
- Se houver outras chaves depois de `"mcpServers"`, o `}` que o fecha leva vírgula.
- Caminhos levam barra dupla (`\\`).

### 5. Reiniciar o cliente

No Claude Desktop, feche pelo ícone ao lado do relógio → **Sair**. Fechar só pelo X não recarrega a configuração. Abra de novo e confira em Configurações → Desenvolvedor se o **zwcad-mcp** aparece "Em execução".

### 6. Testar

Com o ZWCAD aberto em um desenho, peça ao assistente:

1. `system status` → deve voltar `backend: file_ipc`.
2. `system list_windows` → lista os desenhos abertos e qual está ativo.
3. `system execute_lisp` com `(getvar "DWGNAME")` → nome do desenho ativo.

## Ferramentas

Oito ferramentas agrupadas, como no original: `drawing`, `entity`, `layer`, `block`, `annotation`, `pid`, `view` e `system`. Veja a lista de operações no [README original](README.zh-CN.md#工具一览8-个聚合工具).

O mais útil é `system` → `execute_lisp`: roda qualquer AutoLISP/Visual LISP no desenho ativo e devolve o valor da última expressão. Prefira ActiveX (`vla-*`) e `entmake` a `(command ...)`, porque comandos interativos podem ficar esperando um prompt.

Operações novas neste fork:

| Operação | O que faz |
| --- | --- |
| `system` → `list_windows` | Lista os desenhos abertos, o ativo e o alvo atual |
| `system` → `set_target` `{"drawing": "planta-01.dwg"}` | Fixa um desenho: o servidor ativa a aba dele e o LISP recusa rodar em outro. `{"drawing": ""}` limpa |

## Variáveis de ambiente

| Variável | Padrão | Uso |
| --- | --- | --- |
| `ZWCAD_MCP_BACKEND` | `auto` | `file_ipc` (recomendado: dá erro se o ZWCAD estiver fechado), `auto` (cai para DXF em memória sem avisar) ou `ezdxf` (sem ZWCAD) |
| `ZWCAD_MCP_IPC_TIMEOUT` | `10.0` | Segundos por comando (1–300). Recomendado: `30` |
| `ZWCAD_MCP_TRIGGER` | `com` | `com`: dispara pela API COM, sem teclas. `keys`: disparo original por teclas |
| `ZWCAD_MCP_IPC_DIR` | `C:/zwcad-temp` | Pasta de troca de arquivos (defina como variável de sistema se trocar) |
| `ZWCAD_MCP_ONLY_TEXT` | `false` | Desliga as capturas de tela |

## Regras de uso

- **Pode trabalhar em outros programas** enquanto o assistente desenha: nada aparece na tela.
- **Não trabalhe dentro do próprio ZWCAD** ao mesmo tempo: um comando seu pela metade pode se misturar com o do assistente.
- **Vários desenhos abertos:** os comandos vão para o desenho ativo. Use `set_target` para outro desenho e limpe o alvo ao terminar.
- **Janelas de diálogo do ZWCAD** (APPLOAD, propriedades etc.) bloqueiam os comandos: feche-as antes.
- **Salve antes de testes** em desenhos reais.

## Problemas comuns

| Sintoma | Causa | Solução |
| --- | --- | --- |
| Claude Desktop não abre: "Unexpected non-whitespace character after JSON" | JSON quebrado, normalmente sem a `{` inicial | Abra `%APPDATA%\Claude\claude_desktop_config.json` no Bloco de Notas e corrija (regras do passo 4) |
| zwcad-mcp não aparece na lista | Bloco fora de `"mcpServers"` ou vírgula errada | Regras do passo 4 |
| "zwcad_mcp_dispatch.lsp not loaded" | LISP não carregado nesse desenho | `(load ...)` na linha de comando ou APPLOAD → Load |
| Aparece só "v1.0 loaded", sem "+ Fortis patch" | Arquivo LISP do original no lugar | Confira se clonou este fork e carregue de novo |
| Tempo esgotado (Timeout) | Janela de diálogo aberta, comando parado ou LISP não carregado no desenho alvo | Feche o diálogo, aperte ESC no ZWCAD, confira o LISP. Antes de repetir, confira se o comando não rodou em parte |
| "Wrong drawing ... Nothing was executed" | O alvo fixado não é o desenho onde o comando chegou | `list_windows` para ver os desenhos; `set_target` com `""` limpa |
| `status` volta `ezdxf` | ZWCAD fechado, sem desenho aberto, ou Python do WSL | Abra um desenho; use o Python do Windows |

## Desenvolvimento

```powershell
.venv\Scripts\pip install -e . pytest pytest-asyncio
.venv\Scripts\python -m pytest tests/ -v
```

## Licença e créditos

MIT. Veja [LICENSE](LICENSE). Mantém o aviso de copyright original.

- [puran-water/autocad-mcp](https://github.com/puran-water/autocad-mcp): arquitetura base (MIT).
- [dalingo81/ZWCAD-MCP](https://github.com/dalingo81/ZWCAD-MCP): adaptação para o ZWCAD.
- Patch Fortis: compatibilidade Unicode, leader via ActiveX, envio para a janela certa e disparo sem teclas.
