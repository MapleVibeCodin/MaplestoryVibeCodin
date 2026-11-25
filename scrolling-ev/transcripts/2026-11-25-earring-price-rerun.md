# Earring price rerun — 2026-11-25

## User

great now do the live pricing using our previous model to find out top 3 best earrings i can self scroll

## Assistant

## Updated result — 1m earring budget

**My preferred choice is still 3% critical damage Pansy Earrings.** However, Red Cross Earrings have emerged as another worthwhile cheap base.

I reran our hard-budget optimization, including failed scrolls, replacement bases, mixed scroll tiers and retaining the best completed item. The calculations also reproduce our previous saved Pansy result when supplied with the old prices.

### Top 3 candidates

**1. Pansy Earrings — level 45**

3% natural CD · 5 unused slots

+8.01 expected effective LUK

Clean base: 14k · 55.5% chance of +8 or better

[HeneFM shop](https://henefm.com/shops/Breathe)

**2. Emerald Earrings — level 30**

2% natural CD · 5 unused slots

+8.34 expected effective LUK

Clean base: 5k · 64.7% chance of +8 or better

[HeneFM shop](https://henefm.com/shops/Tisms)

**3. Red Cross Earrings — level 25**

2% natural CD · 5 unused slots

+8.30 expected effective LUK

Clean base: 5.9k · 63.0% chance of +8 or better

[HeneFM shop](https://henefm.com/shops/Fireball95)

**Pricing limitation:** These are the best suitable base-price observations I could retrieve from HeneFM, not guaranteed live stock. The Emerald listing is from yesterday's indexed data. The model assumes replacement bases are available at similar prices, so verify the actual five-slot listings before purchasing in quantity.

## Updated scroll and ingredient prices

| Material | Purchase price used |
|---|---:|
| Earring DEX Lesser, 100% | 38,500 |
| Earring DEX Intermediate, 60% | 90,000 |
| Earring DEX Greater, 10% | 20,000 |
| Earring LUK Intermediate, 60% | 110,000 |
| Earring LUK Chaos | 310,000 |
| Black Crystal Ore | 3,000 |
| Refined Black Crystal | 4,500 |
| Fragment of Magic | 170 |
| Processed Parchment | 480 |

The 60% DEX scroll is now cheaper than in our previous model, which used 95k.

### Self-crafting Lesser is still cheaper

Using raw Black Crystal Ore and refining it yourself:

20,000+3(3,000+1,200)+10(170)+480 = 34,780

That saves **3,720 mesos per Lesser scroll** compared with buying DEX Lesser at 38.5k, provided you have Arcforge level 8.

## Which strategy wins?

| Earring | Buy all scrolls | Craft Lesser scrolls | Damage-equivalent score | Chance of +10 or better |
|---|---:|---:|---:|---:|
| Pansy 3% CD | 7.986 | 8.006 | **9.686** | 16.3% |
| Emerald 2% CD | 8.324 | 8.343 | 9.463 | 19.7% |
| Red Cross 2% CD | 8.271 | 8.297 | 9.417 | 19.3% |

The first two numerical columns are expected added effective LUK, not actual rolled stats. Damage-equivalent score includes the previous model's approximate 0.56 LUK value per percentage point of natural crit damage. The expensive 4% CD Pansy (250k) scored only 8.718, so it is not worth the premium for this budget.

## What I would do

Buy a clean 3% CD Pansy at 14–15k, open with a 20k DEX Greater, and if the first scroll succeeds, the optimal next action at the initial budget is a 90k DEX Intermediate. If it fails, the model initially restarts on another cheap clean base. Subsequent actions depend on remaining mesos, slots and best retained earring; don't blindly repeat this opener until the budget is exhausted.

A guaranteed +5 option costs 187,900 with five crafted Lesser scrolls. The optimal adaptive strategy has about a 0.68% modeled chance of finishing below +5, so reserve the guaranteed route if that downside is unacceptable.

Catalyst-assisted crafting is not compelling for this self-use objective at the previous 65k catalyst price. Allowing random crafted scrolls to be immediately applied barely changes the expected result (8.006245 to 8.006268 for Pansy). A full inventory-aware crafting optimizer has not been run.

## Get the missing genuinely live quotes

Run this PowerShell block using the existing encrypted HeneFM key, then paste its clipboard output into this chat:

~~~powershell
& {
    $s = Get-Content "$env:LOCALAPPDATA\HeneFM Personal Research\key.dpapi" | ConvertTo-SecureString
    $k = [System.Net.NetworkCredential]::new("",$s).Password
    $q = [ordered]@{
        Pansy = "items/1032012/price?min.crit_damage=3&min.upgrade_slots=5"
        Emerald = "items/1032007/price?min.crit_damage=2&min.upgrade_slots=5"
        RedCross = "items/1032005/price?min.crit_damage=2&min.upgrade_slots=5"
        Star = "items/1032008/price?min.crit_damage=2&min.upgrade_slots=5"
        DEXGreater = "items/2040306/price"
        Catalyst = "items/4130003/price"
    }
    $out = foreach ($name in $q.Keys) {
        try {
            $v = Invoke-RestMethod -Uri ("https://henefm.com/api/v2/" + $q[$name]) -Headers @{Authorization="Bearer $k"} -UserAgent "PersonalPriceResearch/1.0" -MaximumRedirection 0 -ErrorAction Stop
            [pscustomobject]@{Name=$name;Data=$v}
        } catch {
            [pscustomobject]@{Name=$name;Error="Request failed"}
        }
    }
    $out | ConvertTo-Json -Depth 12 | Set-Clipboard
    Write-Host "Price results copied. Paste into ChatGPT."
}
~~~

This requests six on-demand price summaries, not a bulk archive. The filtered equipment calls are new and have not been tested on your PC; the API may suppress prices for thinly traded variants. It does not establish seller-level stock.

[Post-save verification notice omitted.]

## Archive note
Reconstructed visible wording and commands; cards and math flattened, citations omitted from archive. Source URLs and model limitations recorded separately in RESEARCH_HANDOFF.md. No live private API calls executed by ChatGPT.
