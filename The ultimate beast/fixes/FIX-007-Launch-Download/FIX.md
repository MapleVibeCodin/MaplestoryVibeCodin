# FIX-007-Launch-Download: Missing ZIP, wrong install, or unverified launch

Status: **Delivery workaround; live pending**

SoftLock ZIP was missing locally; failure before runtime. Do not require manual downloads. Use Git existing authentication, immutable runtime SHA, isolated LOCALAPPDATA folder, sparse checkout six runtime files, verify commit and Git blob hashes, run START.ps1 compile preflight. Latest recorded runtime 456b90748e6440870b4f0ea9cbc475210c8b5c0e; current manifest in [continuation](../../../fm-sprint/NEXT-CHAT.md). Historical [FINAL-RELEASE-GATE.md](../../research/FINAL-RELEASE-GATE.md). Preserve existing installs and data. Regression: missing local ZIP cannot block acquisition; explicit error on unavailable Git/auth, wrong SHA, hash mismatch, or compile failure. Do not automatically delete or close unrelated processes.

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.
