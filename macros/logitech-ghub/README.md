# Logitech G HUB — 10 independent NUMPAD+ placeholder macros

Checkpoint date: 2026-11-25 (Taipei local date)  
Repository: https://github.com/MapleVibeCodin/MaplestoryVibeCodin  
Branch: `main`  
Active project: Logitech G HUB macro editing. **Not FM Rush or scrolling EV.** Do not alter those projects to fulfill this task.

## User requirement (latest and authoritative)

The user rejected the idea of one macro containing ten NUMPAD+ taps. They want exactly **10 separate, editable placeholder macros**. Each contains **one** NUMPAD+ press/release, with a 5 ms key-down delay. They also reported that attempting to select the original NUM+ macro through the UI did not work.

The current screenshot shows a pre-existing macro named `NUM PLUS ENTER 5MS`, with NUMPAD+ and Enter events and recorded 5 ms delays. This pre-existing macro must not be overwritten.

## Files

1. [Create-10-Numpad-Placeholders.ps1](./Create-10-Numpad-Placeholders.ps1) — complete Windows PowerShell implementation, byte-for-byte matching the previously delivered conversation artifact. Local original was 8,538 bytes; SHA-256 `f648fff9e496e8054739a2f5d19ab514594b77032c00f28de53e921b6e7c7c6a`; Git blob SHA `5ef52a2c0e95132c70c90cab9d3cdec56183c847`.
2. [transcripts/2026-11-25-current-chat.md](./transcripts/2026-11-25-current-chat.md) — accessible previous user and assistant messages, including the exact correction and checkpoint command, screenshot provenance and coverage limitations.
3. The original screenshot is not included as a binary in the GitHub archive. Screenshot filename `image(20261123-200149).png`, resolution 1334×794, local SHA-256 `f154e4740f342ace367f8748a438f648b56bb04e02794e3d3c4385b2ce1bc086`.

## Implementation behavior

- Attempts to elevate to administrator and finds `%LOCALAPPDATA%\LGHUB\settings.db`.
- Requires Python 3 (`py.exe -3` preferred, fallback `python.exe`) and uses Python SQLite/JSON to edit G HUB's database.
- Locates existing `NUM PLUS ENTER 5MS` macro, fallback `FM SPOT`, requiring `MACRO_PLAYBACK` attribute and an `applicationId`.
- Creates `NUM+ PLACEHOLDER 01` through `NUM+ PLACEHOLDER 10` as separate cards with unique UUIDs in the same application profile.
- Each new macro is a simple sequence of three components: `NUMPAD +` key-down, `delay 5ms`, `NUMPAD +` key-up. No Enter or other inputs, no ten-press macro.
- Preserves original cards and skips already-existing placeholder names on repeated runs. Writes a timestamped SQLite database backup before the modification; runs `PRAGMA integrity_check` and checks new macro event structure.
- Stops G HUB/updater processes, edits the database, restarts services and tries to reopen G HUB.
- Does not assign the ten macros to any actual buttons; they should be available under `Assignments > MACROS` if the target G HUB version recognizes this structure.

## One-paste Windows installation

Run this complete block from PowerShell. It fetches the verified file into Downloads and invokes it:

```powershell
$u = Join-Path $HOME 'Downloads\Create-10-Numpad-Placeholders.ps1'
Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/main/macros/logitech-ghub/Create-10-Numpad-Placeholders.ps1' -OutFile $u -ErrorAction Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $u
```

The script asks for administrator elevation. In G HUB, navigate to `Assignments > MACROS` and look for `NUM+ PLACEHOLDER 01` through `10`.

## Validation actually performed

- The original local file was inspected in full; size 8,538 bytes and SHA-256 recorded above.
- The embedded Python source was extracted from the PowerShell here-string and successfully compiled with the available Python interpreter.
- An isolated synthetic SQLite `data(file)` database with a source macro matching the required structure was constructed.
- First execution returned exit code 0 and added 10 independent macro cards, each with exactly three components.
- Second execution returned exit code 0 and added no duplicates; total cards remained eleven including the original.
- The GitHub uploaded PowerShell file was read back using the GitHub connector. Its Git blob SHA equals the `git hash-object` result for the original local file: `5ef52a2c0e95132c70c90cab9d3cdec56183c847`. That verifies exact committed bytes.
- **Not performed:** Windows PowerShell parsing/runtime test; user PC database edits; actual G HUB GUI visibility, selection, button binding, or macro playback. Do not claim that these are verified.

## Resume priorities

1. Start with this README and the complete script, not a summarized memory of the code. Read the current GitHub branch to avoid stale versions.
2. Respect the requirement of **ten different macros**, **one NUMPAD+ each**. Do not silently add Enter, L, repetitions, or change the current original macro.
3. If the user says the macro list is empty/unselectable or the command failed, request the command's console error or inspect the exact relevant G HUB database state with a non-mutating diagnostic first; investigate schema/profile compatibility without deleting existing macros. The current script is not a proven G HUB runtime fix.
4. A local backup is generated on successful script execution; do not delete the backup. Restore from it only with explicit user approval.
5. Keep this project checkpoint separate from the FM Rush AGENTS.md workflow. Preserve other repository content.

## Integrity scope

This archive includes all accessible previous textual user requests and completed assistant responses from this short G HUB conversation. It is **not** a full ChatGPT export of hidden or inaccessible messages. The original screenshot is inventoried by digest but not copied. This checkpoint is written before the assistant's final confirmation reply and thus cannot itself include that future reply.
