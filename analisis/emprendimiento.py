"""Emprendimiento y crecimiento.

1. ¿Dónde está Colombia? Densidad de empresas nuevas (Banco Mundial) y desarrolladores en GitHub por cada mil
   habitantes, frente a lo esperado para su nivel de ingreso, sus gemelos y la región.
2. ¿Crear empresas antecede a crecer, o es al revés? Panel de países con efectos fijos de país y de año:
   - crecimiento promedio de los 3 años siguientes contra la densidad de empresas de hoy;
   - cambio en la densidad de los 3 años siguientes contra el crecimiento de hoy.
   Si solo la segunda relación aparece, las empresas siguen al ciclo; si aparece la primera, la creación de
   empresas anticipa crecimiento (sin que eso pruebe causalidad).
3. Colombia por dentro (RUES): sociedades nuevas por año, peso de las SAS, sectores y cámaras."""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def posicion(p, gemelos, var, desde, hasta):
    x = p[(p.anio >= desde) & (p.anio <= hasta)].groupby("iso3").agg(v=(var, "mean"), y=("pib_pc_ppa", "mean"),
                                                                      lat=("latinoamerica", "first"), pais=("pais", "first")).dropna()
    x = x[x.v > 0]
    m = smf.ols("np.log(v) ~ np.log(y)", data=x).fit()
    x["esperado"] = np.exp(m.predict(x))
    x["razon"] = x.v / x.esperado
    col = x.loc["COL"]
    return {"variable": var, "ventana": [desde, hasta], "n": int(len(x)),
            "colombia": float(col.v), "esperado_colombia": float(col.esperado), "razon_colombia": float(col.razon),
            "percentil_razon": float((x.razon < col.razon).mean()),
            "mediana_gemelos": float(x[x.index.isin(gemelos)].v.median()),
            "mediana_latam": float(x[x.lat.astype(bool) & (x.index != "COL")].v.median()),
            "elasticidad_ingreso": float(m.params.iloc[1]),
            "puntos": x.reset_index()[["iso3", "pais", "v", "y", "esperado", "lat"]].to_dict("records")}


def panel_fe(p, h=3):
    x = p[["iso3", "anio", "crec_pib_pc", "densidad_empresas", "pib_pc_ppa", "inversion_pib"]].sort_values(["iso3", "anio"]).copy()
    g = x.groupby("iso3")
    x["crec_fut"] = sum(g.crec_pib_pc.shift(-k) for k in range(1, h + 1)) / h
    x["log_dens"] = np.log(x.densidad_empresas.where(x.densidad_empresas > 0))
    x["dlog_dens_fut"] = x.groupby("iso3").log_dens.shift(-h) - x.log_dens
    x["log_y"] = np.log(x.pib_pc_ppa)
    out = {}
    d1 = x.dropna(subset=["crec_fut", "log_dens", "log_y", "crec_pib_pc"])
    m1 = smf.ols("crec_fut ~ log_dens + crec_pib_pc + log_y + C(iso3) + C(anio)", data=d1).fit(
        cov_type="cluster", cov_kwds={"groups": d1.iso3.astype("category").cat.codes})
    out["densidad_a_crecimiento"] = {"coef": float(m1.params["log_dens"]), "ee": float(m1.bse["log_dens"]),
                                     "p": float(m1.pvalues["log_dens"]), "n": int(m1.nobs), "paises": int(d1.iso3.nunique()),
                                     "lectura": "puntos porcentuales de crecimiento anual futuro por cada 100 % más de densidad"}
    d2 = x.dropna(subset=["dlog_dens_fut", "crec_pib_pc", "log_dens", "log_y"])
    m2 = smf.ols("dlog_dens_fut ~ crec_pib_pc + log_dens + log_y + C(iso3) + C(anio)", data=d2).fit(
        cov_type="cluster", cov_kwds={"groups": d2.iso3.astype("category").cat.codes})
    out["crecimiento_a_densidad"] = {"coef": float(m2.params["crec_pib_pc"]), "ee": float(m2.bse["crec_pib_pc"]),
                                     "p": float(m2.pvalues["crec_pib_pc"]), "n": int(m2.nobs), "paises": int(d2.iso3.nunique()),
                                     "lectura": "cambio en log densidad en 3 años por cada punto de crecimiento hoy"}
    # mismo contemporáneo, para ver la correlación simple
    d3 = x.dropna(subset=["crec_pib_pc", "log_dens"])
    m3 = smf.ols("crec_pib_pc ~ log_dens + C(iso3) + C(anio)", data=d3).fit(cov_type="cluster", cov_kwds={"groups": d3.iso3.astype("category").cat.codes})
    out["contemporaneo"] = {"coef": float(m3.params["log_dens"]), "p": float(m3.pvalues["log_dens"]), "n": int(m3.nobs)}
    return out


def colombia_rues():
    from .datos import leer
    a = leer("SELECT anio, tipo, nuevas, nuevas_sas, meses FROM marts.rues_anual ORDER BY anio, tipo")
    a = a.astype({"anio": int, "nuevas": float, "meses": int})
    a["nuevas_sas"] = pd.to_numeric(a.nuevas_sas)
    conf = pd.read_csv("entradas/confecamaras.csv")
    soc = a[a.tipo == "sociedad"].set_index("anio")
    val = []
    for _, r in conf.dropna(subset=["sociedades"]).iterrows():
        nuestro = float(soc.loc[int(r.anio), "nuevas"])
        val.append({"anio": int(r.anio), "confecamaras": float(r.sociedades), "rues_agregado": nuestro,
                    "diferencia_pct": 100 * (nuestro / r.sociedades - 1), "fuente": r.fuente})
    sect = leer("""SELECT anio, ciiu2, sum(n) n FROM staging.stg_rues_sector WHERE tipo = 'juridica' AND anio >= 2015 GROUP BY 1, 2""")
    sect["n"] = sect.n.astype(float)
    cam = leer("""SELECT camara, anio, sum(n) n FROM staging.stg_rues WHERE tipo = 'sociedad' AND anio >= 2015 GROUP BY 1, 2""")
    cam["n"] = cam.n.astype(float)
    mensual = leer("""SELECT mes, sum(n) n FROM staging.stg_rues WHERE tipo = 'sociedad' GROUP BY 1 ORDER BY 1""")
    return {"anual": a.to_dict("records"), "validacion": val,
            "sas_participacion": {int(i): float(r.nuevas_sas / r.nuevas) for i, r in soc.iterrows()},
            "sectores": sect.to_dict("records"), "camaras": cam.to_dict("records"),
            "mensual": [{"mes": str(r.mes), "n": float(r.n)} for r in mensual.itertuples()]}


def analizar(p, gemelos):
    return {"densidad": posicion(p, gemelos, "densidad_empresas", 2015, 2022),
            "github": posicion(p, gemelos, "desarrolladores_por_mil", 2023, 2025),
            "panel": panel_fe(p), "rues": colombia_rues()}
