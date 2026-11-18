# FM Rush v24.25 — choose a listing, scan one seller

Current HeneFM deals, purchase receipts and shop stock in one app.

## Installation

Close the old app. Extract the entire clean ZIP and run **START_FM_RUSH.bat**.
Keep the included assets folder: the English recognition model is essential.
The clean download contains no screenshots, videos, old versions or update notes.
Extracting over an existing app folder reuses its installed `.venv` and settings;
a new folder installs dependencies on its first launch. Purchase records remain
in `%LOCALAPPDATA%\FM_Rush\archives`.

Load the included **browser_extension (24.22.0)** in `brave://extensions`, replacing
or reloading the old extension, then reload HeneFM. This step enables listing
clicks and CHASE/SKIP buttons. Keep your three-minute Deals filter.

## Choose what to chase

Incoming listings are available without being assigned. Click a listing anywhere
on HeneFM or press its **CHASE** button. That seller becomes the only OCR target;
new arrivals do not replace it. A green outline confirms the choice was delivered.
You can also choose a row in the desktop Chase tab.

**SKIP** on a HeneFM card dismisses that listing. Skipping another card leaves your
current choice alone. **SKIP DEAL / Ctrl+Alt+N** clears the selected deal without
recording a purchase or selecting another one. Click another listing whenever
you want. Clicking CHASE on a skipped card reopens it.

**Ctrl+Alt+B** confirms the selected purchase, records its item/stats/prices and
clears the chase target. It does not automatically take the next deal.
**FIND AGAIN / Ctrl+Alt+F**, or clicking the chosen listing again, retries scanning.

## In-game highlights

Open MapleStory's channel menu normally. A transparent, click-through red cell
outline and arrow mark the chosen channel directly over the real menu. Its
position is anchored to the menu from the uploaded screenshot; it follows the
selected game window and hides when the menu closes. It never clicks for you.

The name reader begins on the early light frames of the room fade. During the first 125 ms of room entry, the reader checks one candidate per fresh frame. It verifies the letters with a prewarmed OCR model. The wider search follows if the first passes do not find a match. It retries
without the previous quarter-second delay, searches only the selected live IGN,
and accepts three confidently read letters for a **CHECK NAME** shop marker.
Repeated identical letters and weak readings do not qualify. Loading, resizing
or lost lettering clears stale positions. Selecting another listing clears the
old seller's marker, including queued results from the previous choice.

A bounded worker indexes only the newest queued view. Room-header OCR and a
heavy full-room detection pass cannot delay live searches. OCR stays within a
three-second entry/retry burst; idle watching does no OCR. Found positions can
stay eligible for 120 seconds after detection if their alert leaves the page,
until you change or clear your choice. An off-page selected purchase stays
available for receipt logging, but its unfound seller is not scanned.

The v24.24 replay marked the correct shop in 15 of 15 runs across five supplied clips, 22–38 ms after each fixed readable fade reference. Video replay measures the software marker callback. Native Windows capture,
GUI/compositor latency and network competition remain outside that measurement;
an instant successful identification is not guaranteed on every fade frame.

## One-time setup

Select **Unfkabe’s game window** in the capture dropdown; seller clients may have the same MapleStory title. A different client's window will show a different room.

Open **Shops & cash → Set current buyer cash / shop setup**. Confirm Unfkabe's actual spendable cash (the form starts at **2M**) and each seller's old occupied slots that are NOT already in this ledger. Blank occupancy means unknown; no automatic shop assignment is made while it is unknown.

The planning defaults are a **500K cash reserve**, a warning above **20% of available cash per purchase**, and **3% estimated sale tax**. They are adjustable warnings, not hidden deal filters. Confirm the tax matches your actual setup. Collection uses actual cash received, not an inferred sale-tax result.

Old screenshots are not treated as proof that an item is still owned. To onboard existing stock, save the blank CSV template and import only currently owned items. Fields: `stock_id,item,stats,quantity,unit_cost,list_price,seller,listed_hours,slots`. Use a stable, unique stock ID where possible. Leave unknown cost or listed age blank; leave seller blank for buyer inventory. Imports do not debit current cash. Imported shop stock replaces the corresponding count of untracked old occupied slots.

## While chasing

All listings on the current HeneFM page remain available. Archived names do not enter the scan queue. Columns show the explicit HeneFM resale price, estimated profit per holding hour, and cash/slow-turnover warnings. Sale-time estimates are heuristics, not guarantees. No CozyFM lookup is required by this workflow.

The compact strip opens below MapleStory when there is room. **Tools → Place under game** repositions it after you move the game. **Trade Desk** opens the full desk, and **Inventory** opens your purchase and listing prices directly. **Hide desk** returns to the strip.

- **Ctrl+Alt+N:** skip the chosen deal and wait for another choice.
- **Ctrl+Alt+F:** explicitly retry the shop finder.
- **Ctrl+Alt+B:** after actually buying, record the selected purchase and clear the target.

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

Room-entry bursts, one OCR thread, a three-second deadline, current-page scoping and large red markers remain. A new page list does not run continuous OCR. Choosing a live listing can request a guarded entry check when already inside an FM room.

**Export scanner timing** records local page-to-app delivery, search, queue, frame age and software result-to-UI timing. It does not measure HeneFM server freshness, human travel, network competition or compositor display time. A scanner cannot guarantee winning a race against other buyers; saved-image speed is not proof of live end-to-end speed.

Development tests and replay fixtures remain in the Git repository rather than the runtime ZIP. Run `TEST_LOCATOR.bat` from a full checkout. See `UPDATE_V24_22.txt` for validation and limits.
