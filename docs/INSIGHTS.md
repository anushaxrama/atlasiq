# Insights from the executed warehouse

Generated from actual SQL queries. See [full results](evidence/analyses.json), [verification](evidence/verification.json) and [measured query plan](evidence/query-plan.json).

- The warehouse contains **284,899 accepted sampled trips**. Rejected rows are retained in quarantine. Coverage is **2025-01-01 through 2025-03-31** across **3 monthly partitions**. These are capped deterministic samples, not full TLC months or all NYC mobility. Equal monthly sample caps do not establish equal population demand.
- The highest-count pickup zone in this sample is **Midtown Center (Manhattan)**, with **13,260 observed trips**, according to analysis 01. This ranking is conditional on deterministic sampling and exclusions.
- Weather-day group comparisons from analysis 06 are listed below. They are descriptive, include partial UTC days at local filter edges and do not isolate a causal weather effect.

| Condition | Reporting days | Mean observed trips per day |
|---|---:|---:|
| Wet | 23 | 2932.39 |
| Dry | 68 | 3197.85 |

![Observed demand](demand-chart.svg)

No business optimization, savings, performance improvement or causal effect is claimed. Query timings include connection overhead on the recorded local environment; they are not cloud production latency. This limited historical window cannot establish annual seasonality or city-wide demand growth.
