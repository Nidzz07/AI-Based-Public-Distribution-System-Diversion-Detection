# Fixtures — three shops that exercise everything

Copied verbatim from PROJECT-BRIEF.md. This file is the authority the pytest
suite asserts against: write the assertion here first, then the implementation.

```
                        #4521 Sitapur   #4102 Barabanki   #4788 Hargaon
archetype               transport       transport, no GPS  counter skim
allocated / dispatched  12,000 / 12,000 8,000 / 8,000      9,000 / 9,000
weighed                 11,015          7,512              8,970
dispensed               10,980          7,490              8,190
dispatch → receipt      -8.21%          -6.10%             -0.33%
receipt → counter       -0.32%          -0.29%             -8.70%
delivery gap            61 h            52 h               44 h
gps deviation           3.4 km          unavailable        0.8 km
txn_card_ratio          0.88            0.71               0.55
hour violations         1               1                  4
complaints in window    7               2                  6
fired rules             30 + 25 + 22    30 + 25            20 + 15 + 8
bonus                   +10             0 (below 3)        +10
SCORE                   87              55                 53
severity                HIGH            MEDIUM             MEDIUM
coverage_pct            100             83                 100
gap_hop                 dispatch_to_    dispatch_to_       receipt_to_
                        receipt         receipt            counter
```

Between them: gap localisation at two hops, a skipped rule, coverage
reduction, bonus firing, bonus not firing, and all three row states.

## How these land in the database

`seed.py` writes raw inputs only. Everything in the lower half of the table
above — variances, fired rules, bonus, score, severity, coverage_pct,
gap_hop — is derived by `engine/` at evaluation time and is not precomputed
anywhere.

The raw inputs seed hardcodes for these three shops:

| Input | Stored as | #4521 | #4102 | #4788 |
| --- | --- | --- | --- | --- |
| allocated / dispatched / weighed / dispensed | `cycles` (period `2026-08`) | 12000 / 12000 / 11015 / 10980 | 8000 / 8000 / 7512 / 7490 | 9000 / 9000 / 8970 / 8190 |
| delivery gap | `deliveries.arrival_ts − dispatch_ts` | 61 h | 52 h | 44 h |
| gps deviation | `deliveries.gps_deviation_km` / `gps_available` | 3.4, available | null, **unavailable** | 0.8, available |
| txn_card_ratio | distinct `transactions.card_id` ÷ `shops.ration_cards` | 1056 / 1200 | 639 / 900 | 550 / 1000 |
| hour violations | `cycles.hour_violations_month` | 1 | 1 | 4 |
| complaints in window | `complaints.filed_at` within 14 days of case open | 7 | 2 | 6 |

Case open time, and the anchor every complaint window is measured back from,
is `2026-08-14T09:12:00`.

#4521 also carries 2 complaints older than the window and #4102 carries 1.
They are there so a broken window check fails a test instead of passing
quietly.

The other 57 shops are generated. They may fire one or two rules, but no
generated shop is built to reach #4521's combination — the ranked list opens
on the demo case.
