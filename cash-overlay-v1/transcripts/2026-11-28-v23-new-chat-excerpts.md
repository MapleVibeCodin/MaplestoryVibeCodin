# 2026-11-28 — accessible continuation dialogue

This is a chronological transcription of accessible selected user-visible project dialogue, not a complete chat export. Original wording preserved in included passages; UI cards converted to text where indicated, tool citations not portable, private session measurements and raw attachments intentionally excluded from this public repository. Earlier compacted context is not a verbatim source. Do not present this as the complete transcript. Existing detailed technical records are linked by NEXT_CHAT_HANDOFF.md.

## User
ok how many of each mob did i kill

## Assistant
I found an important issue while checking the raw EXP notifications: **you were receiving party-shared EXP and party bonus EXP**, even though the scanner recorded your party size as one.

That means dividing your total EXP by 107 (Echopus EXP) would substantially misrepresent your personal kill count. The previous solo classification was incorrect.

[Private session-specific table and measurements omitted.]

To determine actual kills by species, the scanner needs to distinguish your combat kills from shared EXP and party bonuses, and recognize monster death animations.

I've [saved the newly discovered party-classification failure to GitHub](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/cash-overlay-v1/fixes/2026-11-28-v21-false-solo-party-context.md). The fix is not yet implemented.

## User
ok well give me the exact. find a way how

## Assistant
[Private session-specific recovered item observations omitted.]

## Why I can't get the exact kill count yet

I investigated reversing the party EXP formula. However, Classic World distributes 80% of EXP according to party member levels and 20% according to damage contribution. Without both variables, the calculation doesn't have a unique solution.

[Citation UI omitted; source references and community-formula limitation retained in the offline replay research record.]

The recording also has gaps of up to 59.6 seconds between retained combat images.

## How to solve this permanently

Instead of saving more screenshots, the scanner should analyze combat continuously in memory and record:

- Monster species and individual tracking ID.
- Your attacks and damage dealt.
- Monster death animation and timestamp.
- Whether you or another player caused the death.
- Associated loot and EXP notifications.

This would substantially improve kill attribution with minimal additional storage.

[Private results omitted.]

The successful offline recognition experiment is [saved and verified on GitHub](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/cash-overlay-v1/research/2026-11-28-v21-offline-monster-loot-template-replay.md). The runtime upgrade has not yet been implemented.

## User
ok do all the significant upgrades.  i also want an easy   way to track everything, monster drop, exp drop, all that stuff. the best way honestly is to look on the right side where the xp and loot is but you need to research the best methodology. google how the big websites do it and mimic

## Assistant
[Technical release and all implementation details archived in fixes/2026-11-28-v22-notification-replay-release.md; visual cards and complete assistant prose not transcribed here.]

## User
okok  update best you can

## Assistant
# Maple Research Scanner v2.3 — ready

Upgraded, published and verified on GitHub.

## Additional improvements

| Feature | Upgrade |
|---|---|
| Long-session processing | Incremental reading instead of repeatedly processing history |
| Notification recognition | Selective third recognition pass |
| Monster-specific drops | Automatically grouped by species |
| EXP breakdown | Personal, shared and party bonus |
| Farming timeline | Minute-by-minute CSV |
| Duplicate notifications | Separate arrival records preserved |
| Incomplete recognition | Explicit pending and unreadable counts |
| Storage | No additional continuous screenshots |

## Actual testing

[Visual card text transcribed in display order.]
Repeated source-reading workload
99.97× less
Tested using 9,459 existing records

Recognition agreement
83.3%
Previously 80.7% on the same 336-image experimental sample

All 13 conflicting recognition results were withheld rather than guessed. Four new helper regression tests passed.

## Install and launch

Close your existing scanner and run:

```powershell
& { $env:MAPLE_CASH_REF='a7b2ac21b55b3463be466ccb7c94571c48e69fd3'; $f=Join-Path $env:TEMP 'MapleResearch_v23_INSTALL.ps1'; Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/MapleVibeCodin/MaplestoryVibeCodin/$env:MAPLE_CASH_REF/cash-overlay-v1/INSTALL.ps1" -OutFile $f; powershell.exe -NoProfile -ExecutionPolicy Bypass -File $f }
```

Everything remains automatic. Farm normally, close the scanner and upload the ZIP.

**GitHub:** [Latest verified checkpoint](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/commit/c9b74f53915d39fcb3d233bf92c957b0c61da38a) · [Upgrade and testing record](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/cash-overlay-v1/fixes/2026-11-28-v23-incremental-notifications.md)

Full Windows integration testing remains pending. Exact personal monster kills are not yet verified; species-specific drops are reported separately. All previous fixes, research and historical files remain preserved.

## User
ok next secret map for forgotten?

## Assistant
## Next hidden gem: Decayed Tunnel I

105–140k EXP/hr
Our modeled single-platform potential, not yet tested
[Open map and spawn locations](https://meowdb.com/msclassic/maps/010006120)

| Monster | Spawn points | HP | EXP |
|---|---:|---:|---:|
| Duskmander | 11 | 2,682 | 133 |
| Evil Eye | 9 | 606 | 50 |

The map supports 15 simultaneous monsters across 20 spawn points.

**Where to stand:** Target the four-Duskmander cluster around map coordinates (902, 596), identified in our previous spawn analysis. Actual platform accessibility still needs verification.

**Getting there:** Perilous Descent II → Perilous Descent III → Decayed Tunnel I.

[Private prior benchmark omitted; routing and map ID from the prior response not independently revalidated in this handoff.]

There is also a literal hidden map inside Decayed Tunnel I called **Someone Else's Grave**, but I would prioritize Decayed Tunnel I for sustained farming.

## User
how often do redditers say they get lie detectored?

## Assistant
[Public research answer not fully transcribed; historical source citations not portable. No detection avoidance advice. Reddit anecdotes are not representative rates or evidence of actual enforcement algorithm.]

## User
give me command

## Assistant
```powershell
Start-Process (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Maple Cash Overlay.lnk')
```

## User
LETS MOVE TO NEW CHAT. REMEMBER VERBATUM REMEMBER EVERYTHING AND SAVE TO MEMORY GITHUB AND PULL EVERYTHING FROM GITHUB. NO MORE WORK

## Assistant
I’ll verify the latest GitHub checkpoint, preserve the accessible conversation and update the handoff instructions so the next chat resumes from the repository without repeating the research. No Work or Codex.

[Handoff verification record follows in separate continuation file. No claim of full archival or platform memory synchronization.]
