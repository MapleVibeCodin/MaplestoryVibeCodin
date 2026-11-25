# Claw catalyst and clean-variant research — 2026-11-25

User: "also run the variable of using 2h weapon catalyst. do all the research to find out what the odds are. also research how much each variant (+1 clean, +2 clean, +3 clean) costs on henefm"

## Findings
2H catalyst is accepted on Avarice claw upgrades. No verified official roll probability table was found. Anecdotal reports include 8 level-40 claws: 6 unchanged, 2 negative; a -3 Avarice; 3 weapon crafts: 2 unchanged, 1 negative; 3 two-handed crafts all -2/-3; Vaulter 2000 +2 attack. These are separate anecdotal reports, not pooled unbiased data. Negative, unchanged and positive attack rolls possible. Scroll catalyst 75/20/5 must not be transferred to weapon crafting.

HeneFM indexed snapshots, not synchronized live quotes or guaranteed availability; all clean variants require 7 slots remaining:
| Base | Standard | +1 | +2 | +3 |
|---|---:|---:|---:|---:|
| Steel Avarice |32k|38.1k|130–135k|555.6k|
| Adamantium Avarice |70–90k|328.9k|900k|unverified|
| Blood Avarice |unverified|73–200k|400k sold|unverified|
| Dark Avarice |85k|200–300k|750k|unverified|
| Steel Slain |2.1–2.6m|2–3.3m|4.65m|unverified|

HeneFM pages https://henefm.com/items/1472014, https://henefm.com/items/1472016, https://henefm.com/items/1472015, https://henefm.com/items/1472017, https://henefm.com/items/1472018, https://henefm.com/items/4130001. Catalyst observed 33.5–38.9k on recent indexed offers, older snapshot 80k+. Adamantium Ingot observed average sold around 350. Adamantium upgrade level9 recipe Steel Avarice +5 Adamantium Ingot +40k fee + optional 2H catalyst, https://maplefm.gg/crafting/weaponcrafting/. Community report input attack doesn't carry over https://www.reddit.com/r/MSClassicWorld/comments/1xhcjal/quick_question_about_weaponcrafting_stats_do/ ; not independently verified. Catalyst anecdotes https://www.reddit.com/r/MSClassicWorld/comments/1xh0vr1/how_do_crafting_catalysts_work/ and https://www.reddit.com/r/MSClassicWorld/comments/1xqrvtw/whats_your_experience_been_with_using_catalysts/.

## Actual model run
Craft cost 35k Steel +2k ingots +40k fee +40k catalyst=117k, round up120k. Sensitivity160k. NPC recovery10k assumed. Standard Adamantium Avarice natural29ATT buy70k. Scrolls L70k +1 guaranteed, I600k +2 60%, G65k +4 10%; Chaos unpriced excluded. Hard5m. No citizenship. Three explicitly hypothetical distributions for -3,-2,-1,0,+1,+2,+3: conservative [.03,.10,.12,.65,.06,.03,.01], middle [.03,.10,.12,.50,.15,.07,.03], optimistic [.03,.10,.12,.35,.20,.12,.08]. Not observed odds, not proof +3 is maximum. Float32 Numba DP 5k grid, state liquidation wealth m, active attack a and remaining slots r, best parked attack b (not rescrolled). No-active state stop/buy/craft; active stop/NPC/restart/park best/apply. First surviving failed scroll mandatory NPC. Wealth includes NPC salvage of retained items, actual cash checked for purchase, craft and scroll. E final attack maximize, cash secondary tie-break; E crafts tracked. One active and one parked only; no FM resale or joint multiple-inventory optimizer.

| Policy | E final ATT | E net spend k | E crafts |
|---|---:|---:|---:|
| Buy-only |40.3516884|4829.97665|0|
| Buy/craft120 conservative|40.3550873|4845.38603|.391183|
| Buy/craft120 middle|40.4943352|4839.91007|11.686218|
| Buy/craft120 optimistic|40.9542542|4836.54888|13.519449|
| Craft-only120 conservative|40.0415154|4836.60927|13.222161|
| Craft-only120 middle|40.4855766|4828.82488|12.592204|
| Craft-only120 optimistic|40.9528465|4831.34916|13.792452|
| Buy/craft160 conservative|40.3518448|4837.97873|.120316|
| Buy/craft160 middle|40.3630486|4837.66161|.533465|
| Buy/craft160 optimistic|40.6966209|4832.19908|9.305442|

Simple 10 crafts with a standard70k fallback, NPC all discarded at10k, seven Lesser finish490k: total net1660k, middle scenario expected final37.857584; probabilities >=+1 .9436865, >=+2 .6513216, >=+3 .2625759. Conservative .6513216/.3351674/.0956179 and optimistic .9939534/.8926258/.5656115. These probabilities are scenario-based and assume independent rolls. Buying clean +2 Dark at750k or Adamantium at900k and seven Lesser produces38 ATT for1.24m or1.39m; better than 10-craft middle policy on both expected cost and ATT, subject to actual stock. No actual purchases, authenticated prices, or engine integration. Save is structured research, not full verbatim archive.
