# FM Rush v24.15

Mirror the listings shown on HeneFM Deals, keep a persistent deal queue, and mark matching seller names in the selected MapleStory window.

## Install or update

For an existing installation, close FM Rush and extract this small ZIP **over the existing app folder**, choosing to replace app files. Keep `.venv` and `config.json` so dependencies and settings are reused. Run the top-level `START_FM_RUSH.bat` and confirm **v24.15**.

For future updates, close FM Rush and double-click **`UPDATE_FM_RUSH.bat`** in that folder. It downloads the compact package, backs up previous app files under `updates_backup`, and replaces only runtime files. It preserves `.venv`, `config.json`, archives, screenshot folders and purchased images. No Git or Python package reinstall is needed for ordinary updates. If an update changes the browser extension, reload it once in `brave://extensions`, then reload HeneFM. The updater follows the `improve-name-locator` branch.

For a first install, extract the ZIP, run `START_FM_RUSH.bat`, load the top-level `browser_extension` folder with **Load unpacked** in Brave's Developer mode, and reload https://henefm.com/flips/deals.

The download excludes uploaded screenshots, replay fixtures, Python bytecode, development checks and the nested old `FM_Rush_v24_7` copy. Test data remains in the Git repository for development. Existing screenshots on your PC are never deleted by the updater.

## Listings and working selection

- Browser delivery has **no profit threshold or sold-status filter**. It includes low-profit, missing-metric and displayed sold listings. HeneFM's own page filters still determine what is rendered.
- Each listing is archived before receipt is acknowledged. Missing values remain unknown; prices are never inferred from resale values.
- New listings join the queue without changing your working item, seller or route.
- Select a queue row to work on another listing. **DONE / NEXT DEAL** completes only the current item and selects the next pending item. Other items from the same seller remain pending.
- **UNDO DONE** restores the last completed item, including after a restart.
- Pending items and the working selection survive restarts. Completed items stay archived and ordinary resend does not reopen them.
- **EXPORT ARCHIVE** saves a JSON history grouped by seller IGN, including completed listings.

The Windows archive is `%LOCALAPPDATA%\FM_Rush\archives\deal_archive.sqlite3`. It persists across extracted app versions. Close the old app before starting another copy.

## Purchased screenshots

After buying an item, select its listing in FIND NAME and click **BOUGHT · SAVE PNG / NEXT**. The app copies that listing's original screenshot into **`Downloads/Bought/`**, then completes the deal and selects the next one. All purchase PNGs share this single folder, with no seller or date subfolders. **OPEN BOUGHT** opens it for scrolling while you relist. Filenames include item, seller and purchase price; the listing image preserves the displayed stats and resale guidance.

Keep screenshot saving enabled in the extension. If the image is missing, the app asks you to locate `FM_Rush_Item_Screenshots` (useful with a custom browser download directory); cancel to wait for capture. It remembers the chosen source folder. Missing or broken images leave the deal pending. The exact listing ID is matched, so a newer deal cannot replace the purchase screenshot. Repeating BOUGHT after UNDO DONE reuses the same file. UNDO DONE reopens the deal and keeps its purchase PNG.

The extension remains v24.11.0; existing screenshots and archives work with this update. Purchase recording uses a manual click and does not detect game transactions.

## Finding shops

One worker runs a short search burst after you enter an FM room (including a channel change). Starting the locator while already inside a room also runs one burst. It reads the FM room header once, then searches pending seller IGNs archived for that room, plus sellers with an unknown room. Channels cannot be identified from the game header, so all archived channels for that FM number are included. Repeated items from the same seller share one search. It does not visit rooms or channels automatically.

Found sellers get a large **red box, red downward arrow and IGN label**. Ambiguous reads say **CHECK NAME** and use dashed borders; verify the seller. Overlapping candidate names share a CHECK marker. Several distinct shops can stay marked together. Static markers reuse their drawing rather than repainting the whole overlay on every timer tick.

Each entry burst has a three-second deadline, checked between inference batches. It first checks only the strongest visual candidates for each seller, using at most two visual candidates and the existing identity verification. It skips expensive recovery for absent sellers until every queued seller has had this quick sweep. It then runs full recovery for remaining names, with at most two attempts per seller. Once it finishes, **OCR stays idle until the next entry**. New listings remain archived and do not restart idle OCR; movement and queue selection do not restart it either. **FIND AGAIN** explicitly starts another burst. Very large queues can leave sellers unchecked within the deadline; select a seller and use FIND AGAIN to prioritize it. If the FM header cannot be read, automatic name search stays idle; FIND AGAIN can search all pending sellers manually.

OCR remains one thread with the Windows CPU affinity guard. Per-seller cooldowns are removed inside the bounded burst, so it can briefly use more of one core. Between entries, only a lightweight loading-screen watcher remains active: sparse brightness samples and reduced-rate frame copies, with no OCR. Brief black transitions are latched so an entry during inference is not lost. PAUSE stops capture entirely. Model startup and live capture add latency beyond saved-image benchmarks.

## Screenshot archive

The extension saves rendered listing cards under:

`Downloads/FM_Rush_Item_Screenshots/IGN_<seller>/YYYY-MM-DD/`

One PNG is saved per unique listing, with 48-hour deduplication. Filenames include time, seller, item, channel/room, price and fingerprint. Sold entries are labelled. The extension resolves the current card position before capture and skips vanished cards rather than saving another seller's card under the wrong name.

Screenshot saving defaults on; its popup toggle preserves an earlier off preference. Disable Brave's **Ask where to save each file** for automatic saving. A debugger banner may appear; avoid DevTools on the same tab. The archive stays local and can run without the Windows app. Unrendered or vanished cards cannot be captured. Existing screenshots remain in their old directories; new captures use IGN folders.

## Timing and checks

The extension sends a soft-refresh signal every 1.2 seconds; HeneFM can ignore or delay it. This does not guarantee fresh site data. No private HeneFM endpoints are used and the page is not rewritten.

Development checks are available from a full Git checkout: run `TEST_LOCATOR.bat`. `benchmark_name_finder.py` measures saved-image recognition and optional simulated target-arrival CPU stress. These exclude live capture, GUI dispatch and marker drawing; live Windows behavior still needs a game-session check. `benchmark_entry_burst.py` compares warm room-entry latency against v24.11; see `benchmark_entry_v24_12.json` and `UPDATE_V24_12.txt`.

Discord/OCR alerts retain the separate **15,000 mesos AND 15%** filter. Browser listings do not use it.

The v24.14 queue replay (`benchmark_queue_sweep.py`, `benchmark_queue_v24_14.json`) compares the same room queue against v24.13: six absent sellers before two visible sellers improved from 914 ms to 290 ms median in three warm runs. It excludes startup, live capture and GUI; live results vary. See `UPDATE_V24_14.txt`.
