# FM Rush v24.20 — native labels and selection-triggered scans

One workspace for current HeneFM deals, purchase receipts, two seller shops and buyer cash.

Buyer: **Unfkabe**. Sellers: **fkable** and **unfkable**, 18 slots each. No third selling shop is assumed.

## Update

Close FM Rush and run **UPDATE_FM_RUSH.bat**, or copy the small ZIP's contents over the existing app folder. Keep `.venv` and `config.json`. Confirm app **v24.20**.

Reload the extension from this app folder in `brave://extensions`, confirm **24.17.0**, then reload HeneFM. If your old extension points to another extracted folder, use Load unpacked on the updated `browser_extension` directory.

The package excludes personal screenshots, replay data, bytecode and the older nested app. Updates preserve local archives, installed dependencies and settings.

## Room-entry scanner

Select the deal before travelling for the first entry search. Selecting a different
live deal after arrival now also starts a bounded scan automatically; it no longer
leaves the finder idle. Already-found labels remain marked when selection changes. Only the
current HeneFM page supplies other names; keep your three-minute page filter.
A found marker remains eligible for two minutes after detection even when its
card disappears. Loading, a lost label or a changed capture window clears its
screen position so an old square cannot point at a different shop.

The locator uses a brief entry burst, a small native-scale pass, fresh-frame
contrast checks during fade-in, and local tracking after verification. A
numbered minimap header can start the selected seller search using the selected
route provisionally; room OCR remains the fallback. It does not read the current
channel from game memory. Ambiguous lettering stays visibly CHECK NAME.

The v24.20 validation used three real-time replays per supplied clip,
with marker callbacks at
8.662–8.664 s (Ceci), 11.832–11.837 s (Tounge), and 14.981–14.990 s
(Gimchigirl, CHECK NAME). Each box was in the annotated shop region. These are
Linux software callback times from compressed desktop video, excluding Windows
capture, GUI/compositor latency, network freshness and other players' actions.
The last deadline has little margin; live Windows racing performance is unverified.

The November 17 label regressions now cover six recovered positions (three exact,
three CHECK). HisCapybara and Kethan remain unverified in their truncated crops;
full game frames are needed. These crop tests isolate recognition and do not
validate live capture or room-entry gating. Selecting a deal after arrival is
separately covered by worker tests, including an unchanged capture frame.

The full checkout includes `benchmark_video_entries.py` and accuracy regressions;
recordings and developer files are excluded from downloads.

## One-time setup

Select **Unfkabe’s game window** in the capture dropdown; seller clients may have the same MapleStory title. A different client's window will show a different room.

Open **Shops & cash → Set current buyer cash / shop setup**. Confirm Unfkabe's actual spendable cash (the form starts at **2M**) and each seller's old occupied slots that are NOT already in this ledger. Blank occupancy means unknown; no automatic shop assignment is made while it is unknown.

The planning defaults are a **500K cash reserve**, a warning above **20% of available cash per purchase**, and **3% estimated sale tax**. They are adjustable warnings, not hidden deal filters. Confirm the tax matches your actual setup. Collection uses actual cash received, not an inferred sale-tax result.

Old screenshots are not treated as proof that an item is still owned. To onboard existing stock, save the blank CSV template and import only currently owned items. Fields: `stock_id,item,stats,quantity,unit_cost,list_price,seller,listed_hours,slots`. Use a stable, unique stock ID where possible. Leave unknown cost or listed age blank; leave seller blank for buyer inventory. Imports do not debit current cash. Imported shop stock replaces the corresponding count of untracked old occupied slots.

## While chasing

All listings on the current HeneFM page remain available. Archived names do not enter the scan queue. Columns show the explicit HeneFM resale price, estimated profit per holding hour, and cash/slow-turnover warnings. Sale-time estimates are heuristics, not guarantees. No CozyFM lookup is required by this workflow.

Choose a deal in the Chase tab. **CHASE MODE · HIDE DESK** hides the large desk while keeping the small target strip, hotkeys and game markers active. Open it again with **OPEN TRADE DESK**.

- **Ctrl+Alt+N:** choose the next current-page deal.
- **Ctrl+Alt+F:** explicitly retry the shop finder.
- **Ctrl+Alt+B:** after actually buying, confirm the selected deal was purchased and advance.

The purchase hotkey records the item, displayed numeric stats, quantity, alert Buy price, explicit HeneFM listing price and expected sale time. Quantity uses the lot count when read; otherwise it starts at one. Verify the visible quantity for bundles. If you paid a different price or bought a different quantity, use **Correct cost / qty** before listing. One receipt is retained per listing; adjust that receipt if you buy additional units from the same listing. A missing Buy price prompts for the actual paid amount; missing resale prices remain unknown rather than being reconstructed from profit.

The text receipt is saved immediately. It does not wait for an image, a folder picker or a screenshot download. **Undo mistaken buy** reverses an unlisted receipt and reopens its deal. Duplicate retries do not debit cash twice, and a short debounce guards accidental double hotkeys.

Screenshot saving is turned **off once on this workflow upgrade**. It can be enabled again in the extension popup; later upgrades preserve that opt-in. Existing PNGs remain untouched. The hotkey creates a text receipt, not another Bought PNG.

## Listing and stock

Inventory shows only unsold stock by default, with stats, paid cost, suggested listing price, seller and actual listed age. Copy listing details when entering your store.

When old occupancy is known, new receipts are assigned to the first seller with room, keeping transfer batches together. Equipment uses a slot per unit; explicit consumable lots use one listing slot. Unknown categories use conservative per-unit accounting. Imported stock can specify slots explicitly. Verify actual game slot usage.

**Shops & cash** groups transfer batches from Unfkabe to each seller. After performing the actual transfer and listing, select the rows and click **Confirm LISTED**. Confirm multiple rows at once when appropriate. This starts their listing age; a restart or repricing does not reset the first-listed date. After at least 12 hours or twice the displayed expected sale time, items get a review reminder for the next planned visit. No automatic price cuts are made.

## Sales and capital

Select only items you verified sold, then use **Confirm SOLD at list price**. This is a user confirmation, not automatic sale detection. It records estimated seller proceeds using the planning tax; it does NOT immediately increase buyer cash.

After the actual mesos transfer, click **Cash received from fkable/unfkable** and enter what Unfkabe really received. The amount can include proceeds from old untracked stock. Cash is credited once per recorded receipt action; the field returns to zero when tracked proceeds have been collected. Reconcile current buyer cash if actual spending, fees or sales outside the ledger caused drift.

When buyer cash is below the reserve, the desk highlights the seller with the most recorded proceeds first. Group transfers and listings into visits instead of automatically restarting both stores or cutting every stale item's price.

Ledger files are in `%LOCALAPPDATA%\FM_Rush\archives\trade_ledger.sqlite3` on Windows, alongside the existing deal archive. Export the ledger to JSON for backup or review. Sold history is hidden until requested. Actual game purchases, listings, sales and account transfers still require your action/confirmation; hotkeys do not send game inputs.

## Scanner timing

Room-entry-only bursts, one OCR thread, a three-second deadline, current-room scoping and large red markers remain. A new page list does not run continuous OCR. The first live list can request one guarded room-entry check when already inside an FM room.

**Export scanner timing** records local page-to-app delivery, room-header, search, queue, frame age and software result-to-UI timing. It does not measure HeneFM server freshness, human travel, network competition or compositor display time. A scanner cannot guarantee winning a race against other buyers; saved-image speed is not proof of live end-to-end speed.

Development tests and replay fixtures remain in the Git repository rather than the runtime ZIP. Run `TEST_LOCATOR.bat` from a full checkout. See `UPDATE_V24_20.txt` for validation and limits.
