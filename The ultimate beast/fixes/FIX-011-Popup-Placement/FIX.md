# FIX-011 — Route popup placement (permanent UI preference)

Status: **Source corrected; live placement pending**

User wants the existing route popup top middle of MapleStory, not top right. Keep the 160x185 native-pixel popup, 12px top inset, transparency, click-through behavior, existing visibility gates and all shortcuts. Center relative to the client, not desktop or outer window. Runtime: 95f282dee685bda329daa8a3de15417e83e81427; source: The ultimate beast/fm_sprint.py, App.show_route_mini. Prior backup: 0a59364723b066ae697545bd44b0f65c8aed3074.

Regression: for 1366x768, popup client-relative bounds (603,12,763,197); for 1280x720, (560,12,720,197). With decorated window or negative monitor coordinates, client offsets must be included. Odd width may differ by half a pixel. Five arithmetic cases passed in source review; actual Windows overlay positioning unverified. Preserve all prior fix IDs and no automatic movement. Use test_popup_placement.py for executable source-level checks before future layout changes; test file staged, not executed in this turn.
