# Method 5 — accessible dialogue excerpt

Verbatim prose and tables through pre-verification; chart markup and final receipt excluded. Not a complete transcript.

## User

ok now do next

## Assistant commentary

I’ll run Method 5 using the four existing models plus the shop-density correction, selecting the ensemble by simulated seconds saved rather than prediction accuracy.

## Assistant

# Method 5 of 5 — Decision-focused ensemble

**Completed: 95 model combinations and 3,326 positioning policies tested.**

I combined all four forecasting methods, including the new shop-density variants, and selected policies based on net seconds saved during validation.

## Best combinations

| Model combination | Validation savings | Test savings |
|---|---:|---:|
| 100% HSMM | +3.08s | 0.00s |
| 75% density-adjusted HSMM + 25% Hawkes | +2.26s | 0.00s |
| 25% of each of the four models | 0.00s | 0.00s |
| 100% HSMM with density and historical-event weighting | +3.08s | 0.00s |

The ensemble did not outperform Method 4 alone. Combining multiple models diluted some of the stronger signals without producing additional actionable predictions.

## Final comparison of all five methodologies

| Method | Test seconds saved | Next-channel accuracy | Log loss ↓ |
|---|---:|---:|---:|
| Marked TPP | −3.31 | 6.40% | 3.577 |
| Hawkes | 0.00 | 3.20% | 3.611 |
| Renewal | 0.00 | 5.09% | **3.312** |
| HSMM | 0.00 | **8.43%** | 3.499 |
| Best genuine ensemble | 0.00 | 5.52% | 3.525 |

HSMM is the leading candidate for further testing, but **none of the five methodologies has demonstrated positive net time savings on the common test batch.** The accuracy figures are sampled forecast times, not actual successful advance positioning.

## Archive index (editorial)
Full numerical outputs: ../results/2026-11-27-method05-ensemble.json; methodology: ../2026-11-27-method05-ensemble.md.
