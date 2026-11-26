# Windows historical replay checkpoint — 2026-11-26

User-provided FM_Rush_Lab7_Replay.json, SHA-256 075f8fb32d2ecda968a2a89b8628291f1544a079de0464837afba48a963b5d94. Corrected candidate fcc23d02c441541f026e447a7fe0b6a9de563a60 per preceding checkout and command; replay itself does not embed commit identity.

- Archive members verified: 57. Errors: none.
- Ten original recordings, 5,777 decoded frames, 199 sampled frames. All ten prior_match flags true; 47 geometry-positive and 140 room-positive samples. Six clips have one fewer decoded frame than metadata. Exact native shop gate: zero positive samples on compressed videos.
- 42 PNGs decoded, ten exact anchors all confirmed by geometry; prior_match null for every PNG because optional prior summary was not supplied.
- 116 unique historical Git blobs decoded_unscored, zero unavailable/decode failures, ten legacy expectation flags, one exact anchor confirmed by geometry. The old archive retrieval/hash/decode gate is satisfied per runner results. Item OCR and independent ground-truth labels were not evaluated.
- Five legacy sessions, 2,914 raw events, 35/37 segments and 2,909 events eligible. Two open segments excluded. Zero invalid lines, duplicates, read errors or quarantines. Legacy sequence completeness unverified. Zero purchase events means no observed purchase evidence, not zero actual purchases.
- Later 04-39-52 video not included in this Windows run; prior separate offline replay remains documented.
- Prior corrected Windows unit run 170/170 and synthetic benchmark passed. Full combined qualification runner was not rerun with media arguments; evidence collected in separate runs. Live capture/recognition, receipt/channel identity and resource cleanup warnings remain outstanding. No production modification or release approval. Raw media and logs not uploaded.

Next: resolve OCR worker shutdown warnings in isolated tests and then conduct read-only live Windows measurement with a qualified candidate.