# FM Rush v24.11

Mirror the listings shown on HeneFM Deals, keep a persistent deal queue, and mark matching seller names in the selected MapleStory window.

## Install or update

1. Close the old FM Rush app. Extract the new ZIP into a fresh folder.
2. In `brave://extensions`, disable/remove the old FM Rush extension. Enable Developer mode, choose **Load unpacked**, and select the new top-level `browser_extension` folder.
3. Reload https://henefm.com/flips/deals.
4. Run the top-level `START_FM_RUSH.bat`. Confirm **v24.11** in the title and select MapleStory in FIND NAME.

Use the launcher at the ZIP's top level; the nested `FM_Rush_v24_7` directory is an older copy. Dependencies and extension permissions have not changed.

## Listings and working selection

- Browser delivery has **no profit threshold or sold-status filter**. It includes low-profit, missing-metric and displayed sold listings. HeneFM's own page filters still determine what is rendered.
- Each listing is archived before receipt is acknowledged. Missing values remain unknown; prices are never inferred from resale values.
- New listings join the queue without changing your working item, seller or route.
- Select a queue row to work on another listing. **DONE / NEXT DEAL** completes only the current item and selects the next pending item. Other items from the same seller remain pending.
- **UNDO DONE** restores the last completed item, including after a restart.
- Pending items and the working selection survive restarts. Completed items stay archived and ordinary resend does not reopen them.
- **EXPORT ARCHIVE** saves a JSON history grouped by seller IGN, including completed listings.

The Windows archive is `%LOCALAPPDATA%\FM_Rush\archives\deal_archive.sqlite3`. It persists across extracted app versions. Close the old app before starting another copy.

## Finding shops

One worker searches all pending seller IGNs against the current selected game window, deduplicating repeated items from the same seller. It does not visit other rooms or channels automatically.

Found sellers get a large **red box, red downward arrow and IGN label**. Ambiguous reads say **CHECK NAME** and use dashed borders; verify the seller. Overlapping candidate names share a CHECK marker. Several distinct shops can stay marked together. Static markers reuse their drawing rather than repainting the whole overlay on every timer tick.

New arrivals do not cancel a seller already being searched. Each seller gets a bounded search/retry sequence; room changes, name movement, new listings or **FIND AGAIN** can rearm searches. A selected missing seller is prioritized within the shared CPU budget. Capture pauses when the pending queue is empty.

OCR remains one thread, with the Windows CPU affinity guard and a shared sustained search budget targeting 35% of one logical CPU. Capture, UI and Discord work are additional. Large queues take time; cooldown after an expensive search can delay another target.

## Screenshot archive

The extension saves rendered listing cards under:

`Downloads/FM_Rush_Item_Screenshots/IGN_<seller>/YYYY-MM-DD/`

One PNG is saved per unique listing, with 48-hour deduplication. Filenames include time, seller, item, channel/room, price and fingerprint. Sold entries are labelled. The extension resolves the current card position before capture and skips vanished cards rather than saving another seller's card under the wrong name.

Screenshot saving defaults on; its popup toggle preserves an earlier off preference. Disable Brave's **Ask where to save each file** for automatic saving. A debugger banner may appear; avoid DevTools on the same tab. The archive stays local and can run without the Windows app. Unrendered or vanished cards cannot be captured. Existing screenshots remain in their old directories; new captures use IGN folders.

## Timing and checks

The extension sends a soft-refresh signal every 1.2 seconds; HeneFM can ignore or delay it. This does not guarantee fresh site data. No private HeneFM endpoints are used and the page is not rewritten.

Run `TEST_LOCATOR.bat`. `benchmark_name_finder.py` measures saved-image recognition and optional simulated target-arrival CPU stress. These exclude live capture, GUI dispatch and marker drawing; live Windows behavior still needs a game-session check. See `UPDATE_V24_11.txt` and `benchmark_v24_11.json`.

Discord/OCR alerts retain the separate **15,000 mesos AND 15%** filter. Browser listings do not use it.
