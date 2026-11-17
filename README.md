# FM Rush v24.21 — replacement room text reader

Current HeneFM deals, purchase receipts and shop stock in one app.

## Installation

Close the old app. Extract the entire clean ZIP and run **START_FM_RUSH.bat**.
Keep the included assets folder: the English recognition model is essential.
The clean download contains no screenshots, videos, old versions or update notes.
Extracting over an existing app folder reuses its installed `.venv` and settings;
a new folder installs dependencies on its first launch. Purchase records remain
in `%LOCALAPPDATA%\FM_Rush\archives`.

The bundled browser extension remains **24.17.0**. If using a new folder,
load that folder's `browser_extension` directory in `brave://extensions`, then
reload HeneFM. Keep your three-minute Deals filter.

Older in-place updaters cannot accept the new model asset. Use this complete
clean ZIP for the transition to v24.21 instead of the old update launcher.

## Replacement scanner

The scan controller and reader are replaced. Selected-name shapes propose
locations, and an English recognition model verifies the actual lettering.
Other live sellers share a room text index. Location hints are retried during
the entry fade; a shape proposal alone never establishes identity. Room-header
OCR never blocks name recognition.
Only the current HeneFM page supplies targets; archived sellers are excluded.

A separate region worker keeps the newest readable entry snapshot while OCR
is busy. Old queued views are dropped rather than delaying the next scan. Results retain their source frame and are relocated against the newest
capture before a marker is published. Loading, a changed capture size and lost
lettering invalidate positions. Inference is confined to a three-second entry
burst, with a bounded retry when selecting another live deal. There is no idle
OCR. OCR uses one thread; Windows process affinity remains capped at two CPUs.

Select the deal before travelling to put its seller first. **FIND AGAIN** or
**Ctrl+Alt+F** starts another bounded scan. Found positions stay eligible for
120 seconds from detection even if the page drops their card. Current live
sellers can remain marked longer. Unfound off-page sellers are dropped promptly.

Three clearly read letters are enough for a fast **CHECK NAME** marker. The
fragment must distinguish that seller from the other live targets; repeated
identical letters and low-confidence fragments do not qualify. This intentionally
accepts partial names and similar names sharing those letters. Full-name
confirmation is no longer required before showing a useful location.
The app never clicks a shop or buys an item automatically.

The full source checkout includes real-time video replay and recognition tests.
Video times measure the software marker callback, excluding native Windows
capture, GUI/compositor latency and other players. Live Windows racing latency
still needs checking; a replay is not a guarantee of winning a purchase.

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

Room-entry bursts, one OCR thread, a three-second deadline, current-page scoping and large red markers remain. A new page list does not run continuous OCR. The first live list can request one guarded room-entry check when already inside an FM room.

**Export scanner timing** records local page-to-app delivery, search, queue, frame age and software result-to-UI timing. It does not measure HeneFM server freshness, human travel, network competition or compositor display time. A scanner cannot guarantee winning a race against other buyers; saved-image speed is not proof of live end-to-end speed.

Development tests and replay fixtures remain in the Git repository rather than the runtime ZIP. Run `TEST_LOCATOR.bat` from a full checkout. See `UPDATE_V24_21.txt` for validation and limits.
