# FM Rush v24.7 — Earlier room-entry scan

## Install

1. Close the running FM Rush app.
2. Extract this ZIP into a new folder and run START_FM_RUSH.bat.
3. Replace the older Brave extension with the bundled browser_extension folder (see browser_extension/README_INSTALL.txt), then reload the HeneFM tab.
4. Select the MapleStory window in FIND NAME if needed. Enter the room, change channel, or press FIND AGAIN.

The window title must say v24.7. Compact controls and the click-through in-game marker remain. Green HERE means exact text recognition. Yellow CHECK means ambiguous lettering or overlap: check the seller before buying.

## Faster search

The first pass searches a half-size feature image for candidate locations. Each candidate is refined against ORIGINAL-resolution pixels and verified by text recognition before any marker is shown. This reduces full-window matching work without drawing speculative markers.

The fast recognition pass uses a 160-pixel minimum input width instead of padding every name to at least 320 pixels. Long names still expand to their required width. When this changes recognition on an overlapping tag, the original padding is retried on just those candidate patches. If no candidate verifies, the original full-resolution search remains as recovery.

Capture now accepts a frame every 16 ms instead of v24.6's 33 ms (up to approximately 60 copies/second). The loading gate scans on the first pair of stable visible samples, with no extra settling timer. It still rejects black frames and changing fade brightness. Nominal pre-recognition wait after brightness settles is approximately 16–32 ms, plus worker polling (up to about 8 ms) and scheduling; actual Windows/game frame delivery may be slower. Name recognition time and GUI dispatch are additional.

GUI event dispatch remains 10 ms. Recognition remains one thread and only runs on target changes, room transitions, camera movement or manual retry, with one bounded retry after a miss. The higher frame-copy rate can increase capture overhead; this does not enable continuous OCR.

v24.7 validation: six timing-gate and worker tests passed, including fade rejection, repeat channel transitions, stale-target suppression and bounded retry. The recognition algorithm is byte-for-byte unchanged from v24.6; the following recognition tests and benchmark results are from that version.

v24.5 fixes remain: the top row is included, both crop contexts are checked, short names require two agreeing reads, and ambiguous extra border/overlap glyphs produce a yellow CHECK marker. There is no continuous OCR or large preview.

## Timing comparison

Five warmed screenshot replays per sample, both versions measured in the same Linux runtime. These are algorithm times, excluding capture, fade settling and drawing the Windows marker.

| Seller | v24.5 median | v24.6 median |
| --- | ---: | ---: |
| Cernia | 284.2 ms | 84.1 ms |
| Rollermo | 467.2 ms | 195.6 ms |
| jtedoigte | 170.7 ms | 84.4 ms |
| iSadlyfe | 156.7 ms | 84.1 ms |
| Oral | 311.1 ms | 165.3 ms |
| FoxGod | 151.1 ms | 77.8 ms |
| Kilerious | 170.2 ms | 159.2 ms |
| Snapkin (no readable match) | 148.9 ms | 257.8 ms |

Recovery can be slower on unreadable names. Measurements vary with machine and load; this is not a guarantee of end-to-end speed on your PC. See benchmark_v24_6.json for the measured results. The 1.2-second HeneFM soft-refresh signal remains a separate upstream delay and does not guarantee a network update.

## Verification

Seven readable reported sellers locate correctly in saved-image replay: FoxGod, Oral, Kilerious, jtedoigte, iSadlyfe, Cernia and Rollermo. Marker coordinates are checked against the names, not desktop alert text. Game-only crops are used and visible desktop-panel occlusions are masked.

Kilerious, Cernia and Rollermo produce CHECK markers in these samples. Snapkin is not legibly identifiable in its supplied frame. Kilerious is not present in the supplied FM15 frame; the readable sample is FM17. Those two samples remain no-match checks.

Existing tests cover Mora, dark lettering on light tags, duplicate names, absent names, prefixes, similar spellings, loading transitions, stale target suppression and bounded retries. All 15 finder, reported-miss, worker and new timing-gate tests passed. A further 20 resized/dimmed-image comparisons retained all 15 detections that v24.5 could make. Two small Rollermo variants remained unreadable in both versions.

See benchmark_v24_6.json for five-run warmed Linux replay timings. These exclude Windows capture, waiting for a stable frame, and drawing the native marker. Live Windows capture and end-to-end latency cannot be verified here. Obscured letters, different fonts and extreme resizing can still miss.

Run TEST_LOCATOR.bat after setup to replay the included finder/worker tests.

## Browser feed

The bundled Brave extension is v24.4.1: 1.2-second soft-refresh default; unsold unusually-cheap flagged deals OR at least 15,000 mesos profit AND 15%; backup reload off. Install/update resets the saved refresh interval to 1.2 seconds. Discord/OCR alerts also use 15,000 mesos AND 15%.


## Deal scanner repair (v24.7.2 / Brave v24.5.0)
- Deals are recorded as delivered **only after** FM Rush acknowledges receipt. Earlier builds marked them seen before delivery, so an app-disconnected tab reload could skip them permanently.
- In Brave's FM Rush popup, watch Seller links seen / Listing cards found / Profit cards parsed / Qualified deals / Pending unsent / Sent to FM Rush / Windows app status.
- Use Resend visible deals to reset the session's delivered list and route currently eligible cards again. May produce duplicate pings.
- Keep HeneFM open at https://henefm.com/flips/deals; reload that tab once when updating the extension. Start the Windows app before browsing to route deals immediately.
- Refresh signals run every 1200ms but HeneFM may ignore refresh events; the public site displays deal listings with a stated 60-second delay for free access.
