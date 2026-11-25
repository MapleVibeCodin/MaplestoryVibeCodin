# FM Rush conversation checkpoint — 2026-11-25

Scope: all three user-visible messages available in this chat before the checkpoint response (two user messages, one assistant reply). Speaker labels added; message body wording and code preserved. Interface-only citation marker and code-block identifier excluded. Earlier separate conversations, hidden instructions, tool calls, and commentary are not part of this transcript. This public repository contains project material only.

## User

give me latest command to open the fmm rush

## Assistant

Paste into PowerShell to open the latest installed FM Rush scanner (v24.53.1):

```powershell
$f = Get-ChildItem "$HOME\Desktop","$HOME\Downloads" -Filter "START_FM_RUSH.bat" -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if ($f) { Start-Process $f.FullName -WorkingDirectory $f.DirectoryName } else { Write-Host "FM Rush not found" }
```

Automatically locates and launches your newest local FM Rush installation without reinstalling anything. It selects by launcher modification date, rather than verifying the installed version.

## User

```
Checkpoint this chat to GitHub, including all accessible unsaved messages verbatim and the latest project state. Verify the files before I switch.
```

## Checkpoint metadata (not transcript)

GitHub main source read during this checkpoint: Scanner Nov 20/fm_rush.py, blob 3003be0a814acb8a647a2a02da3fce230b015869, window title v24.53.1; UPDATE_FM_RUSH.ps1 blob c490c8693847cddf0109fbb56164d3b7602caac9; START_FM_RUSH.bat blob 02c7f54b1c4ba3de258f2fd65b4a781bddde92fa. No runtime source changed in this chat. Launch command searches only Desktop and Downloads, does not update software or validate local version, and sorts by modification date. Local Windows launch and live game behavior not tested. Existing scrolling-EV research remains separate and unchanged. Root AGENTS.md is the FM Rush handoff.
