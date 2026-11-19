"""Lectura de los marts de PostgreSQL y utilidades comunes."""
import json, os
import numpy as np
import pandas as pd
import psycopg

RES, PUB = "resultados", "publicado"
SEMILLA = 2026


def con():
    return psycopg.connect(host=os.environ.get("PGHOST", "localhost"), port=os.environ.get("PGPORT", "5432"),
                           user=os.environ.get("PGUSER", "postgres"), password=os.environ.get("PGPASSWORD", ""),
                           dbname=os.environ.get("PGDATABASE", "crecimiento"))


def leer(sql):
    with con() as c, c.cursor() as cur:
        cur.execute(sql)
        cols = [d.name for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)


def panel():
    df = leer("SELECT * FROM marts.panel_analisis ORDER BY iso3, anio")
    for c in df.columns:
        if c not in ("iso3", "pais", "region", "ingreso", "latinoamerica"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _limpio(o, d=9):
    if isinstance(o, float):
        return None if o != o else round(o, d)
    if isinstance(o, (np.floating,)):
        return None if o != o else round(float(o), d)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, dict):
        return {str(k): _limpio(v, d) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_limpio(v, d) for v in o]
    return o


def guardar(nombre, obj):
    os.makedirs(RES, exist_ok=True)
    json.dump(_limpio(obj), open(f"{RES}/{nombre}.json", "w"), ensure_ascii=False, indent=1, allow_nan=False)
