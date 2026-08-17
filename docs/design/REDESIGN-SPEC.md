# LEAKPROOF — Redesign Spec

Reference: GOV.UK Design System (design-system.service.gov.uk) — chosen
because it is a real, published system built by a government team solving
the same problem this project has: presenting official, high-stakes data
so it reads as trustworthy and scannable, not decorative. Two of its rules
matter more than any specific pixel value and override everything else in
this document if they ever conflict: color is signal, never decoration;
and status is never shown by color alone — always color + a text label
together.

## What stays unchanged
The five brand colors locked in Stage 0 are NOT being replaced:
  bg      #FAF8F4
  navy    #132A47
  green   #2E7D5B
  gold    #C8952B
  coral   #D4573D
These are already muted and appropriate. This spec adds missing tokens
around them and tightens how they're used — it does not swap the palette.

## New tokens (additions, not replacements)

Text
  ink            #14171A   primary body text — NOT navy. Navy is reserved
                            for headings/brand elements, not paragraph text.
  ink-secondary  #5B6169   meta text, captions, timestamps, helper text
  ink-muted      #94989E   disabled/skipped-state text

Border
  border         #DDD9D0   warm-toned to sit on #FAF8F4, replaces any
                            cool-grey border currently in use
  border-strong  #C7C2B6   table rules, dividers that need more presence

Surface
  surface        #FFFFFF   cards, table body
  surface-sunk    #F3F0EA  code-like blocks, the skipped-row background
                            (already exists as bg-navy/5 — this just names
                            it properly instead of leaving it as an opacity
                            trick)

These are additive. Nothing currently using navy/green/gold/coral/bg needs
to change color — they need to stop being used for things ink/ink-secondary
should be doing instead (see rules below).

## Typography — real hierarchy, not just two fonts

Keep serif display (Fraunces/Source Serif) + Inter body. The gap right now
isn't the font choice, it's that too few sizes are actually in use. Lock
this scale:

  score-display   48px / 1.0    serif semibold   navy      (the 87 itself)
  page-title      28px / 1.2    serif semibold   navy
  section-heading 18px / 1.3    serif semibold   navy
  body            15px / 1.5    Inter regular    ink
  body-secondary  14px / 1.5    Inter regular    ink-secondary
  meta-label      12px / 1.4    Inter medium     ink-secondary
                                 uppercase, letter-spacing 0.04em
  table-header    12px / 1.4    Inter medium     ink-secondary
                                 uppercase, letter-spacing 0.04em
  table-cell      14px / 1.5    Inter regular    ink, tabular-nums

Rule: any text currently sitting at "body size, navy color" that ISN'T a
heading should drop to ink at body/body-secondary size. This is the single
biggest fix — navy-colored body text is what's currently flattening the
hierarchy, because heading-color and paragraph-color read as the same
weight of importance.

## Status / severity — tag pattern, not colored pills

This is the second biggest fix. Full-rounded, saturated color pills
("badge soup") are the most overused AI-dashboard tell. GOV.UK's tag
component is the corrective: a small RECTANGLE (2px radius, matching our
existing single radius token — do not introduce a second radius for tags),
tinted background at ~15% of the severity color, solid-color text in the
full-strength severity color, uppercase, sentence case content (not
ALL-CAPS blaring), and it always carries a text label — color is never
the only signal.

  severity-high    bg coral/15   text coral    "High"
  severity-medium  bg gold/15    text gold     "Medium"
  severity-low     bg green/15   text green    "Low"
  status-open      bg gold/15    text gold     "Open"
  status-closed    bg green/15   text green    "Closed"

Existing left-border-on-data-rows pattern (Officer list, trace table) is
CORRECT and stays — that's a different, also-valid pattern for indicating
severity on a full row. The tag component above is for compact inline
status (e.g. a status chip next to a case ID, or in a table cell that
isn't a full severity-colored row). Don't use both patterns on the same
element.

## Tables — real table discipline

Applies to: Officer list, Reasoning trace, Rulebook, Linked complaints,
Auditor timeline. All of these are structurally tables even where some are
currently rendered as stacked cards.

- Numeric columns (score, kg, %, weight) are right-aligned with
  tabular-nums. Currently some of these may be left-aligned — fix.
- Every table gets a real one-line caption above it stating what it shows
  in plain language — CaseDetail's "Every rule in the rulebook, what it
  read, and what it did about it" is already doing this correctly; extend
  the same pattern to Officer, Rulebook, and Auditor if not already there.
- Row density: 12-16px vertical padding per row for list/table views
  (Officer, trace, complaints, audit timeline) — tighter than a "hero
  card" but not cramped. This is what makes a page read as a real data
  product instead of a landing page with numbers on it — information
  density signals seriousness for this category of tool.
- Table headers are meta-label style (12px, uppercase, tracked,
  ink-secondary) — not the same size/weight as body text.

## What "professional, not AI-generated" means as a checklist

Before considering any page done, check it against this list:
  [ ] No text is navy EXCEPT headings and the score-display number
  [ ] No rounded-full badge/pill exists anywhere — tags are rectangular
  [ ] Every status/severity indicator has a text label, not just a color
  [ ] Numeric columns are right-aligned, tabular-nums
  [ ] Table headers are visually distinct (smaller, tracked, muted) from
      table cells
  [ ] Every table/list has a one-line caption explaining what it shows
  [ ] No gradients, no more than one shadow depth, no more than one
      border-radius token (tags included)
  [ ] No emoji; typographic marks only (— · … ✓ → ←)
  [ ] Focus rings visible on every interactive element

## Per-page application

Officer (list)
  Table with real caption ("60 shops, ranked by evidence"). Severity stays
  as left-border on the row (existing pattern, correct). Score column
  right-aligned tabular-nums. Case ID / shop name uses body-secondary
  weight, not navy.

Case Detail
  score-display for the 87 itself — this is the one place the huge serif
  navy number is earned. Everything else on the page (labels, meta,
  memo caption) drops to ink/ink-secondary. Ladder node captions
  ("FCI depot weighbridge") are body-secondary, not navy.

Rulebook
  Full table treatment: caption, meta-label headers, tabular-nums on
  threshold/weight columns, severity as the rectangular tag next to each
  rule's severity field (not the current colored left-border, since these
  rows aren't "cases" — they're config entries. Tag is more correct here).

Inspector
  List stays table-disciplined per above. The notes form gets ink-colored
  labels (not navy), border token on the textarea, and the same tag
  pattern if a note has a status.

Auditor
  Timeline as a real table/list: timestamp and actor in meta-label style,
  action in a small rectangular tag (not colored text), detail in body
  style. The identical/mismatch recompute result uses success-green/
  error-red exactly as GOV.UK reserves those two colors — nowhere else on
  this page should compete with that signal.