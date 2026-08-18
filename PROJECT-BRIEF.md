# LEAKPROOF — Project Brief

## Problem
India's Public Distribution System moves subsidised foodgrain to roughly
two-thirds of the population under the National Food Security Act. It moves
through a chain: government allocation → transport consignment → fair-price
shop receipt → beneficiary transaction at an ePoS counter. Grain leaks between
those hops. Today the mismatch surfaces months later in an audit, by which
time the trail is cold, and inspections are allocated by rotation rather than
by evidence.

## Solution
LEAKPROOF reads data the PDS already produces — ePoS-linked weighing scales,
FCI depot weighbridges, vehicle GPS, and public grievance portals — and
reconciles four numbers per cycle. Where they disagree, it localises WHICH
hop the grain left at, scores the case against a rulebook an officer can edit,
and emits a reasoning trace that survives scrutiny in front of a magistrate.

LEAKPROOF installs no hardware. It reads existing infrastructure.

## Users and roles
Officer   — sees the ranked case list, opens a case, reads the trace
Inspector — sees cases ordered by score for field visits, adds notes
Auditor   — sees the append-only trail, presses Recompute

Roles are a dropdown switcher in this build. Real auth is out of scope.

## The four-hop reconciliation model
allocated_kg → dispatched_kg → weighed_kg → dispensed_kg

Three variances, three places grain can go:
  allocated → dispatched   paper diversion at the depot
  dispatched → weighed     transport-leg diversion
  weighed → dispensed      counter skimming at the shop

locate_gap() returns the worst hop. This is the core insight: "985 kg opened
between dispatch and receipt — not the dealer, the transport leg."

## The six features
F1 Four-hop reconciliation ladder      — engine/reconcile.py
F2 Versioned YAML rulebook             — rules.yaml + engine/rulebook.py
F3 Reasoning trace                     — engine/score.py
F4 Complaint auto-linking              — engine/complaints.py
F5 Graceful degradation on missing data— threaded through F1/F3
F6 Reproducibility on append-only trail— engine/audit.py

Deliberately excluded: statistical z-score as a scoring input (badge only),
inspector map optimisation, anything beneficiary-facing, LLM memo generation.

The z-score badge is computed in routers/cases.py at case-open time: each
shop's worst hop variance against the mean and population SD of all 60 shops'
worst hops, confirming at z >= 2.0. #4521 sits at z 1.66, so its badge reads
"does not confirm" — an honest result, not a tuned one. engine/score.py never
reads it; the score is fired weights plus the complaint bonus and nothing else.

## Scoring
Weights live in rules.yaml, loaded at runtime.

  weighing_variance     variance_dispatch_to_receipt  <  -5.0 %   30
  delivery_gap          delivery_gap_hours            >  48 hrs   25
  gps_deviation         gps_deviation_km              >  2.0 km   22
  counter_variance      variance_receipt_to_counter   <  -5.0 %   20
  transaction_mismatch  txn_card_ratio                <  0.6      15
  operating_hours       hour_violations_month         >= 3         8
  complaint_bonus       >=3 complaints in 14 days                 +10

Total possible 130, displayed capped at 100.
Severity bands: HIGH >= 75, MEDIUM >= 50, else LOW.

Every rule hit records: rule_id, label, raw_value, threshold, contribution,
severity, and status (fired | passed | skipped).

## Graceful degradation (F5)
A rule whose input is unavailable gets status "skipped", contributes 0, and
reduces coverage_pct. It is never "passed". The UI displays this as a greyed,
italic row plus a coverage badge: "55 / 100 · signal coverage 83%".

This is the difference between "we checked and it was fine" and "we could not
check". Conflating the two is how audit systems lose credibility.

## Fixtures — three shops that exercise everything

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

Between them: gap localisation at two hops, a skipped rule, coverage
reduction, bonus firing, bonus not firing, and all three row states.

### #4521 is not the only 87 — correction, Stage 4

An earlier draft of this brief said no generated shop reaches #4521's
combination. Under seed 4521 that is false. Three generated shops fire the same
30 + 25 + 22 + 10 and land on exactly 87:

  #4910 FPS Hargaon-36 (4 complaints) · #4219 FPS Laharpur-3 (3) ·
  #4458 FPS Mahmudabad-40 (3)

This is not a bug in the fixtures. The `transport` archetype in seed.py draws a
receipt variance in (-9.0, -5.2), a delivery gap in (49, 72) and a GPS deviation
in (2.1, 4.5) — all three thresholds — and 3 or more complaints then adds the
bonus. 87 is simply the ceiling of that archetype, and four of sixty shops
reaching it is realistic rather than embarrassing.

seed.py is NOT to be adjusted to remove them: random.seed(4521) is an invariant,
and changing the archetype bounds would move all 57 generated shops.

Ties are therefore broken in the ranked list, not in the score:

  ORDER BY score DESC, complaint_count DESC, coverage_pct DESC, case_id

Corroborating complaints first — among cases the rulebook scores equally, the
one the public has already complained about seven times is the one to send an
inspector to. Coverage second: between two equally-complained cases, prefer the
one we could evaluate more fully. #4521 has 7 complaints against 4, 3 and 3, so
it holds the top of the list on the tie-break rather than on a special case.

If asked on stage, the honest answer is "four shops hit 87; the demo case leads
because it has the most corroboration", not "only one shop can score 87".

## API contract — frozen at hour 2
GET  /api/cases?severity=&district=   ranked case list
GET  /api/cases/{case_id}             case + trace + linked complaints
GET  /api/shops/{shop_id}             shop profile + cycle history
GET  /api/rulebook                    parsed rules.yaml + version
GET  /api/audit/{case_id}             append-only event list
POST /api/cases/{case_id}/notes       inspector note, writes to audit log
POST /api/cases/{case_id}/recompute   re-derives from stored inputs

Canonical case-detail response: docs/contract/case_detail.json
Frontend builds against that static file until Stage 3.

## Audit events
CASE_OPENED · RULE_FIRED (one per fired rule) · COMPLAINT_LINKED ·
NOTE_ADDED · SCORE_RECOMPUTED

Recompute returns {stored, recomputed, identical} and writes a new row.
It never mutates an old one.

## Screens
Officer   ranked list, severity as left-border, sortable, filter by district
CaseDetail four-node reconciliation ladder · trace table (3 row states) ·
           coverage badge · linked complaints · plain-language memo · trend
Rulebook  rules.yaml rendered with version and updated_by
Inspector cases sorted by score, notes form
Auditor   event timeline + Recompute button

## Declared limitations
Stated proactively to judges as scoping decisions, not discovered as gaps:
1. Data is synthetic, generated under random.seed(4521)
2. Rule weights are back-solved for the demo case, not learned
3. Escalation is a stub — no email or SMS is sent
4. Roles are a dropdown, not authentication
5. Inspector routing is score-sorted, not geographically optimised
6. Memos are f-string templates — "template now, LLM later"
7. Headline statistics (28%, 1-in-5, 4-6 months, 5x) are illustrative
8. Card border tokens (border-strong #C7C2B6, border #DDD9D0) read below
   WCAG 1.4.11's 3:1 non-text contrast threshold against the cream
   background; interactive state is instead conveyed by full fill inversion
   on hover/focus, which clears contrast comfortably.
9. Coral text on the reconciliation ladder's located-hop labels (#D4573D on
   the cream background — the variance figures at 14px medium and the "gap
   located" label at 12px) reads 3.79:1, below WCAG AA's 4.5:1 threshold for
   text. Neither size qualifies as large text, so 4.5:1 is the applicable
   floor. This is a locked brand token; the finding is documented rather than
   silently patched. The label never carries colour alone — it is always read
   with its text.
10. Ink-muted text on skipped trace rows (#94989E on the sunk row ground
    #F3F0EA) reads 2.55:1, below WCAG AA. It reads 2.90:1 where ink-muted
    sits on a white card instead. Same status — locked token, documented
    rather than patched. A skipped row's meaning is carried by its "Skipped"
    text label, not by the muting.

## Out of scope
Deployment, auth, real data integration, mobile app, notifications,
multi-district scaling, ML model training, LLM anything.