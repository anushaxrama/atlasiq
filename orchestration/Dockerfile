FROM apache/airflow:2.10.5-python3.12
USER airflow
RUN python -m venv /home/airflow/atlas-tools && /home/airflow/atlas-tools/bin/pip install --no-cache-dir uv==0.13.6
WORKDIR /home/airflow/atlas
COPY --chown=airflow:root pyproject.toml uv.lock ./
COPY --chown=airflow:root src ./src
COPY --chown=airflow:root warehouse ./warehouse
COPY --chown=airflow:root analyses ./analyses
COPY --chown=airflow:root orchestration ./orchestration
RUN /home/airflow/atlas-tools/bin/uv sync --frozen --no-dev
ENV AIRFLOW__CORE__DAGS_FOLDER=/home/airflow/atlas/orchestration ATLAS_PROJECT_ROOT=/home/airflow/atlas ATLAS_DATA_DIR=/opt/airflow/atlas-data DBT_SEND_ANONYMOUS_USAGE_STATS=false
