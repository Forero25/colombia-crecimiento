"""Crecimiento de Colombia frente a sus gemelos, la región y el mundo.

1. Trayectoria del ingreso por persona (PPA), índice 2000 = 100.
2. Crecimiento anual promedio por décadas.
3. Convergencia: los países pobres suelen crecer más rápido. ¿Creció Colombia lo que se esperaba dado su ingreso
   inicial, su inversión y sus instituciones? (regresión entre países, 2000-2024)
4. Contabilidad del crecimiento (Penn World Table): cuánto del crecimiento del producto por trabajador vino de
   más capital, de más capital humano y de productividad (PTF)."""
import numpy as np
import pandas as pd
import statsmodels.api as sm


def grupos(p, gemelos):
    lat = set(p.loc[p.latinoamerica.astype(bool), "iso3"])
    return {"Colombia": {"COL"}, "Gemelos": set(gemelos), "Latinoamérica": lat - {"COL"}, "Mundo": set(p.iso3)}


def trayectoria(p, g, base=2000):
    x = p[p.anio >= 1995][["iso3", "anio", "pib_pc_ppa"]].dropna()
    b = x[x.anio == base].set_index("iso3").pib_pc_ppa
    x = x[x.iso3.isin(b.index)].copy()
    x["indice"] = 100 * x.pib_pc_ppa / x.iso3.map(b)
    out = {}
    for nombre, paises in g.items():
        s = x[x.iso3.isin(paises)].groupby("anio").indice.median()
        out[nombre] = {int(a): float(v) for a, v in s.items()}
    return out


def por_periodo(p, g):
    periodos = {"2000-2009": (2000, 2009), "2010-2019": (2010, 2019), "2020-2025": (2020, 2025), "2000-2025": (2000, 2025)}
    out = {}
    for nombre, paises in g.items():
        x = p[p.iso3.isin(paises)]
        out[nombre] = {per: float(x[(x.anio >= a) & (x.anio <= b)].groupby("iso3").crec_pib_pc.mean().median())
                       for per, (a, b) in periodos.items()}
    return out


def convergencia(p, desde=2000, hasta=2024):
    x = p[(p.anio >= desde) & (p.anio <= hasta)]
    ini = p[p.anio == desde].set_index("iso3").pib_pc_ppa
    fin = p[p.anio == hasta].set_index("iso3").pib_pc_ppa
    g = (100 * (np.log(fin) - np.log(ini)) / (hasta - desde)).rename("crec")
    ctrl = x.groupby("iso3").agg(inversion=("inversion_pib", "mean"), instituciones=("efectividad_gobierno", "mean"),
                                 crec_pob=("crec_poblacion", "mean"))
    d = pd.concat([g, np.log(ini).rename("log_ini"), ctrl], axis=1).dropna()
    X = sm.add_constant(d[["log_ini", "inversion", "instituciones", "crec_pob"]])
    m = sm.OLS(d.crec, X).fit(cov_type="HC1")
    pred = m.predict(X)
    resid = (d.crec - pred)
    return {"n": int(len(d)), "coef": m.params.to_dict(), "p": m.pvalues.to_dict(), "r2": float(m.rsquared),
            "colombia": {"observado": float(d.crec["COL"]), "predicho": float(pred["COL"]), "residuo": float(resid["COL"]),
                         "percentil_residuo": float((resid < resid["COL"]).mean())},
            "puntos": d.assign(predicho=pred).reset_index().rename(columns={"index": "iso3"}).to_dict("records")}


def contabilidad(p, g, periodos=((1995, 2023), (2010, 2023))):
    x = p[["iso3", "anio", "pib_real", "capital_real", "empleo", "capital_humano", "participacion_trabajo", "ptf"]].dropna()
    out = {}
    for a, b in periodos:
        ini, fin = x[x.anio == a].set_index("iso3"), x[x.anio == b].set_index("iso3")
        comunes = ini.index.intersection(fin.index)
        ini, fin = ini.loc[comunes], fin.loc[comunes]
        T = b - a
        gy = 100 * (np.log(fin.pib_real / fin.empleo) - np.log(ini.pib_real / ini.empleo)) / T
        gk = 100 * (np.log(fin.capital_real / fin.empleo) - np.log(ini.capital_real / ini.empleo)) / T
        gh = 100 * (np.log(fin.capital_humano) - np.log(ini.capital_humano)) / T
        alfa = 1 - x[(x.anio >= a) & (x.anio <= b)].groupby("iso3").participacion_trabajo.mean().loc[comunes]
        d = pd.DataFrame({"producto_por_trabajador": gy, "capital": alfa * gk, "capital_humano": (1 - alfa) * gh})
        d["productividad"] = d.producto_por_trabajador - d.capital - d.capital_humano
        bloque = {}
        for nombre, paises in g.items():
            s = d[d.index.isin(paises)]
            bloque[nombre] = {**s.median().to_dict(), "n": int(len(s))}
        out[f"{a}-{b}"] = bloque
    return out


def analizar(p, gemelos):
    g = grupos(p, gemelos)
    return {"grupos": {k: sorted(v) for k, v in g.items() if k != "Mundo"}, "n_mundo": len(g["Mundo"]),
            "trayectoria": trayectoria(p, g), "por_periodo": por_periodo(p, g),
            "convergencia": convergencia(p), "contabilidad": contabilidad(p, g)}
