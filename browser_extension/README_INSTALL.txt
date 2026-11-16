FM Rush v24.7 / Brave extension v24.5.0 — November 14, 2026

CHANGES
- Soft refresh: 1,200 ms (default).
- Browser deal forwarding: profit at least 15,000 mesos AND at least 15%, OR an unsold card marked "Unusually cheap: check it is still there".
- Windows app's Discord/OCR profit filter: at least 15,000 mesos AND 15%.
- No page rewrite; sold cards are excluded; default backup page reload is OFF.
- This is a soft refresh *signal* every 1.2 seconds; the actual site may rate-limit or ignore it.

INSTALL / UPDATE
1. Close FM Rush and extract the ZIP to a new folder on disk.
2. In Brave, open brave://extensions and disable/remove the older FM Rush extension so only one version runs.
3. Enable Developer mode, click Load unpacked and select the extracted browser_extension folder.
4. Reload the existing HeneFM Deals tab once. The saved refresh is set to 1,200 ms on extension install/update.
5. Run START_FM_RUSH.bat and confirm the browser status from the extension icon.

URL: https://henefm.com/flips/deals
NOTE: A 1.2s signal does not prove a fresh network response or guarantee deal discovery time; repeated refreshes can cause HeneFM HTTP 429 responses.

REPAIR v24.5.0
- Old extension marked deals seen before delivery. If Windows app was offline and tab reloaded, no deals were forwarded again. Now only successful sends persist.
- Diagnostics in Brave popup now show links detected, cards found, profit cards parsed, qualified, queued, sent, and whether app listening on localhost.
- Use 'Resend visible deals' to intentionally resend qualifying visible cards (may produce duplicate pings).
- The scanner reads HeneFM page DOM only; the 1200ms 'soft refresh' signal is not a guarantee HeneFM will request new server data. HeneFM publicly notes 60-second delayed free access.

NEW IN v24.8: SCREENSHOTS
- Each rendered item card on your HeneFM Deals page can be captured to a PNG automatically, even when below the 15k/15% alert filter.
- Location: Brave's Downloads/FM_Rush_Item_Screenshots/YYYY-MM-DD/ directory.
- Checkbox in FM Rush popup enables/disables capture. Enabled by default.
- Requires new debugger/downloads permissions. Chrome/Brave may show the browser debugging notification during capture.
- Avoid opening DevTools in the same HeneFM tab while screenshot capture runs.
- Turn OFF Brave Settings > Downloads > "Ask where to save each file" for no download prompts.
- The screenshot archive is independent of FM Rush's Windows app.
- Screenshot capture is not guaranteed for content that HeneFM does not actually render; queued items can disappear before being captured.
