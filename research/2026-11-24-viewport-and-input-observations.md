# 2026-11-24 — viewport, input and movement observations

## Scope and evidence
These are session observations, not new runtime features. Keep the scanner passive and manual-click-only as specified in AGENTS.md. Do not commit raw desktop captures, personal identifiers or account-specific information. The original video and screenshots belong in the user's private archive. No live Windows test was performed by the assistant.

## Display investigation
Goal: see the uppermost Free Market shop signs along with lower platforms from the existing standing location, without moving the character. The wide-aspect-ratio community workaround was reported to expand horizontal coverage; its original post and exact mechanism have not been independently verified in this session. Tested by user screenshots:
- Desktop 1720×900, fullscreen: top signs clipped, black side bars.
- In-game 1920×1080 fullscreen: comparable normalized landmark positions; top signs clipped.
- In-game 1024×768 windowed: reduced horizontal coverage, no meaningful vertical gain.
- Desktop 1720×1200 with game 1366×768 windowed, then fullscreen: top/bottom letterboxing, top signs still clipped.
- The game dropdown also showed 800×600, 1280×720, 1366×768 and respective fullscreen choices. UI Size is separate from game resolution.
- The evidence is consistent with a fixed logical vertical field of view and aspect-dependent horizontal rendering, not proof of internal engine code. Increasing monitor resolution or stretching cannot recover unrendered pixels. Avoid repeating failed resolution tests. The proposed 800×600 starting-mode experiment was not completed.
- The scanner currently supports 1280×720 and 1366×768 client geometry; nonstandard rendering requires separate alignment validation. Do not change runtime code based solely on these screenshots.

## Input observations
Current published scanner hotkeys were verified by reading Scanner Nov 20/trade_hotkeys.py and READ_ME_FIRST.txt. The program registers Windows hotkeys and enqueues pointer/selection actions; it does not send game keystrokes. The user supplied screenshots of external G HUB mappings. These are independent of the scanner and their local behavior is not verified. Preserve manual selection and confirmation. Do not infer exact Num+ behavior without testing Windows accessibility settings; Mouse Keys double-click was a hypothesis, not a confirmed setting. No input automation code changes were made.

## Movement video
Original recording dated 2026-11-24 15-03-50.mp4 (private source). Prior assistant reported 10.7 seconds at 60 FPS, five apparent horizontal jumps of 146–147 recorded pixels, event timestamps 3.350, 3.967, 4.617, 5.267 and 5.917 s, with inter-event intervals 617, 650, 650, 650 ms. Mean of rounded intervals 641.75 ms; the prior response rounded to 642 ms. It estimated walking speed ~170 recorded px/s. These are **prior conversational estimates, not independently validated measurements**; the frame-tracking method and camera correction data were not preserved, and recorded pixels must not be treated as world units. Do not treat observed interval as minimum skill cooldown. Verify against original video if precision matters. No character identity or account-specific stats stored in this public repo.

## Handoff
Keep the current scanner UI, passive alignment, chase lock, marker and updater behavior unchanged. No runtime files were changed in this research session. Do not claim a private video upload or full chat export based solely on this note. The research checkpoint documents observations so future sessions need not repeat basic display experiments or repository orientation.
