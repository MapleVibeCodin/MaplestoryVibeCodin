# Accessible dialogue — next export and holdout

Rendered user-visible source as authored, with attachment referenced by original archive; verification receipt follows this pre-verification archive and is not included. 

## User

give me command

## Assistant

Run this in PowerShell. It copies the latest two days of HeneFM observations to your clipboard. Paste the output here; I'll isolate everything after **20:35:05.774**.

```powershell id="9riloe"
& { $from = (Get-Date).Date.AddDays(-1).ToString('yyyy-MM-dd'); $t = "EXPORT TIME: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff zzz')"; $f = Get-ChildItem "$HOME\Downloads" -Recurse -File -Filter "*.png" | Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}_.*CH\d+-FM\d+' -and $_.Name.Substring(0,10) -ge $from } | Sort-Object Name | Select-Object -ExpandProperty Name; (@($t) + @($f)) -join "`r`n" | Set-Clipboard }
```

The reconstructed model, test results and accessible dialogue have been saved to GitHub and verified individually. The master checkpoint update and full continuity audit remain incomplete.

## User

[Attachment only: Pasted text(20261127-130346).txt; byte-exact original stored in ../raw/2026-11-27/]

## Assistant commentary

I’ll score this new export using the unchanged prediction rule, then compare the results against simply staying in the previous channel.

## Assistant

## New dataset tested — 21:03 Taipei time

<grid columns={2}>
  <grid-item>
    <caption>Total records</caption>
    <title size="2xl" tabularNums={true}>2,456</title>
  </grid-item>
  <grid-item>
    <caption>New observations</caption>
    <title size="2xl" tabularNums={true}>404</title>
  </grid-item>
  <grid-item>
    <caption>New consolidated events</caption>
    <title size="2xl" tabularNums={true}>261</title>
  </grid-item>
  <grid-item>
    <caption>Duplicate identifiers</caption>
    <title size="2xl" tabularNums={true}>0</title>
  </grid-item>
</grid>

All previous 2,052 records match the archived original. I also reproduced the previous reconstructed model's test results exactly before scoring the new batch, without changing its parameters.

### Exact channel prediction

| Lead time | Predictive | Persistence |
|---|---:|---:|
| Next event | 8.4% | 7.3% |
| 5 seconds | 12.6% | 14.2% |
| 10 seconds | 11.5% | 13.0% |
| 15 seconds | 10.0% | 10.3% |
| 30 seconds | 8.5% | 8.1% |

### Time saved or lost

Assuming a two-second channel change:

<card gap={3}>
  <caption>Net time saved over 261 events</caption>
  <title size="2xl" color="danger">−24.80 seconds</title>
  <divider/>
  <row>
    <text color="success">Saved at least 1 second</text>
    <spacer/>
    **11 events**
  </row>
  <row>
    <text color="danger">Lost at least 1 second</text>
    <spacer/>
    **25 events**
  </row>
  <row>
    Already on correct channel ≥1s early
    <spacer/>
    **16/261**
  </row>
  <row>
    Unnecessary or speculative switch attempts
    <spacer/>
    **108**
  </row>
</card>

The current reconstructed channel predictor is still not providing a net advantage in the simulation.

## What improved

The room-positioning component recovered on this larger batch:

<box gap={2}>
  <row><text>Fixed middle floor</text><spacer/>**0.927 floors**</row>
  <box height={3} radius="full" background="surface-tertiary"><box background="#94a3b8" width="100%" height="100%" radius="full"/></box>
  <row><text>Predictive floor</text><spacer/>**0.728 floors**</row>
  <box height={3} radius="full" background="surface-tertiary"><box background="#16a34a" width="78.5%" height="100%" radius="full"/></box>
  <caption>21.5% less vertical distance, conditional on already being in the correct channel.</caption>
</box>

I also tested 13 confidence thresholds for switching channels. None produced positive net savings on either the preceding 184-event sample or this new batch. Simply increasing the confidence requirement is not enough.

**Next model priority:** Predict which channel is about to become active, rather than which channel has recently been active. Keep the positioning model separate. Actual deal announcement timestamps and physical travel seconds are still unverified.
