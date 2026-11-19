"""Pronóstico del crecimiento del PIB por persona a 1 y 3 años, con evaluación hacia adelante.

Para cada año de prueba T (2008-2024), los modelos se entrenan solo con datos cuyo resultado ya se conocía antes de T,
y predicen el crecimiento de todos los países en T. Se compara:
- ingenuo: el promedio de los últimos 5 años del país;
- ridge: regresión lineal regularizada con los rasgos del país;
- gradient boosting: árboles (HistGradientBoosting), que manejan datos faltantes y relaciones no lineales;
- gradient boosting sin variables de emprendimiento, para medir si estas aportan.
Al final se pronostica Colombia con boosting y un intervalo conformal (ver pronosticar). La cobertura de un
intervalo de cuantiles directo también se reporta, porque resultó menor que la prometida."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .datos import SEMILLA

EMPRENDIMIENTO = ["log_dens", "d_log_dens"]


def preparar(p, h):
    x = p.sort_values(["iso3", "anio"]).copy()
    g = x.groupby("iso3")
    x["y"] = sum(g.crec_pib_pc.shift(-k) for k in range(1, h + 1)) / h
    for k in (0, 1, 2):
        x[f"crec_l{k}"] = g.crec_pib_pc.shift(k)
    x["crec_media5"] = g.crec_pib_pc.transform(lambda s: s.rolling(5, min_periods=3).mean())
    x["log_y"] = np.log(x.pib_pc_ppa)
    x["materias_primas"] = x.export_combustibles.fillna(0) + x.export_minerales.fillna(0)
    x["instituciones"] = x[["efectividad_gobierno", "calidad_regulatoria", "estado_derecho", "control_corrupcion"]].mean(axis=1)
    x["log_dens"] = np.log(x.densidad_empresas.where(x.densidad_empresas > 0))
    x["d_log_dens"] = x.log_dens - g.log_dens.shift(1)
    # ciclo mundial: crecimiento mediano del año, sin el propio país
    x["crec_mundo"] = x.groupby("anio").crec_pib_pc.transform("median")
    x["inflacion_log"] = np.sign(x.inflacion) * np.log1p(np.abs(x.inflacion))
    feats = ["crec_l0", "crec_l1", "crec_l2", "crec_media5", "log_y", "inversion_pib", "inflacion_log", "credito_pib",
             "comercio_pib", "materias_primas", "crec_poblacion", "pob_15_64", "instituciones", "crec_mundo"] + EMPRENDIMIENTO
    return x, feats


def modelos(feats_sin):
    return {
        "ridge": lambda f: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), RidgeCV(alphas=np.logspace(-2, 3, 20))),
        "boosting": lambda f: HistGradientBoostingRegressor(max_depth=4, learning_rate=0.05, max_iter=300, min_samples_leaf=40,
                                                             l2_regularization=1.0, random_state=SEMILLA),
        "boosting_sin_emprendimiento": lambda f: HistGradientBoostingRegressor(max_depth=4, learning_rate=0.05, max_iter=300,
                                                                                min_samples_leaf=40, l2_regularization=1.0, random_state=SEMILLA),
    }


def evaluar(p, h, desde=2012, hasta=2024):
    """Desde 2012: la densidad de empresas empieza en 2006 y los modelos necesitan varios años con ella."""
    x, feats = preparar(p, h)
    feats_sin = [f for f in feats if f not in EMPRENDIMIENTO]
    filas, errores_cuantil = [], []
    for T in range(desde, hasta - h + 2):
        tr = x[(x.anio + h <= T - 1) & x.y.notna()]   # resultado conocido antes de T
        te = x[(x.anio == T - 1) & x.y.notna()]        # se predice desde el año T-1 hacia adelante
        if len(te) == 0:
            continue
        pred = {"ingenuo": te.crec_media5.fillna(te.crec_l0).values}
        for nombre, fab in modelos(feats_sin).items():
            fs = feats_sin if nombre.endswith("sin_emprendimiento") else feats
            fs = [f for f in fs if tr[f].notna().any()]
            m = fab(fs).fit(tr[fs], tr.y)
            pred[nombre] = m.predict(te[fs])
        for i, (_, r) in enumerate(te.iterrows()):
            filas.append({"T": T, "iso3": r.iso3, "y": r.y, **{k: float(v[i]) for k, v in pred.items()}})
        q = {a: HistGradientBoostingRegressor(loss="quantile", quantile=a, max_depth=4, learning_rate=0.05, max_iter=300,
                                              min_samples_leaf=40, random_state=SEMILLA).fit(tr[feats], tr.y).predict(te[feats]) for a in (0.1, 0.9)}
        errores_cuantil.append(float(((te.y.values >= q[0.1]) & (te.y.values <= q[0.9])).mean()))
    d = pd.DataFrame(filas)
    nombres = ["ingenuo", "ridge", "boosting", "boosting_sin_emprendimiento"]
    mae = {n: float((d[n] - d.y).abs().mean()) for n in nombres}
    mae_col = {n: float((d[d.iso3 == "COL"][n] - d[d.iso3 == "COL"].y).abs().mean()) for n in nombres}
    # bootstrap por año de la diferencia de error entre boosting con y sin emprendimiento
    rng = np.random.default_rng(SEMILLA)
    por_t = d.assign(dif=(d.boosting - d.y).abs() - (d.boosting_sin_emprendimiento - d.y).abs()).groupby("T").dif.mean()
    boot = [rng.choice(por_t.values, len(por_t)).mean() for _ in range(4000)]
    errores_abs = (d.boosting - d.y).abs()
    return {"h": h, "n": int(len(d)), "error_abs_p80": float(errores_abs.quantile(0.8)), "anios_prueba": [int(d["T"].min()), int(d["T"].max())], "mae": mae, "mae_colombia": mae_col,
            "aporte_emprendimiento": {"dif_mae": float(por_t.mean()), "ic95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]},
            "cobertura_intervalo_80": float(np.mean(errores_cuantil)),
            "colombia": d[d.iso3 == "COL"][["T", "y", "ingenuo", "ridge", "boosting"]].to_dict("records")}


def pronosticar(p, h, error_p80):
    """Pronóstico puntual con boosting e intervalo conformal: ± el percentil 80 de los errores absolutos que el mismo
    modelo cometió en la evaluación hacia adelante. Por construcción cubrió el 80 % de los casos pasados."""
    x, feats = preparar(p, h)
    tr = x[x.y.notna()]
    ultimo = x[(x.iso3 == "COL") & x.crec_pib_pc.notna()].anio.max()
    fila = x[(x.iso3 == "COL") & (x.anio == ultimo)]
    out = {"desde": int(ultimo), "h": h, "anios": [int(ultimo) + 1, int(ultimo) + h]}
    m = HistGradientBoostingRegressor(max_depth=4, learning_rate=0.05, max_iter=300, min_samples_leaf=40, l2_regularization=1.0,
                                      random_state=SEMILLA).fit(tr[feats], tr.y)
    out["media"] = float(m.predict(fila[feats])[0])
    out["bajo"], out["alto"] = out["media"] - error_p80, out["media"] + error_p80
    out["crec_poblacion_ultimo"] = float(fila.crec_poblacion.iloc[0])
    return out


def analizar(p):
    ev = {f"h{h}": evaluar(p, h) for h in (1, 3)}
    return {"evaluacion": ev, "pronostico": {f"h{h}": pronosticar(p, h, ev[f"h{h}"]["error_abs_p80"]) for h in (1, 3)}}
