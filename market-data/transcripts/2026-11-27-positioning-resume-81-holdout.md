# HeneFM positioning resume — accessible exchange, 2026-11-27

User-visible source text as authored; rendered interactive formatting may differ. Final verification receipt is not yet part of this pre-verification archive. No unrelated private data included.

## User

START GITHUB MEMORY.

Repository: [https://github.com/MapleVibeCodin/MaplestoryVibeCodin](https://github.com/MapleVibeCodin/MaplestoryVibeCodin)

Read AGENTS.md, checkpoints/LATEST.md, and market-data/2026-11-27-next-chat-handoff.md.

Resume HeneFM predictive positioning from checkpoint 40a4e12c2ff349305c6c591938dca7e62598a031.

Recover all historical research, transcripts, original datasets, model assumptions, failures and test results. Run all 10 continuity checks.

My objective is to be in the EXACT channel before the next deal is announced, and approximately near the correct FM room. Even one second saved is valuable. Optimize actual time saved, not room-speed accuracy.

The latest original dataset contains 2,052 records, including 81 unscored observations. Retrieve it directly from GitHub. Do not ask me to upload it again.

Continue without repeating completed research. Preserve all historical files and archive every accessible exchange word for word. Update and verify GitHub after every substantive exchange. Never suggest Work or Codex.

## Assistant commentary

I’ll retrieve the repository checkpoint, recover the original dataset, and verify continuity before changing the predictive model.

## Assistant

# HeneFM predictive positioning — checkpoint recovery

<row align="center">
  <icon name="check-circle-filled" color="success" size="xl"/>
  **GitHub main matches your requested checkpoint.**
</row>

[Verified commit: `40a4e12c2ff349305c6c591938dca7e62598a031`](https://github.com/MapleVibeCodin/MaplestoryVibeCodin/commit/40a4e12c2ff349305c6c591938dca7e62598a031)

The optimization objective is preserved:

- **Primary:** Be in the exact channel before the next deal announcement.
- **Secondary:** Be physically close to the predicted FM room.
- **Performance metric:** Net seconds saved, including incorrect predictions and unnecessary channel changes.
- **Validation:** Use only information available before each prediction. No hindsight or retuning on the unseen test batch.

The existing research documents confirm that conditional room accuracy is not a substitute for successful advance channel positioning.

## Assistant commentary

The latest export is accessible directly from GitHub, and its blob SHA matches the archived original. The previous handoff also identifies a reproducibility gap: the fitted channel-model weights and full travel-time simulation were not saved. I’ll distinguish reconstructed tests from exact reproductions.

## Assistant

## Original datasets recovered

All six exports were retrieved directly from GitHub. Their blob hashes match the original archive manifest.

<card gap={3}>
  <grid columns={2}>
    <grid-item>
      <caption>Historical records recovered</caption>
      <title size="2xl" tabularNums={true}>7,970</title>
    </grid-item>
    <grid-item>
      <caption>Latest dataset</caption>
      <title size="2xl" tabularNums={true}>2,052</title>
    </grid-item>
    <grid-item>
      <caption>New raw observations</caption>
      <title size="2xl" tabularNums={true}>81</title>
    </grid-item>
    <grid-item>
      <caption>New consolidated events</caption>
      <title size="2xl" tabularNums={true}>49</title>
    </grid-item>
  </grid>
  <divider/>
  <caption>Latest observation: November 27, 20:35:05.774 Taipei time. All 1,971 previous observations remain intact.</caption>
</card>

## New holdout test

I executed a reconstruction of the previously documented 75/25 channel-prediction rule without retuning it on the 81 new observations.

| Prediction horizon | Exact channel | Persistence baseline |
|---|---:|---:|
| Next event | 3/48 | 4/48 |
| 5 seconds | 6/47 | 5/47 |
| 10 seconds | 3/45 | 3/45 |
| 15 seconds | 7/44 | 5/44 |
| 30 seconds | 3/41 | 3/41 |

### Estimated channel-change time saved

<card gap={3}>
  <caption>Independent event simulation — assumed 2-second channel change</caption>
  <title size="2xl" color="danger" tabularNums={true}>−29.09 seconds</title>
  <caption>Net time saved across 49 consolidated events — negative means time lost.</caption>
  <divider/>
  <row>
    <text>Reactive baseline</text>
    <spacer/>
    **90.00 s**
  </row>
  <box height={3} background="surface-tertiary" radius="full">
    <box background="#94a3b8" width="75.57%" height="100%" radius="full"/>
  </box>
  <row>
    <text>Predictive reconstruction</text>
    <spacer/>
    **119.09 s**
  </row>
  <box height={3} background="surface-tertiary" radius="full">
    <box background="#dc2626" width="100%" height="100%" radius="full"/>
  </box>
  <divider/>
  <grid columns={2}>
    <grid-item>
      <caption>Events saving ≥1 second</caption>
      <title color="success" size="xl">2</title>
    </grid-item>
    <grid-item>
      <caption>Events losing ≥1 second</caption>
      <title color="danger" size="xl">16</title>
    </grid-item>
  </grid>
</card>

The reconstructed rule failed this holdout. The conditional floor predictor also performed slightly worse than fixed middle-floor positioning: 0.86 versus 0.82 floors of average distance.

**I would not deploy this version for proactive channel switching.** The original logistic model's fitted weights and earlier travel simulation implementation were not archived, so this is not an exact reproduction of those tests. Download timestamps also remain proxies for announcement times, and the simulation does not measure actual walking time.
