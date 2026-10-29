"""Monthly official-source batch. No network or application work occurs at import time."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def run_stage(stage, **context):
    import os
    import subprocess
    from pathlib import Path

    end = context["data_interval_end"]
    index = end.year * 12 + end.month - 1 - 2
    month = f"{index // 12:04d}-{index % 12 + 1:02d}"
    config = context["dag_run"].conf or {}
    month = config.get("month", month)
    limit = int(config.get("limit", 100000))
    root = Path(os.getenv("ATLAS_PROJECT_ROOT", "/home/airflow/atlas"))
    executable = str(root / ".venv/bin/atlasiq")
    args = [executable, stage]
    if stage == "ingest":
        args += ["--month", month, "--limit", str(limit)]
    subprocess.run(args, check=True, cwd=root, timeout=1200)


def alert_hook(context):
    import json
    import logging

    logging.getLogger("atlasiq.alert").error(
        json.dumps(
            {
                "event": "atlas_task_failed",
                "dag_id": context["dag"].dag_id,
                "task_id": context["task_instance"].task_id,
                "run_id": context["run_id"],
                "action": "Inspect task logs and raw.ingestion_runs; retry the same partition after correction. No external notification is configured.",
            }
        )
    )


with DAG(
    "atlasiq_monthly",
    start_date=datetime(2025, 3, 15),
    schedule="0 6 15 * *",
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=2),
    default_args={
        "owner": "atlasiq",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "retry_exponential_backoff": True,
        "execution_timeout": timedelta(minutes=25),
        "on_failure_callback": alert_hook,
    },
    description="Monthly TLC partition about two months behind publication date; override month/limit in dag_run.conf.",
    tags=["batch", "tlc", "dbt", "warehouse"],
) as dag:
    tasks = [
        PythonOperator(task_id=stage, python_callable=run_stage, op_kwargs={"stage": stage})
        for stage in ["bootstrap", "ingest", "transform", "validate", "publish"]
    ]
    for upstream, downstream in zip(tasks, tasks[1:]):
        upstream >> downstream
