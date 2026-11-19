#!/bin/sh
# Pipeline completo: ingesta -> carga a PostgreSQL -> dbt (modelos y pruebas) -> análisis -> pruebas de Python.
set -e
if [ "${DESCARGAR:-1}" = "1" ]; then
  python ingesta/banco_mundial.py
  python ingesta/innovation_graph.py
  python ingesta/pwt.py
  python ingesta/rues.py
fi
python ingesta/cargar.py
cd dbt && dbt build --profiles-dir . && cd ..
python -W ignore -m analisis.correr
pytest -q -W ignore
