# Final Things To Check

Pre-delivery checklist for the geographic workshop deck. Mostly concerns places where
[slides.qmd](slides.qmd) hard-codes a fact that actually lives in the playground app at
`C:\geographic_or_ds_playground` or its data — if the app changes and the slide doesn't, the
slide quietly starts lying to the room.

Companion file: [notes/2026-08-05-slides-vs-playground-app-mismatches.md](notes/2026-08-05-slides-vs-playground-app-mismatches.md),
which records mismatches already found and how each was resolved.

## Outstanding app changes (agreed, not yet made)

- [ ] **Age band → 50-84.** App says 50-85 in `app/Homepage.py:24` and in the `analyst_prompt`
      strings at `app/utils_investigations.py:35` and `:218`. Data file is
      `demand_MF_50_84.csv`, so 50-84 is correct and the slides already say it.
- [ ] **Deprivation in the starting brief.** Slides state two objectives (access for 50-84,
      and prioritising the most deprived areas). `app/Homepage.py` currently states only the
      age one. Needed for coherence with the Pareto metrics, which already score deprivation.

## Numbers the slides hard-code from the app

Each of these appears on a slide as a bare figure. Re-check after any change to the app's
data or scoring.

- [ ] **5 measures** — "compared all 14 combinations against **5 different measures**" in
      [_geographic-main-exercise.qmd](_geographic-main-exercise.qmd). Source: `PARETO_METRICS`,
      `app/utils.py:68`. **Known to be changing** — improvement in journey times for the most
      deprived regions is being added to the scoring set. If that takes it to six, update the
      slide.
- [ ] **"Several of them are defensible"** — deliberately vague, but check it's still true
      after the metric set changes. Adding a metric usually *grows* the Pareto front, and
      `app/utils.py:60-67` records that the inter-tertile scoring choice alone moved it
      between 5/14 and 9/14. If the front becomes most of the field, "several" undersells it
      and the "there's no single best answer" point actually gets stronger.
- [ ] **14 candidates / 91 pairs** — used in both
      [_location-optimization.qmd](_location-optimization.qmd) (the combinatorics build:
      14 / 91 / 364 / 1001 / 2002 / 3003 = `C(14,k)`) and the debrief. Source:
      `data/devon_cdcs.csv`, `Existing == "No"`. Adding or removing a candidate site breaks
      **every number on that slide**, and the `solution_car_5.pkl` / `solution_car_6.pkl`
      pickles need regenerating too.
- [ ] **11 analyses / 6 briefings** — on the "You didn't disagree because somebody was wrong"
      slide. Sources: `ALL_INVESTIGATIONS` (`app/utils_investigations.py:225`) and
      `MAXIMUM_BRIEFINGS` (`app/utils.py:18`).

## Claims that depend on the current solution data

- [ ] **The two-site pair claim.** The debrief says the two best *individual* sites aren't
      always the best *pair*, and that on this data they match on most measures but not on
      worst-case journey time. Verified 2026-08-05 against the pickles: naive pair equals true
      best pair for weighted average, unweighted average, 90th percentile, coverage and
      inter-tertile ratio — and **differs only for `max`**.

      This is fragile. Re-run the check after any change to sites, travel data or scoring:

      ```
      cd C:\geographic_or_ds_playground
      # compare naive_top_two_pair() vs true_best_pair() per metric
      # (the same comparison Optimise_6_Sites.py:416-430 makes at runtime)
      ```

      If it comes to differ on more metrics the slide gets *stronger* and should be reworded;
      if it stops differing at all, the slide needs to drop the claim entirely.

## Still missing from the deck

- [ ] **App link and QR code.** The "How this works" slide says "head to the app and begin"
      but carries no actual link — needs the deployment URL before delivery.
- [ ] **Trade-off chart.** [assets/PLACEHOLDER-tradeoff-chart.png](assets/PLACEHOLDER-tradeoff-chart.png)
      is a generated grey placeholder. Replace with an export of the app's Multi-objective
      Overview tab. Marked with a TODO comment in the qmd.
- [ ] **Timings.** No running order anywhere in the deck — particularly wanted around the two
      Menti sessions and the exercise.
- [ ] **Placeholder slides** flagged in the 2026-07-30 review and still empty:
      Routing and Scheduling, the dialysis showcase, and Boundary Optimization in
      [_other-geographic-techniques.qmd](_other-geographic-techniques.qmd).

## Consistency to eyeball on a full run-through

- [ ] **Two different site datasets.** The concept slides in
      [_geographic-key-concepts.qmd](_geographic-key-concepts.qmd) map **15 MIUs**
      (`data/devon_mius.geojson`); the exercise uses **4 existing + 14 candidate CDCs**
      (`devon_cdcs.csv` in the app repo). Both are Devon healthcare sites shown as red pins.
      Worth deciding whether to call the switch out explicitly, since an attendee who counts
      pins will notice.
- [ ] **Objectives wording.** "Best at what?" in
      [_location-optimization.qmd](_location-optimization.qmd) lists five objectives phrased
      in plain English. They should stay recognisable against `RANK_METRIC_LABELS`
      (`app/utils.py:45`) — same concepts, same order of importance, no new ones on either side.
- [ ] **Fenced-div fragments.** The `fragment` and `icon` attributes only do anything on a
      `.value-box` div — the filter ignores them on a `.column` (`_extensions/bergam0t/value-box/value-box.lua:56`).
      Two instances of this were found and fixed; if fragments stop firing on a slide, check
      the attribute isn't on the wrapper.
- [ ] **Render warnings.** `quarto render slides.qmd` should complete with no "unclosed div"
      or "fenced div" warnings. One unclosed raw `<div>` was silently swallowing every slide
      after it, so treat these as real rather than cosmetic.
