# Agent Monitor

A live web dashboard that shows what Claude Code is doing in real-time — like a Cursor/AutoGPT agent view.

![Dashboard](https://img.shields.io/badge/status-live-brightgreen) ![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![Dependencies](https://img.shields.io/badge/dependencies-zero-orange)

## How it works

```
Claude Code hooks → bash hook.sh → POST /event → SSE → Browser dashboard
```

- Claude Code's **PostToolUse** hook fires on every tool call
- `hook.sh` reads the JSON from stdin and curls it to the local server
- `server.py` (pure Python stdlib, **zero dependencies**) receives events and pushes them via Server-Sent Events
- `index.html` renders a live dashboard with contextual viewers

## Features

- **Timeline** (left panel) — every tool call, color-coded by type (Read=blue, Edit=orange, Bash=red, etc.)
- **Live Viewer** (center panel) — auto-switches based on tool type:
  - **Code editor** for Read/Edit/Write (syntax highlighting, diff view for edits)
  - **Terminal** for Bash (black terminal with $ prompt)
  - **Google browser** for WebSearch (fake Chrome with search results)
  - **Browser** for WebFetch (with address bar and page content)
  - **Search panel** for Grep/Glob (with pattern highlighting)
  - **Agent orb** for Task (pulsing orb with task description)
- **Stats** (right panel) — read/write/command/search counts, tool usage bar chart, file tree
- Auto-follow mode tracks latest event; click timeline items to pin

## Quick Start

### 1. Start the server

```bash
cd agent-monitor
python server.py
```

Server runs at **http://localhost:7778**.

### 2. Configure Claude Code hooks

**Option A: Automatic setup**

```bash
python setup.py
```

**Option B: Manual setup**

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash /path/to/agent-monitor/hook.sh"
          }
        ]
      }
    ]
  }
}
```

### 3. Restart Claude Code

Hooks only load on session start — restart Claude Code after configuring hooks.

### 4. Open the dashboard

Navigate to **http://localhost:7778** and use Claude Code normally. Events appear live!

## Architecture

```
agent-monitor/
├── server.py          # ThreadingHTTPServer + SSE, port 7778
├── public/
│   └── index.html     # Full dashboard UI (single file)
├── hook.sh            # Bash hook that curls event JSON to server
├── hook.ps1           # PowerShell version (experimental)
├── setup.py           # Auto-configures hooks in settings.json
└── README.md
```

- **Zero dependencies** — pure Python stdlib (`http.server`, `threading`, `json`)
- **SSE** with per-client queues for reliable delivery
- **Ring buffer** of 1000 events (configurable via `MAX_EVENTS`)

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Dashboard UI |
| `/event` | POST | Receive hook events (JSON body) |
| `/api/stream` | GET | SSE stream of live events |
| `/api/events` | GET | Last 200 stored events (JSON) |
| `/api/stats` | GET | Tool counts and file lists |

## Notes

- Requires **Python 3.8+**
- Uses `ThreadingHTTPServer` (required for SSE to work alongside POST)
- On Windows, use `bash` (Git Bash) for the hook, not PowerShell
- `hook.sh` logs to `/tmp/hook-debug.log` for troubleshooting

## License

MIT
