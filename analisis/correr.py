"""Corre todos los análisis sobre los marts de PostgreSQL y guarda resultados/*.json y publicado/*.csv."""
import os
import warnings

import pandas as pd

from . import crecimiento, emprendimiento, gemelos, pronostico
from .datos import PUB, guardar, panel

warnings.filterwarnings("ignore")
UMBRAL_ESTABLE = 0.75


def main():
    p = panel()
    g = gemelos.analizar(p)
    estables = [e["iso3"] for e in g["reciente"]["estabilidad"] if e["frecuencia"] >= UMBRAL_ESTABLE]
    g["gemelos_estables"] = estables
    g["umbral_estable"] = UMBRAL_ESTABLE
    guardar("gemelos", g)
    guardar("crecimiento", crecimiento.analizar(p, estables))
    guardar("emprendimiento", emprendimiento.analizar(p, estables))
    guardar("pronostico", pronostico.analizar(p))
    os.makedirs(PUB, exist_ok=True)
    cols = ["iso3", "pais", "region", "ingreso", "latinoamerica", "anio", "crec_pib", "crec_pib_pc", "pib_pc_ppa",
            "inversion_pib", "inflacion", "densidad_empresas", "desarrolladores_por_mil", "manufactura_pib",
            "export_combustibles", "export_minerales", "efectividad_gobierno", "internet", "ptf"]
    p[cols].to_csv(f"{PUB}/panel_resumido.csv", index=False)
    print("gemelos estables:", estables)


if __name__ == "__main__":
    main()
