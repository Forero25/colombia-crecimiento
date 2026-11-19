# Imagen del pipeline: ingesta en Python, transformación con dbt y análisis.
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
COPY requirements-pipeline.txt .
RUN pip install --no-cache-dir -r requirements-pipeline.txt
COPY ingesta/ ingesta/
COPY dbt/ dbt/
COPY analisis/ analisis/
COPY tests/ tests/
COPY entradas/ entradas/
COPY correr.sh .
CMD ["sh", "correr.sh"]
