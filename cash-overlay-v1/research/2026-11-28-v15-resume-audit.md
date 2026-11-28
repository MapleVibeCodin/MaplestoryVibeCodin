# Cash Overlay v1.5 resume audit — 2026-11-28

## User (verbatim)

START GITHUB MEMORY.

Repository: https://github.com/MapleVibeCodin/MaplestoryVibeCodin

Resume Maple Cash Overlay v1.5 from verified checkpoint 5ee32bab0b87cda77b8115899437acc0b10beaba.

Read AGENTS.md, checkpoints/LATEST.md, and cash-overlay-v1/NEXT_CHAT_HANDOFF.md in full. Recover all relevant research, source code, previous failures, benchmarks, requirements and regression tests. Verify HANDOFF_MANIFEST.json and run all 10 continuity checks.

The primary objectives are map quality (EXP/hr, mesos/hr, mobs/hr) and personal farming efficiency (mob movement, kill speed, spawn pressure, neglected platforms, player population, inventory and potion consumption, and MeowDB comparisons).

Preserve all previous versions and raw evidence. Do not repeat completed research. Distinguish observed facts from estimates. Continue improving the actual implementation and update GitHub after every substantive exchange. Give single copy-paste PowerShell commands. Never suggest Work or Codex.

## Assistant visible opening (verbatim, markup retained)

I’ll verify the checkpoint, recover the handoff and implementation, then check the manifest and continuity requirements before making any changes.

# Maple Cash Overlay v1.5 — GitHub recovery

<row align="center">
  <icon name="check-circle-filled" color="success" size="xl"/>
  **Requested GitHub checkpoint verified**
</row>

GitHub confirms that `main` is identical to your requested checkpoint. No newer or divergent commits were found.

| Component | Verified reference |
|---|---|
| Handoff checkpoint | `5ee32bab0b87cda77b8115899437acc0b10beaba` |
| v1.5 runtime | `585ebb8c2b08e33e452b9b92a6632537d1c644cf` |
| Upstream engine | Javipen/maple-exp-overlay |
| Runtime manifest | 23 files |
| Installer dependencies | 15 project files |

[GitHub repository](https://github.com/MapleVibeCodin/MaplestoryVibeCodin) · [Handoff document](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/5ee32bab0b87cda77b8115899437acc0b10beaba/cash-overlay-v1/NEXT_CHAT_HANDOFF.md)

All 23 manifest blob IDs match GitHub. The history comparison also shows zero removed paths. I’m checking the runtime’s test coverage and separating implemented features from those still awaiting live validation.

## Static continuity audit (not transcript)

1. Repository/version: main identical to 5ee32bab0b87cda77b8115899437acc0b10beaba before audit. Source Cash 1.5. Runtime 585ebb8c2b08e33e452b9b92a6632537d1c644cf. Runtime-to-handoff one commit, four documentation/manifest paths only.
2. Architecture: actual source of cash_overlay.py, inventory_ui.py, hybrid_capture.py, scene_analysis.py and research_analysis.py read; all 23 manifest files retrieved and GitHub-reported blob IDs matched 23/23. Other core/test files inventoried, not every line manually inspected. No independent local hashing or execution this turn.
3. Map coverage: exact name match and Primeval Forest I reference 010006010 only; no global map calibration or actual spawn-cap proof. Source model 23 points, cap10, 7.56s tick, 952 mobs/hr, 88949 EXP/hr. Reference not freshly reverified externally this turn.
4. Camera confidence/fallback: ORB robust masked translation, uncertain registration breaks tracks; anonymous candidate speed/recurrence, not kills/respawns. No live detector calibration.
5. Calibration and prior failures: full FIRST_CAPTURE_QUALIFICATION, compression benchmark, five-minute method, research objectives, README, spatial source catalog and TEST_EVIDENCE read. 79 v1.3 frames, 1.010s mean cadence, ~529 KB/frame; occluded map, missed pickup OCR, 34 negative metadata ages. v1.4 ordering/relocation logic present; live recall and placement unverified. No actual local archive attached.
6. Passive workflow: 2Hz target/4Hz bursts, lossless crops, use/etc/pet reminders, no input; exact item quantity and complete tab coverage unknown. Upstream base pinned; hotkeys off by default.
7. Installer: all 15 referenced project files present in matched manifest; exact pinned upstream, new timestamped build, venv, compile and five test suites. 31 test methods counted (5+7+5+6+8), historical five core and isolated synthetic camera tests documented; no new execution or Windows installation verified.
8. Data retention: absolute LocalAppData roots, unique builds and analysis outputs, 5 GiB guard, no deletion, no public raw personal evidence. Compare from 5a6c2831fefd4dffbb3eb9b91bc05d264c3e66d4 to handoff: nine commits ahead, zero removed paths. Previous v1.3 to runtime comparison eight commits. Local filesystem not inspected.
9. Outstanding validation: v1.5 capture health, real actor templates, message recall, inventory/potion reconciliation and real combat association unverified. Source-level finding: research_analysis.analyze segments by map/level/segment but does not filter by active flag; current endpoint rates must not be represented as active-only. Reviewed combat CSV lacks session ID; use review for a single session only as documented. These are review findings, not newly fixed or executed failures. Next real session/replay before further claims.
10. Checkpoint workflow: complete handoff and manifest read; both full master documents retrieved (AGENTS 320 lines, LATEST 430 lines), relevant sections and mandatory ten-check instructions inspected. Full line-by-line human/model review of unrelated historical sections incomplete due output limit. Prior 20-point protocol recovered. Canonical pointer to be updated, append-only record. Earlier full dialogue and raw attachments not recovered, final post-write response not archived in this pre-write record. No runtime code changes or new live tests. No claims of background synchronization.

No prior raw data copied to public GitHub; all previous versions preserved. Resume from verified v1.5 runtime, not a new release.
