# Analytical SQL catalogue

Each numbered SQL file includes the question, expected columns and interpretation caveats. Run all of them against the real warehouse with `uv run atlasiq insights`. Actual row outputs and measured query durations are saved to `docs/evidence/analyses.json`; the generated narrative and SVG chart live in `docs/INSIGHTS.md`.

1. Zone ranking — grouped counts, dense ranking and official zone join.
2. Weekday/hour — local calendar alignment and counts per covered date.
3. Rolling demand — seven-calendar-day rolling means with modeled zero counts.
4. Fare distribution — borough medians/p90/p99 using ordered-set percentiles.
5. Trip efficiency — volume-gated zone comparisons; per-trip means, not fleet speeds.
6. Weather association — reporting-day wet/dry comparison; no causal claim.
7. Federal holiday comparison — calendar dimension and descriptive day averages.
8. Week-over-week — exact seven-day calendar join; undefined percentage for zero denominator.
9. Unusual demand — documented prior same-weekday median/MAD flags.
10. Zone flow — pickup/dropoff role-playing dimension joins and overall share.
11. Provider mix — within-day composition using a partitioned window denominator.
12. Refresh and rejections — source/sample/accepted/modeled reconciliation and load duration.

Run the SQL unchanged through a parameterized application helper or psql. The committed analyses use no user-provided SQL fragments. They operate on accepted sample rows, so negative/refund exclusions, deterministic selection, one taxi type, one month and weather coverage materially limit inference. No city-wide economic, causal or optimization conclusion is justified by these queries alone.
