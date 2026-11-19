import json, os
import numpy as np
import pandas as pd
import pytest

from analisis.gemelos import vecinos
from analisis.pronostico import preparar
from analisis.emprendimiento import panel_fe

RES = os.path.join(os.path.dirname(__file__), "..", "resultados")


def test_el_gemelo_de_un_clon_es_el_clon():
    rng = np.random.default_rng(0)
    m = pd.DataFrame(rng.normal(size=(30, 6)), index=[f"P{i}" for i in range(29)] + ["COL"])
    m.loc["CLON"] = m.loc["COL"] + 0.01
    s, _, _ = vecinos(m, "COL", 3)
    assert s.index[0] == "CLON"


def _panel_sintetico(efecto, n=80, T=20, semilla=1):
    rng = np.random.default_rng(semilla)
    filas = []
    for i in range(n):
        nivel = rng.normal(0, 1)
        dens = np.exp(rng.normal(1, 0.3, T))
        for t in range(T):
            filas.append({"iso3": f"P{i}", "anio": 2000 + t, "densidad_empresas": dens[t], "pib_pc_ppa": np.exp(9 + 0.01 * t),
                          "inversion_pib": 20.0, "crec_pib_pc": nivel + rng.normal(0, 1)})
    d = pd.DataFrame(filas).sort_values(["iso3", "anio"])
    # el crecimiento de t+1 depende de la densidad de t
    d["crec_pib_pc"] += efecto * d.groupby("iso3").densidad_empresas.shift(1).pipe(np.log).fillna(0)
    return d


def test_panel_detecta_un_efecto_que_existe_y_no_inventa_uno_que_no():
    con = panel_fe(_panel_sintetico(3.0))["densidad_a_crecimiento"]
    sin = panel_fe(_panel_sintetico(0.0))["densidad_a_crecimiento"]
    assert con["coef"] > 0.5 and con["p"] < 0.01
    assert sin["p"] > 0.01


def test_sin_fuga_de_informacion_en_el_objetivo():
    d = pd.DataFrame({"iso3": ["A"] * 6, "anio": range(2000, 2006), "crec_pib_pc": [1, 2, 3, 4, 5, 6.0],
                      "pib_pc_ppa": 1000.0, "export_combustibles": 0, "export_minerales": 0, "efectividad_gobierno": 0,
                      "calidad_regulatoria": 0, "estado_derecho": 0, "control_corrupcion": 0, "densidad_empresas": 1.0, "inflacion": 2.0})
    x, feats = preparar(d, 1)
    # el objetivo del año t es el crecimiento de t+1, y ningún rasgo usa t+1
    assert x.loc[x.anio == 2002, "y"].iloc[0] == 4 and x.loc[x.anio == 2002, "crec_l0"].iloc[0] == 3


@pytest.mark.skipif(not os.path.exists(os.path.join(RES, "pronostico.json")), reason="sin resultados")
def test_resultados_coherentes():
    pr = json.load(open(os.path.join(RES, "pronostico.json")))
    for h in ("h1", "h3"):
        mae = pr["evaluacion"][h]["mae"]
        assert mae["boosting"] < mae["ingenuo"], "el modelo debe superar al ingenuo para justificarse"
    g = json.load(open(os.path.join(RES, "gemelos.json")))
    assert len(g["gemelos_estables"]) >= 5
    e = json.load(open(os.path.join(RES, "emprendimiento.json")))
    for v in e["rues"]["validacion"]:
        assert abs(v["diferencia_pct"]) < 6, "el RUES agregado debe cuadrar con Confecámaras"
