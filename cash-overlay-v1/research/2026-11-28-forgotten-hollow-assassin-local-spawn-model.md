# Forgotten Hollow Assassin local-range EXP model — 2026-11-28

User verbatim: ok do your own analysis of forgotten hollow all of the maps. find the best exp using meowdb's xp potential. keep in mind it's wildy wrong if you assume you can kill THE WHOLE MAP. no. assassin you have range, and keep in mind the spawn timer. use that as metric. do calculation for realistic for all forgotten maps

Sources: MeowDB map pages https://meowdb.com/msclassic/maps/010006010 etc; 7.56s modeled server refill tick, shared solo capacity. Live-client coordinates and stats actually retrieved and parsed from ohmi69/osms_datamine_dashboard data/api/v1/maps.json blob f1988748b80dbb49be93013fd82d095441e9cdf2 and monsters.json blob 4ba202ec8f3db1164eb6792ccc51660a518d3cbc; 29 ForgottenHollow map_mark entries, 23 combat. Reach https://meowdb.com/msclassic/guides/weapon-reach and https://ms-classic.com/guides/attack-speed-and-weapon-reach; delay https://meowdb.com/msclassic/guides/attack-speed-and-animation-times. Candidate scan actually executed in JS: for each spawn p, centers x=p.x-400,p.x,p.x+400, y=p.y. Include nonboss q if |q.x-x|<=400 and |q.y-y|<=35. Pair two windows with y difference 71..420 and x separation<=400; no duplicate points because y bands disjoint. This tests geometry neighborhoods, NOT foothold connectivity/standability/line of sight. Low/high scenario effective damage 750/950, refill realization .75/.90 times map cap / all point count, 0.6s cast, one-zone .70 attack uptime, two-zone .55. Hit probabilities assumed 1 for level<=45, .9<=47, .75<=50, .55<=54, .45<=56, .3 above; illustrative, not measured. For each point compute casts ceil(HP/damage)/hit, weighted by refill; EXP sum weighted likewise; scale total by min(1,(7.56/.6*uptime)/weighted casts), multiply 3600/7.56. Optimize lower scenario then upper for ties. Golden Stirge assumed wave-eligible; special timer and flight not independently verified. Boss excluded. Conditional active-map refill scenario, not steady-state alone; if other floors fill all cap, stationary supply may tend toward zero. Rates rounded thousands; not measured or statistical confidence interval.

Map | cap/points | one-zone kEXP/h (point count) | two-zone kEXP/h (point count)
Primeval Forest II |13/19|142-163 (6)|131 (7)
Forgotten Entrance II|26/32|122-146 (5)|120-137 (7)
Perilous Descent III|13/14|115-142 (3)|118 (4)
Decayed Tunnel I|15/20|105-140 (4)|109-131 (7)
End of Fleeting Light|13/25|102-122 (5)|96-110 (5)
Decayed Tunnel II|14/24|98-117 (4)|108-130 (6)
Forgotten Entrance I|18/27|93-112 (4)|114 (5)
Forgotten Entrance III|26/44|92-110 (6)|120-137 (7)
Perilous Descent II|16/29|92-111 (4)|121 (8)
Forbidden Entrance|12/32|89-107 (5)|88-115 (6)
Primeval Forest III|9/11|82-99 (3)|104-114 (4)
Perilous Descent I|13/23|79-94 (4)|74-89 (4)
Dilapidated Tomb|10/24|78-96 (5)|69-84 (5)
Lingering Regret|17/42|77-93 (4)|108-118 (7)
Someone Else's Grave|6/8|76-94 (3)|71-85 (3)
Another Sanctuary|13/27|75-90 (3)|75-90 (4)
Precipice of Darkness|14/37|73-90 (4)|84-113 (6)
Valley of Death|9/26|69-83 (5)|93-116 (8)
Faded Canopy|17/35|67-80 (4)|111-122 (7)
Hanging Gardens of Rot|31/69|66-80 (4)|98-118 (6)
Decayed Tunnel III|9/18|63-75 (3)|87-116 (5)
Primeval Forest I|10/23|50-60 (3)|100-118 (6)
Forgotten Dungeon Tunnel|6/28|32-38 (5)|51-62 (8)

Top single-zone world-coordinate centers (candidate, nearest same-floor standable position required): Primeval II (1101,1765) three Golden Stirge, two Aqumander, one Echopus; Entrance II (2221,1036) three Raffle two Glowshroom; Perilous III (480,1779) two Duskmander one Echopus; Decayed I (902,596) four Duskmander; Entrance III (2839,1563) three Glowshroom three Curse Eye. Faded Canopy two-zone centers (979,1031),(1324,1372), five Echopus two Raffle; not claimed connected. Pure solo static outside-filled minimum local occupancy max(0,C-(N-k)), not guaranteed actual kill rate; Perilous III one zone 2, two zones 3; Primeval III one zone 1, two zones 2; Entrance II two zones 1. No runtime changes or regression execution. Research record includes verbatim user request and numeric findings, not full assistant transcript. No private session measurements published.