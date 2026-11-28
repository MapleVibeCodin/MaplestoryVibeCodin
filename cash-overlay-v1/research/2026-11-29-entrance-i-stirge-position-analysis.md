# Forgotten Entrance I Golden Stirge position analysis

User verbatim: now find out best spot in forgotten enterance. big thing for this map, is find out the movement of the stringes. best place to kill for most kilsl per hour of stringes?

Sources: https://meowdb.com/msclassic/maps/010006040 and https://meowdb.com/msclassic/monsters/56; https://ms-classic.com/maps/forgotten-entrance-i. Golden Stirge level 42 HP1278 base EXP93, flying, six of 27 spawn points. Client data ohmi69/osms_datamine_dashboard data/api/v1/maps.json map id 10006040, mob_id 56 at (2203,1179),(1464,1050),(2195,644),(2287,1345),(1106,2005),(231,1945). These are spawn coordinates not flight paths. MeowDB modeled 7.56s wave and shared map cap; not actual individual respawn measurement. Client capacity 18 differs from MeowDB estimated 20.3; not used to estimate actual species rate.

Actual latest extended private ZIP reopened. Filter minimap candidates map Forgotten Entrance I epoch1; 15408 observations, box [4,71,227,143]. Consecutive pairs with positive gap <=.35s and same segment, level, rect, box provide 1565.12s. Take accepted own_exp 93 notifications same map/epoch; 269 total, 160 timestamps contained in valid pairs. Assign to preceding sample in pair; positions in local minimap pixels, not world units. Compare local counts divided by same local observation duration. No correction for capture completeness, selection bias, or shared/bonus awards. Full session conditional EXP decomposition 292 equivalents (412/hr); accepted own awards 269. 
| Local pixel region | valid seconds | awards | local awards/hr |
|---|---:|---:|---:|
| x145.5–149.5 y31.5–35.5 |169.20|54|1149|
| x125–<150 y30–<45 |233.27|63|972|
| x120–<160 y25–<50 |411.84|87|760|
| x75–<100 y60–<75 |141.20|30|765|
| x120–<130 y28–<38 |39.84|5|452|
| x120–<160 y0–<25 |210.47|0|0|
| all |1565.12|160|368|

Inspect actual retained screenshots matched to hotspot (39 images, 14 separated by >20s, 12 viewed as contact sheet). Repeated standing position near left edge of long middle-right platform beside twisted tree, facing gap with two small ladder-connected platforms to left; visible Golden Stirges in gap at different heights, near small ledges and below/above main platform. This supports flight through gap and ability to attack across it, not individual continuous trajectory or attraction mechanism. No full monster ID/death tracking, sparse images cannot establish a deterministic flight loop, facing effect or sustained optimal rate. Local fixed position selected retrospectively, 169 seconds noncontinuous, likely optimistic; prioritize independent controlled trial. Compare stationary at left edge vs small platforms, count +93 awards separately and use full elapsed time. No runtime changes or new tests. No raw private screenshots or account identifiers published; normal ChatGPT only.