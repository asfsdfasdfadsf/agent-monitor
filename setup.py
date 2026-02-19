"""
Auto-configures Claude Code hooks to send events to Agent Monitor.
Run: python setup.py
"""

import json
import os
import sys
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
hook_script = (Path(__file__).parent / "hook.sh").resolve().as_posix()
hook_script_win = str((Path(__file__).parent / "hook.ps1").resolve())

is_windows = sys.platform == "win32"

# The command to run in the hook
if is_windows:
    hook_command = f'powershell -ExecutionPolicy Bypass -File "{hook_script_win}"'
else:
    hook_command = f'bash "{hook_script}"'

hook_entry = {"type": "command", "command": hook_command}

print("\n  Agent Monitor - Hook Setup\n")
print(f"  Settings file: {settings_path}")
print(f"  Hook script:   {hook_script_win if is_windows else hook_script}\n")

# Read existing settings
settings = {}
if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text("utf-8"))
        print("  Found existing settings.json")
    except json.JSONDecodeError:
        print("  Warning: Could not parse existing settings.json, creating new")
else:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    print("  Creating new settings.json")

# Add hooks
if "hooks" not in settings:
    settings["hooks"] = {}

for hook_type in ("PreToolUse", "PostToolUse"):
    if hook_type not in settings["hooks"]:
        settings["hooks"][hook_type] = []

    hooks = settings["hooks"][hook_type]
    existing = next((h for h in hooks if h.get("command") and "hook." in h["command"]), None)

    if existing:
        print(f"  {hook_type} hook already configured, updating...")
        existing["command"] = hook_entry["command"]
    else:
        hooks.append(dict(hook_entry))

# Write settings
settings_path.write_text(json.dumps(settings, indent=2) + "\n", "utf-8")

print("\n  Hooks configured successfully!")
print("\n  Next steps:")
print("    1. Run:  python server.py     (starts the monitor)")
print("    2. Open: http://localhost:7778")
print("    3. Use Claude Code normally - events appear live!\n")
