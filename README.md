# ZWCAD-MCP-fortis

**English** · [Português](README.pt-BR.md) · [中文 (original)](README.zh-CN.md)

MCP server that lets an AI client (Claude Desktop, Cursor, etc.) read and draw in **ZWCAD** with nothing popping up on screen, while you keep working in another program.

This is a fork of [dalingo81/ZWCAD-MCP](https://github.com/dalingo81/ZWCAD-MCP) (commit `49883a9`), itself based on [puran-water/autocad-mcp](https://github.com/puran-water/autocad-mcp). The original was built for Chinese Windows. This fork makes it work on Windows in any other language (Portuguese, English, Spanish…) and removes all on-screen interference. Every change is tagged `[Fortis]` in the code and described in [FORTIS_PATCHES.md](FORTIS_PATCHES.md) (Portuguese).

Tested on ZWCAD 2026, Portuguese Windows.

## What changes from the original

| Problem in the original | In this fork |
| --- | --- |
| Accented text read from the drawing broke the reply (timeout) | Accents and symbols (ç, ã, é, ≥, Ø) round-trip correctly on any Windows code page |
| `execute_lisp` code was written as GBK: accents corrupted outside China | Code is written as pure ASCII; characters are restored inside ZWCAD |
| `create_leader` used the LEADER command, which leaves ZWCAD 2026 waiting at a prompt | Leader created via ActiveX; returns the leader and text handles |
| With several drawings open, commands went to the first window found | They go to the active drawing; `set_target` pins one drawing and the LISP side refuses to run in any other |
| Keystroke trigger: Dynamic Input box near the cursor, and ZWCAD jumping to the front | Trigger through ZWCAD's COM API, no keystrokes; focus stays where you are |
| Reopening ZWCAD required restarting the server | The server finds the new window by itself |
| Empty string `""` parameters were not parsed | Fixed |

## Requirements

- Windows 10/11.
- ZWCAD 2020 or newer, with AutoLISP (Professional or Standard). Tested on 2026.
- Python 3.10 or newer, **Windows build** (not WSL).
- Git (optional; you can download the ZIP).

## Installation

### 1. Check Python

In PowerShell:

```powershell
python --version
```

If it is not 3.10 or newer, install it from python.org and tick **"Add python.exe to PATH"**. Close and reopen PowerShell afterwards.

### 2. Download and install the server

Pick a folder for your MCP servers. The example uses `C:\mcp`:

```powershell
mkdir C:\mcp; cd C:\mcp
git clone https://github.com/ArthurmendesC/ZWCAD-MCP-fortis.git ZWCAD-MCP
cd ZWCAD-MCP
python -m venv .venv
.venv\Scripts\pip install -e .
```

The `ZWCAD-MCP` at the end of `git clone` sets the folder name used in the paths of this guide.

Without git: download the ZIP from GitHub (Code → Download ZIP), extract it to `C:\mcp\ZWCAD-MCP` (rename it to `ZWCAD-MCP`; the ZIP comes as `ZWCAD-MCP-fortis-main`), go into the folder and run only the last two lines.

### 3. Load the LISP in ZWCAD

1. Open ZWCAD with a drawing and type `APPLOAD`.
2. Add `C:\mcp\ZWCAD-MCP\lisp-code\zwcad_mcp_dispatch.lsp`, select it and click **Load**.
3. With the file still selected, click **Add to Startup Suite**. It then loads by itself in every drawing you open later.
4. Click **OK**. While that dialog is open, ZWCAD does not accept commands.
5. Check the command line: `=== ZWCAD-MCP Dispatch v1.0 + Fortis patch loaded ===`.

Each drawing has its own LISP namespace. A drawing that was already open before you set up the Startup Suite does not have the dispatcher. In it, paste this at the command line (forward slashes, `/`):

```
(load "C:/mcp/ZWCAD-MCP/lisp-code/zwcad_mcp_dispatch.lsp")
```

### 4. Configure the MCP client

In Claude Desktop: Settings → Developer → **Edit Config**. `claude_desktop_config.json` looks like this; change the path if you used another folder:

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

If the file already has other servers or other keys, follow these rules (this is where mistakes usually happen):

- The file starts with `{` alone on the first line.
- Every server goes **inside** the braces of `"mcpServers"`.
- Servers are separated by commas; no comma after the last one.
- If there are other keys after `"mcpServers"`, its closing `}` takes a comma.
- Paths use double backslashes (`\\`).

### 5. Restart the client

In Claude Desktop, quit from the tray icon next to the clock → **Quit**. Closing with the X does not reload the config. Open it again and check in Settings → Developer that **zwcad-mcp** shows as running.

### 6. Test

With ZWCAD open on a drawing, ask the assistant to run:

1. `system status` → should return `backend: file_ipc`.
2. `system list_windows` → lists the open drawings and which one is active.
3. `system execute_lisp` with `(getvar "DWGNAME")` → name of the active drawing.

## Tools

Eight grouped tools, as in the original: `drawing`, `entity`, `layer`, `block`, `annotation`, `pid`, `view` and `system`. See the operation list in the [original README](README.zh-CN.md#工具一览8-个聚合工具).

The most useful one is `system` → `execute_lisp`: it runs any AutoLISP/Visual LISP in the active drawing and returns the value of the last expression. Prefer ActiveX (`vla-*`) and `entmake` over `(command ...)`, because interactive commands may stay waiting at a prompt.

New operations in this fork:

| Operation | What it does |
| --- | --- |
| `system` → `list_windows` | Lists open drawings, the active one and the current target |
| `system` → `set_target` `{"drawing": "floor-plan-01.dwg"}` | Pins a drawing: the server activates its tab and the LISP side refuses to run in any other. `{"drawing": ""}` clears it |

## Environment variables

| Variable | Default | Use |
| --- | --- | --- |
| `ZWCAD_MCP_BACKEND` | `auto` | `file_ipc` (recommended: errors out if ZWCAD is closed), `auto` (silently falls back to an in-memory DXF) or `ezdxf` (no ZWCAD) |
| `ZWCAD_MCP_IPC_TIMEOUT` | `10.0` | Seconds per command (1–300). Recommended: `30` |
| `ZWCAD_MCP_TRIGGER` | `com` | `com`: trigger through the COM API, no keystrokes. `keys`: original keystroke trigger |
| `ZWCAD_MCP_IPC_DIR` | `C:/zwcad-temp` | File exchange folder (set it as a system variable if you change it) |
| `ZWCAD_MCP_ONLY_TEXT` | `false` | Disables screenshots |

## Usage rules

- **You can work in other programs** while the assistant draws: nothing shows up on screen.
- **Do not work inside ZWCAD itself** at the same time: a half-finished command of yours can mix with the assistant's.
- **Several drawings open:** commands go to the active drawing. Use `set_target` for another one and clear the target when done.
- **ZWCAD dialogs** (APPLOAD, properties, etc.) block commands: close them first.
- **Save before tests** on real drawings.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Claude Desktop won't start: "Unexpected non-whitespace character after JSON" | Broken JSON, usually the opening `{` is missing | Open `%APPDATA%\Claude\claude_desktop_config.json` in Notepad and fix it (rules in step 4) |
| zwcad-mcp does not show in the list | Block outside `"mcpServers"` or a wrong comma | Rules in step 4 |
| "zwcad_mcp_dispatch.lsp not loaded" | LISP not loaded in that drawing | `(load ...)` at the command line, or APPLOAD → Load |
| Only "v1.0 loaded" shows, without "+ Fortis patch" | The original LISP file is in place | Make sure you cloned this fork and load it again |
| Timeout | Open dialog, stuck command, or LISP not loaded in the target drawing | Close the dialog, press ESC in ZWCAD, check the LISP. Before retrying, check whether the command partly ran |
| "Wrong drawing ... Nothing was executed" | The pinned target is not the drawing the command reached | `list_windows` to see drawings; `set_target` with `""` clears it |
| `status` returns `ezdxf` | ZWCAD closed, no drawing open, or WSL Python | Open a drawing; use Windows Python |

## Development

```powershell
.venv\Scripts\pip install -e . pytest pytest-asyncio
.venv\Scripts\python -m pytest tests/ -v
```

## License and credits

MIT. See [LICENSE](LICENSE). The original copyright notice is kept.

- [puran-water/autocad-mcp](https://github.com/puran-water/autocad-mcp): base architecture (MIT).
- [dalingo81/ZWCAD-MCP](https://github.com/dalingo81/ZWCAD-MCP): ZWCAD adaptation.
- Fortis patch: Unicode compatibility, ActiveX leader, window targeting and keystroke-free trigger.
