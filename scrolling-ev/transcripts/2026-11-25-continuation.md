# Continuation exchange — 2026-11-25

Archive metadata: exact user text and prepared final assistant text for this turn; speaker headings added. Earlier archives are partial. Tool interactions and commentary excluded.

## User

awesome. now how do you do this every single time? Same is all of this updated onto github? If so, lets say this chat has future messages and then runs out of messages and i have to use new chat. What would i have to say in the new chat for smooth actual continuation?

## Assistant

**Yes. I've verified the existing research files, transcript excerpts and raw HeneFM sales archive on GitHub. I've also changed our standing workflow from saving only major research to saving every project turn.**

## How it works every time

For each MapleStory research request, the intended workflow is:

1. Complete the research, calculation or implementation.
2. Copy your message and my prepared response verbatim into the dated transcript archive.
3. Update the research files and latest checkpoint with any new findings or decisions.
4. Commit to GitHub and verify the saved files before finishing the response.

You should not have to request a save every time. This is now documented in our [master README](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/main/scrolling-ev/README.md).

## When you start a new chat

Copy and paste this same prompt every time:

```text
Resume from https://github.com/MapleVibeCodin/MaplestoryVibeCodin/tree/main/scrolling-ev. Read the latest README, RESEARCH_HANDOFF.md, CATALYST_RESEARCH.md and transcript archives on main. Restore our project context and continue from the latest checkpoint. Follow the per-turn verbatim archive and GitHub verification protocol. Do not restart completed research. Apply my next instruction.
```

You can put your next research request immediately underneath it.

## Before switching chats

As an extra safeguard, send:

```text
Checkpoint this chat to GitHub, including all accessible unsaved messages verbatim and the latest project state. Verify the files before I switch.
```

This is especially useful if a chat is getting close to its context limit.

**Current status:** the per-turn protocol and this exchange are saved. Existing archives are partial, not a complete word-for-word record of the entire earlier chat. I cannot guarantee automatic synchronization of future messages or access in every new session. If a save fails or text is unavailable, I should explicitly report it. Because the repository is public, private or unrelated information should not be included.

[Open our GitHub project](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/tree/main/scrolling-ev)
