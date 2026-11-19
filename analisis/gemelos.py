"""¿Con quién se parece Colombia? Países "gemelos" por estructura económica, no por geografía.

Para cada país se promedian, en una ventana de años, rasgos de su estructura: nivel de ingreso, peso de la
agricultura, la manufactura y los servicios, apertura comercial, inversión, dependencia de materias primas,
demografía, urbanización, profundidad financiera, calidad institucional e internet. Se estandarizan, se reduce
la dimensión con componentes principales y se mide la distancia entre países. Los "gemelos" son los más cercanos;
los clústeres agrupan a todos. La estabilidad se mide repitiendo el cálculo con variables y países remuestreados."""
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from .datos import SEMILLA

RASGOS = {
    "log_pib_pc": "Ingreso por persona (log, PPA)",
    "agro_pib": "Agricultura (% PIB)",
    "manufactura_pib": "Manufactura (% PIB)",
    "servicios_pib": "Servicios (% PIB)",
    "comercio_pib": "Comercio exterior (% PIB)",
    "inversion_pib": "Inversión (% PIB)",
    "materias_primas": "Combustibles y minerales (% exportaciones)",
    "pob_15_64": "Población en edad de trabajar (%)",
    "urbana": "Población urbana (%)",
    "credito_pib": "Crédito privado (% PIB)",
    "instituciones": "Calidad institucional (promedio WGI)",
    "internet": "Usuarios de internet (%)",
}


def matriz(p, desde, hasta, min_cobertura=0.75):
    x = p[(p.anio >= desde) & (p.anio <= hasta)].copy()
    x["log_pib_pc"] = np.log(x.pib_pc_ppa)
    x["materias_primas"] = x.export_combustibles.fillna(0) + x.export_minerales.fillna(0)
    x.loc[x.export_combustibles.isna() & x.export_minerales.isna(), "materias_primas"] = np.nan
    x["instituciones"] = x[["efectividad_gobierno", "calidad_regulatoria", "estado_derecho", "control_corrupcion"]].mean(axis=1)
    m = x.groupby("iso3")[list(RASGOS)].mean()
    info = x.groupby("iso3")[["pais", "region", "ingreso", "latinoamerica"]].last()
    cob = m.notna().mean(axis=1)
    m = m[cob >= min_cobertura]
    imputados = int(m.isna().sum().sum())
    # imputación: mediana del mismo nivel de ingreso; si no hay, mediana global
    grupo = info.loc[m.index, "ingreso"]
    for c in m.columns:
        m[c] = m[c].fillna(m.groupby(grupo)[c].transform("median")).fillna(m[c].median())
    return m, info.loc[m.index], imputados


def vecinos(m, pais="COL", n=10, var_pca=0.9):
    Z = StandardScaler().fit_transform(m)
    pca = PCA(var_pca, random_state=0).fit(Z)
    P = pca.transform(Z)
    i = list(m.index).index(pais)
    d = np.sqrt(((P - P[i]) ** 2).sum(axis=1))
    s = pd.Series(d, index=m.index).drop(pais).sort_values()
    return s.head(n), pca, P


def estabilidad(m, pais="COL", n=10, reps=500):
    """Frecuencia con que cada país aparece entre los n gemelos al quitar 3 rasgos al azar y remuestrear países."""
    rng = np.random.default_rng(SEMILLA)
    cuenta = pd.Series(0.0, index=m.index)
    for _ in range(reps):
        cols = rng.choice(m.columns, len(m.columns) - 3, replace=False)
        otros = [x for x in m.index if x != pais]
        keep = list(rng.choice(otros, int(0.9 * len(otros)), replace=False)) + [pais]
        s, _, _ = vecinos(m.loc[keep, cols], pais, n)
        cuenta[s.index] += 1
    # se normaliza por las veces que cada país estuvo disponible (90 %)
    return (cuenta / (reps * 0.9)).clip(upper=1).drop(pais).sort_values(ascending=False)


def clusteres(m):
    Z = StandardScaler().fit_transform(m)
    sil = {}
    for k in range(4, 11):
        sil[k] = float(silhouette_score(Z, KMeans(k, n_init=50, random_state=0).fit_predict(Z)))
    k = max(sil, key=sil.get)
    km = KMeans(k, n_init=100, random_state=0).fit(Z)
    ward = AgglomerativeClustering(k, linkage="ward").fit(Z)
    return k, sil, km.labels_, float(adjusted_rand_score(km.labels_, ward.labels_))


def analizar(p):
    out = {"rasgos": RASGOS}
    for nombre, (a, b) in {"reciente": (2015, 2024), "anterior": (1996, 2005)}.items():
        m, info, imp = matriz(p, a, b)
        s, pca, P = vecinos(m)
        k, sil, etiquetas, ari = clusteres(m)
        grupo_col = etiquetas[list(m.index).index("COL")]
        bloque = {"ventana": [a, b], "n_paises": len(m), "valores_imputados": imp,
                  "varianza_pca": pca.explained_variance_ratio_.tolist(),
                  "gemelos": [{"iso3": i, "pais": info.loc[i, "pais"], "region": info.loc[i, "region"], "distancia": float(d)} for i, d in s.items()],
                  "k": k, "silueta": sil, "acuerdo_ward": ari,
                  "mismo_grupo": [info.loc[i, "pais"] for i in m.index[etiquetas == grupo_col] if i != "COL"],
                  "colombia": m.loc["COL"].to_dict(),
                  "mediana_gemelos": m.loc[s.index].median().to_dict(),
                  "mediana_latam": m[info.latinoamerica.astype(bool)].median().to_dict()}
        if nombre == "reciente":
            est = estabilidad(m)
            bloque["estabilidad"] = [{"iso3": i, "pais": info.loc[i, "pais"], "frecuencia": float(f)} for i, f in est.head(20).items()]
            mapa = pd.DataFrame(P[:, :2], index=m.index, columns=["pc1", "pc2"]).join(info).assign(grupo=etiquetas)
            bloque["mapa"] = mapa.reset_index().to_dict("records")
            bloque["cargas"] = {c: pca.components_[:2, j].tolist() for j, c in enumerate(m.columns)}
        out[nombre] = bloque
    return out
