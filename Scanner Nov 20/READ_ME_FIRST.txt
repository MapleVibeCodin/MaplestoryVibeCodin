FM RUSH v24.37 — SCANNER

INSTALL
1. Extract the ZIP and open the Scanner Nov 20 folder.
2. Run START_FM_RUSH.bat. The launcher provisions its Python 3.12 environment as needed.
3. Brave > chrome://extensions > Developer mode > Load unpacked > choose this NEW
   browser_extension folder if the FM Rush extension is not already installed.
4. Open https://henefm.com/flips/deals in Brave.
5. Choose MapleStory in the main strip and click Start locator if needed.
   Click Refresh after opening or restarting the game.
6. Use Tools > FM map for the built-in portal map.

HOW IT WORKS
- Before the game OCR finishes, the top listing already sets the channel and FM
  route. A click-through yellow target-channel reminder appears in MapleStory.
- When the actual channel-change menu is open, its destination cell is outlined.
- The seller IGN is located by the existing nameplate finder.
- NEW: The browser passes HeneFM's own item icon (or its official image URL) to
  the app, which loads/prepares it before you enter the shop. When the shop
  shows the matching pixels, small click-through GREEN CORNER BRACKETS mark candidate
  item icon locations WITHOUT covering the artwork or adjacent item names.
  No full-screen item text OCR is needed.
- CHASE/LOCK retains seller, item and route; UNLOCK resumes first live listing.
- Temporary manual map previews return to first listing after 60 seconds.

IMPORTANT ITEM LIMITS
- This is *icon recognition*, NOT a proof that equipment stats, number of slots,
  quantity or asking price match the HeneFM listing. Inspect the actual item
  and price before buying. Identical icons are all marked as candidates.
- No marker is shown when the icon is unavailable, not visibly present, scaled
  incompatibly or cannot be matched confidently. Never guess a location.
- No purchase or player-movement automation and no game memory access.

LATENCY
- Local pure image-match benchmark on synthetic 1920x1080 frames: median
  ~25 ms, 95th percentile ~39 ms in a 50-run measurement. The first cold pass
  and operating-system scheduling can exceed 50 ms. No claim is made that
  screenshot capture, HeneFM delivery, overlays, or end-to-end recognition
  are guaranteed under 50 ms on your particular Windows machine.
- Matching is CPU-bound, single-scale, performed on existing window capture.
  The game window must be in front for in-game markers to appear.
