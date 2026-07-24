# ZWCAD-MCP

面向 **中望CAD（ZWCAD）** 的 MCP（Model Context Protocol）服务器，让 Claude / Cursor 等 AI 客户端通过自然语言直接驱动中望CAD 绘图、修改、查询与出图。

本项目基于 [puran-water/autocad-mcp](https://github.com/puran-water/autocad-mcp) 改写，并参考了 [mysteryboy2000/ZWCAD-Mechanical-MCP](https://github.com/mysteryboy2000/ZWCAD-Mechanical-MCP) 与 [中望CAD 二次开发文档](https://www.zwsoft.cn/support/zwcad-devdoc)。

## 特性

双后端、同一套 API：

| 后端 | 运行环境 | 是否需要中望CAD | 截图方式 |
|------|----------|-----------------|----------|
| **File IPC**（AutoLISP + Win32 PostMessage） | Windows | 需要（ZWCAD 2020+ 专业版/标准版） | Win32 `PrintWindow` 窗口 PNG 截图 |
| **ezdxf**（无头模式） | 任意平台（Windows / Linux / macOS / WSL） | 不需要 | matplotlib 渲染 PNG |

- **免抢焦点通信**：通过 `PostMessageW(WM_CHAR)` 向中望CAD 的 MDIClient 子窗口发送 `(c:zwmcp-dispatch)` 触发指令，你可以继续在其他窗口工作，自动化在后台执行。
- **JSON 文件桥接**：Python 端写入命令 JSON → LISP 调度器读取执行 → 写回结果 JSON，全程原子写入 + 请求 ID 校验。
- **`execute_lisp`**：执行任意 AutoLISP 代码（中望CAD 完整支持 AutoLISP / Visual LISP，含 `vl-*`、`vlax-*` 函数）。
- **内置 PNG 截图**：`view(operation="get_screenshot")` 抓取当前中望CAD 视图，即使窗口最小化/被遮挡也能截取。
- **无头跨平台**：ezdxf 后端无需安装 CAD，可在 Linux/macOS/CI 中离线生成与编辑 DXF。

## 架构

```
MCP 客户端 (Claude / Cursor / ...)
    │  stdio (JSON-RPC)
    ▼
Python MCP Server (zwcad_mcp)
    │
    ├── File IPC 后端 ──► C:/zwcad-temp/zwcad_mcp_cmd_{id}.json
    │       │                      │
    │       │ PostMessageW(WM_CHAR) 触发 (c:zwmcp-dispatch)（不抢焦点）
    │       ▼                      ▼
    │   中望CAD (ZWCAD) ◄── zwcad_mcp_dispatch.lsp 读命令、执行、写结果
    │                       C:/zwcad-temp/zwcad_mcp_result_{id}.json
    │
    └── ezdxf 后端 ──► 内存中的 DXF 文档（无头，无需 CAD）
```

## 环境要求（File IPC 后端）

- **Windows 10/11**
- **中望CAD 2020 或更高版本**（专业版/标准版均可，需支持 AutoLISP；中望CAD 完整实现了 AutoLISP/Visual LISP 方言）
- **Python 3.10+**（Windows 原生 Python，非 WSL Python）

> ezdxf 无头后端可在任意平台运行，无需安装中望CAD。

## 快速开始

### 1. 安装

```powershell
git clone <本仓库地址>
cd ZWCAD-MCP
python -m venv .venv
.venv\Scripts\pip install -e .
```

### 2. 在中望CAD 中加载 LISP 调度器

打开中望CAD，使用 **APPLOAD** 命令加载 `lisp-code/zwcad_mcp_dispatch.lsp`：

1. 在命令行输入 `APPLOAD`
2. 浏览到 `<仓库路径>/lisp-code/zwcad_mcp_dispatch.lsp`
3. 点击 **加载**
4. 命令行应显示：`=== ZWCAD-MCP Dispatch v1.0 loaded ===` 和 `Ready for commands via (c:zwmcp-dispatch)`

> **提示**：在 APPLOAD 对话框中把该文件加入「启动组」，即可随每张图纸自动加载。也可将 `lisp-code/` 加入中望CAD 的受信任路径。

### 3. 配置 MCP 客户端

在客户端配置（如 Claude Desktop 的 `claude_desktop_config.json`）中添加：

```json
{
  "mcpServers": {
    "zwcad-mcp": {
      "command": "C:\\path\\to\\ZWCAD-MCP\\.venv\\Scripts\\python.exe",
      "args": ["-m", "zwcad_mcp"],
      "env": { "ZWCAD_MCP_BACKEND": "auto" }
    }
  }
}
```

- `ZWCAD_MCP_BACKEND` 可选：`auto`（默认，优先 File IPC，找不到中望CAD 窗口则回落 ezdxf）、`file_ipc`（强制要求中望CAD 运行）、`ezdxf`（纯无头）。

### 4. 验证

在 MCP 客户端调用：

```
system(operation="status")
```

中望CAD 正在运行时应返回 `backend: "file_ipc"`，否则返回 `backend: "ezdxf"`（无头模式）。

## 工具一览（8 个聚合工具）

### `drawing` — 图纸/文件管理
`create`（清空重置）· `open` · `info` · `save` · `save_as_dxf` · `plot_pdf` · `purge` · `get_variables` · `undo` · `redo`

### `entity` — 实体增删改查
- **创建**：`create_line`、`create_circle`、`create_polyline`、`create_rectangle`、`create_arc`、`create_ellipse`、`create_mtext`、`create_hatch`
- **查询**：`list`、`count`、`get`
- **修改**：`copy`、`move`、`rotate`、`scale`、`mirror`、`offset`*、`array`、`fillet`*、`chamfer`*、`erase`

> \* `offset` / `fillet` / `chamfer` 仅 File IPC 后端支持。

### `layer` — 图层管理
`list` · `create` · `set_current` · `set_properties` · `freeze` · `thaw` · `lock` · `unlock`

### `block` — 图块操作
`list` · `insert` · `insert_with_attributes` · `get_attributes` · `update_attribute` · `define`（仅 ezdxf）

### `annotation` — 文字与标注
`create_text` · `create_dimension_linear` · `create_dimension_aligned` · `create_dimension_angular` · `create_dimension_radius` · `create_leader`

### `pid` — 工艺流程图（P&ID，可选）
`setup_layers` · `insert_symbol` · `list_symbols` · `draw_process_line` · `connect_equipment` · `add_flow_arrow` · `add_equipment_tag` · `add_line_number` · `insert_valve` · `insert_instrument` · `insert_pump` · `insert_tank`

> P&ID 符号插入依赖 CTO 符号库（`C:\PIDv4-CTO\`），未安装时其余功能不受影响。

### `view` — 视图与截图
| 操作 | 说明 |
|------|------|
| `zoom_extents` | 缩放显示全部实体 |
| `zoom_window` | 窗口缩放到指定范围 |
| `get_screenshot` | **抓取当前中望CAD 视图为 PNG**（Win32 `PrintWindow`，最小化/后台也可截取；ezdxf 后端用 matplotlib 渲染） |

多数写操作工具支持 `include_screenshot: true` 参数，执行后自动附带一张 PNG 截图，方便 AI 校验绘图结果。

### `system` — 服务器管理
`status` · `health` · `get_backend` · `runtime` · `init` · **`execute_lisp`**

> **`execute_lisp`** 执行任意 AutoLISP 代码（File IPC 后端）：
> ```
> system(operation="execute_lisp", data={"code": "(command \"_.CIRCLE\" \"100,100\" 50)"})
> ```
> 代码通过临时 `.lsp` 文件加载执行，可使用中望CAD 支持的全部 AutoLISP / Visual LISP 能力（`entmake`、`entget`、`ssget`、`vl-*`、`vlax-*` 等），是扩展本服务器的万能入口。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ZWCAD_MCP_BACKEND` | `auto` | 后端选择：`auto` / `file_ipc` / `ezdxf` |
| `ZWCAD_MCP_IPC_DIR` | `C:/zwcad-temp` | IPC 命令/结果 JSON 目录（LISP 端会读取同名系统环境变量自动保持一致） |
| `ZWCAD_MCP_IPC_TIMEOUT` | `10.0` | IPC 命令超时秒数（1–300） |
| `ZWCAD_MCP_LISP_DIR` | 自动探测 | LISP 调度器目录覆盖（默认先找包内 `zwcad_mcp/lisp-code`，再找仓库根 `lisp-code/`） |
| `ZWCAD_MCP_ONLY_TEXT` | `false` | 禁用截图（仅文本反馈） |

> 修改 IPC 目录时，推荐把 `ZWCAD_MCP_IPC_DIR` 设为**系统环境变量**（而不仅是 MCP 客户端的 env），这样中望CAD 进程内的 LISP 调度器也能读到同一值；否则需手改 `zwcad_mcp_dispatch.lsp` 中的 `*zwmcp-ipc-dir*`。

## 中望CAD 适配说明

相对 AutoCAD 版本的主要适配点：

1. **窗口探测**：按标题匹配 `ZWCAD` / `中望CAD`（兼容中英文版本），优先选择已打开图纸的窗口。
2. **命令派发**：在 ZWCAD 2026 上经实测，按键需注入到 **绘图视图子窗口** `AfxFrameOrView140u` 而非 MDIClient；Python 端会优先枚举 `AfxFrameOrView*` 类子窗口，回退到 MDIClient。通过 `PostMessageW(WM_CHAR)` 注入 `(c:zwmcp-dispatch)` + 回车，发送前注入 2×ESC 取消滞留命令。
3. **LISP 方言**：中望CAD 完整支持 AutoLISP / Visual LISP（含 `vl-*`、`vlax-*` ActiveX 函数），调度器 `zwcad_mcp_dispatch.lsp` 无需降级即可运行；相比 AutoCAD LT 反而能力更全。
4. **编码兼容**：结果文件读取按 UTF-8 → GBK → cp1252 回退；`execute_lisp` 临时代码文件优先按 GBK 写入（中望CAD 按系统 ANSI 代码页读 LISP 文件），中文字符串不乱码。调度器 LISP 文件本身为纯 ASCII，任何语言的 Windows 均可加载。
5. **SECURELOAD 兼容**（ZWCAD 2026 实测）：新版中望CAD 禁止 LISP 里 `setvar "SECURELOAD"`，`execute_lisp` 已改用「读文件 + `read`/`eval`」方式执行，不受 SECURELOAD 限制。
6. **TEXT 创建**（ZWCAD 2026 实测）：`_TEXT` 命令提示序列与 AutoCAD 不同，`create_text` 改用 `entmake` 非交互创建，跨版本稳定。
7. **打印样式**：`plot_pdf` 默认使用 `acad.ctb`（中望CAD 自带兼容样式表），可按需在 LISP 中改为 `zwcad.ctb` 等。

## 新电脑部署清单

1. 安装 **Windows 版 Python 3.10+**（勿用 WSL 内的 Python）。
2. `git clone` 本仓库 → `python -m venv .venv` → `.venv\Scripts\pip install -e .`（会按平台自动装 pywin32）。
3. 打开中望CAD（2020+，专业版/标准版），`APPLOAD` 加载 `lisp-code/zwcad_mcp_dispatch.lsp`，看到 `=== ZWCAD-MCP Dispatch v1.0 loaded ===` 即成功（建议加入「启动组」）。
4. IPC 目录 `C:/zwcad-temp` 会由两端自动创建，无需手建；如需更换，设系统环境变量 `ZWCAD_MCP_IPC_DIR`。
5. 把 `mcp-config.json` 内容拷入 MCP 客户端配置，将 `command` 改为本机 `.venv\Scripts\python.exe` 的**绝对路径**。
6. 客户端里调用 `system(operation="status")` 验证，应返回 `backend: "file_ipc"`。

常见问题：
- **status 返回 ezdxf**：中望CAD 没开、没开图纸，或 MCP 用的是非 Windows Python。
- **提示 dispatcher not loaded**：LISP 未加载或加载后新开了图纸标签页（每个文档命名空间独立，建议加入启动组）。
- **命令超时**：确认中望CAD 命令行没有停在某个交互提示上（按 ESC 后重试）；Python 端每 2 秒会自动重发触发指令。

## 开发与测试

```powershell
.venv\Scripts\pip install -e . pytest pytest-asyncio
.venv\Scripts\python -m pytest tests/ -v
```

## 目录结构

```
ZWCAD-MCP/
├── lisp-code/
│   ├── zwcad_mcp_dispatch.lsp   # LISP 调度器（APPLOAD 加载到中望CAD）
│   └── attribute_tools.lsp      # 块属性辅助函数
├── src/zwcad_mcp/
│   ├── server.py                # FastMCP 服务器，8 个聚合工具
│   ├── client.py                # 后端单例、错误处理、截图辅助
│   ├── config.py                # 后端探测与环境变量
│   ├── screenshot.py            # Win32 PrintWindow / matplotlib 截图
│   ├── backends/
│   │   ├── base.py              # 后端抽象基类
│   │   ├── file_ipc.py          # AutoLISP + Win32 PostMessage 后端
│   │   └── ezdxf_backend.py     # ezdxf 无头后端
│   └── pid/                     # P&ID 符号库支持（可选）
├── tests/                       # pytest 测试
├── mcp-config.json              # MCP 客户端配置示例
└── pyproject.toml
```

## 致谢

- [puran-water/autocad-mcp](https://github.com/puran-water/autocad-mcp)（MIT）— 本项目的架构基线
- [mysteryboy2000/ZWCAD-Mechanical-MCP](https://github.com/mysteryboy2000/ZWCAD-Mechanical-MCP) — 中望CAD MCP 工具设计参考
- [中望软件二次开发文档](https://www.zwsoft.cn/support/zwcad-devdoc) — ZWCAD LISP/API 参考

## License

MIT
