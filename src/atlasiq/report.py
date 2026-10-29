"""Execute all analytical SQL and render evidence from queried results."""

import json
import platform
import time
from datetime import datetime, timezone
from typing import Any

from .config import ROOT
from .db import query


def generate() -> dict[str, Any]:
    output = ROOT / "docs/evidence"
    output.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, Any] = {}
    for path in sorted((ROOT / "analyses").glob("*.sql")):
        start = time.perf_counter()
        rows = query(path.read_text())
        evidence[path.stem] = {
            "rows": rows,
            "seconds": round(time.perf_counter() - start, 6),
            "row_count": len(rows),
        }
    (output / "analyses.json").write_text(json.dumps(evidence, indent=2, default=str))
    plans = query(
        "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) select pickup_date,count(*) from marts.fct_trips where pickup_date between '2025-01-10' and '2025-01-12' and pickup_zone=237 group by pickup_date"
    )
    (output / "query-plan.json").write_text(json.dumps(plans, indent=2, default=str))
    counts = query("select count(*) as raw_rows from raw.trips")[0]
    coverage = query(
        "select min(pickup_date) as start, max(pickup_date) as end, count(distinct partition_month) as months from marts.fct_trips"
    )[0]
    checks = query("select status,count(*) as checks from raw.quality_checks group by status")
    best = evidence["01_zone_ranking"]["rows"][0]
    weather = evidence["06_weather_association"]["rows"]
    runs = query(
        "select partition_month,status,source_rows,selected_rows,accepted_rows,rejected_rows,duplicate_rows,elapsed_seconds from raw.ingestion_runs order by started_at"
    )
    record = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "warehouse": counts,
        "coverage": coverage,
        "checks": checks,
        "runs": runs,
        "queries": {
            name: {"seconds": item["seconds"], "row_count": item["row_count"]}
            for name, item in evidence.items()
        },
    }
    (output / "verification.json").write_text(json.dumps(record, indent=2, default=str))
    trends = query(
        "select pickup_date as date,count(*) as trips from marts.fct_trips group by 1 order by 1"
    )
    high = max(r["trips"] for r in trends)
    points = " ".join(
        f"{45 + i / max(len(trends) - 1, 1) * 710:.1f},{240 - r['trips'] / high * 190:.1f}"
        for i, r in enumerate(trends)
    )
    (ROOT / "docs/demand-chart.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="300" viewBox="0 0 800 300"><rect width="800" height="300" fill="#f5f5f0"/><text x="40" y="28" fill="#213b3b" font-family="sans-serif" font-size="16">AtlasIQ · observed sampled trips by local pickup date</text><polyline points="{points}" fill="none" stroke="#2e6864" stroke-width="3"/><text x="40" y="280" fill="#607765" font-family="sans-serif" font-size="12">{trends[0]["date"]} — {trends[-1]["date"]} · real queried records, no population extrapolation</text></svg>'
    )
    text = f"""# Insights from the executed warehouse

Generated from actual SQL queries. See [full results](evidence/analyses.json), [verification](evidence/verification.json) and [measured query plan](evidence/query-plan.json).

- The warehouse contains **{counts["raw_rows"]:,} accepted sampled trips**. Rejected rows are retained in quarantine. Coverage is **{coverage["start"]} through {coverage["end"]}** across **{coverage["months"]} monthly partitions**. These are capped deterministic samples, not full TLC months or all NYC mobility. Equal monthly sample caps do not establish equal population demand.
- The highest-count pickup zone in this sample is **{best["zone_name"]} ({best["borough"]})**, with **{best["observed_trips"]:,} observed trips**, according to analysis 01. This ranking is conditional on deterministic sampling and exclusions.
- Weather-day group comparisons from analysis 06 are listed below. They are descriptive, include partial UTC days at local filter edges and do not isolate a causal weather effect.

| Condition | Reporting days | Mean observed trips per day |
|---|---:|---:|
"""
    for row in weather:
        text += f"| {row['precipitation_class']} | {row['reporting_days']} | {row['mean_daily_observed_trips']:.2f} |\n"
    text += "\n![Observed demand](demand-chart.svg)\n\nNo business optimization, savings, performance improvement or causal effect is claimed. Query timings include connection overhead on the recorded local environment; they are not cloud production latency. This limited historical window cannot establish annual seasonality or city-wide demand growth.\n"
    (ROOT / "docs/INSIGHTS.md").write_text(text)
    return record
