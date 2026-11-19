"""Indicadores del Banco Mundial (WDI y WGI) para todos los países, 1990 en adelante.

API pública: https://api.worldbank.org/v2 (licencia CC BY 4.0).
Escribe data/raw/banco_mundial.csv con columnas: iso3, pais, indicador, anio, valor.
"""
import csv, json, os, sys, time, urllib.request

UA = {"User-Agent": "colombia-crecimiento portfolio project (github.com/Forero25/colombia-crecimiento)"}

# indicador -> (fuente, descripción corta). Fuente 2 = WDI, 3 = Worldwide Governance Indicators.
INDICADORES = {
    "NY.GDP.MKTP.KD.ZG": (2, "Crecimiento del PIB (%)"),
    "NY.GDP.PCAP.KD.ZG": (2, "Crecimiento del PIB por persona (%)"),
    "NY.GDP.PCAP.PP.KD": (2, "PIB por persona, PPA, dólares constantes"),
    "NY.GDP.MKTP.KD": (2, "PIB, dólares constantes"),
    "NV.AGR.TOTL.ZS": (2, "Agricultura, % del PIB"),
    "NV.IND.TOTL.ZS": (2, "Industria, % del PIB"),
    "NV.IND.MANF.ZS": (2, "Manufactura, % del PIB"),
    "NV.SRV.TOTL.ZS": (2, "Servicios, % del PIB"),
    "NE.TRD.GNFS.ZS": (2, "Comercio, % del PIB"),
    "NE.GDI.TOTL.ZS": (2, "Formación bruta de capital, % del PIB"),
    "TX.VAL.FUEL.ZS.UN": (2, "Combustibles, % de exportaciones de mercancías"),
    "TX.VAL.MMTL.ZS.UN": (2, "Minerales y metales, % de exportaciones de mercancías"),
    "TX.VAL.TECH.MF.ZS": (2, "Alta tecnología, % de exportaciones manufactureras"),
    "BX.KLT.DINV.WD.GD.ZS": (2, "Inversión extranjera directa, % del PIB"),
    "FS.AST.PRVT.GD.ZS": (2, "Crédito al sector privado, % del PIB"),
    "FP.CPI.TOTL.ZG": (2, "Inflación (%)"),
    "SP.POP.TOTL": (2, "Población"),
    "SP.POP.GROW": (2, "Crecimiento de la población (%)"),
    "SP.POP.1564.TO.ZS": (2, "Población de 15 a 64 años (%)"),
    "SP.URB.TOTL.IN.ZS": (2, "Población urbana (%)"),
    "SL.TLF.CACT.ZS": (2, "Participación laboral (%)"),
    "SL.UEM.TOTL.ZS": (2, "Desempleo (%)"),
    "SE.TER.ENRR": (2, "Matrícula en educación terciaria (%)"),
    "IT.NET.USER.ZS": (2, "Usuarios de internet (%)"),
    "GB.XPD.RSDV.GD.ZS": (2, "Gasto en I+D, % del PIB"),
    "IC.BUS.NDNS.ZS": (2, "Nuevas empresas por cada 1.000 adultos"),
    "IC.BUS.NREG": (2, "Nuevas empresas registradas"),
    "GE.EST": (3, "Efectividad del gobierno"),
    "RQ.EST": (3, "Calidad regulatoria"),
    "RL.EST": (3, "Estado de derecho"),
    "CC.EST": (3, "Control de la corrupción"),
}


def pedir(url, intentos=4):
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            print("reintento", url, e, file=sys.stderr)
            time.sleep(5 * (i + 1))
    raise SystemExit(f"No se pudo leer {url}")


def paises():
    """Lista de países (sin agregados regionales) con región y nivel de ingreso."""
    d = pedir("https://api.worldbank.org/v2/country?format=json&per_page=400")[1]
    return [{"iso3": c["id"], "iso2": c["iso2Code"], "pais": c["name"], "region": c["region"]["value"],
             "ingreso": c["incomeLevel"]["value"], "lat": c["latitude"], "lon": c["longitude"]}
            for c in d if c["region"]["value"] != "Aggregates"]


def indicador(codigo, fuente, desde=1990, hasta=2026):
    url = (f"https://api.worldbank.org/v2/country/all/indicator/{codigo}?format=json&per_page=20000"
           f"&date={desde}:{hasta}&source={fuente}")
    pag = pedir(url)
    if not (isinstance(pag, list) and len(pag) > 1 and "pages" in pag[0]):
        # los indicadores de gobernanza cambiaron de código en la API (GOV_WGI_GE.EST); se prueba el nombre nuevo
        if fuente == 3 and not codigo.startswith("GOV_WGI_"):
            print("aviso:", codigo, "no existe con ese código; probando GOV_WGI_" + codigo, str(pag)[:200], file=sys.stderr)
            return [(i, codigo, a, v) for i, _c, a, v in indicador("GOV_WGI_" + codigo, fuente, desde, hasta)]
        raise SystemExit(f"Respuesta inesperada para {codigo}: {str(pag)[:300]}")
    filas = []
    for p in range(1, pag[0]["pages"] + 1):
        datos = pag[1] if p == 1 else pedir(url + f"&page={p}")[1]
        for x in datos or []:
            if x["value"] is not None:
                filas.append((x["countryiso3code"] or x["country"]["id"], codigo, int(x["date"]), float(x["value"])))
    return filas


def main(destino="data/raw"):
    os.makedirs(destino, exist_ok=True)
    ps = paises()
    with open(f"{destino}/paises.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ps[0]))
        w.writeheader(); w.writerows(ps)
    with open(f"{destino}/banco_mundial.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iso3", "indicador", "anio", "valor"])
        for cod, (fuente, desc) in INDICADORES.items():
            filas = indicador(cod, fuente)
            w.writerows(filas)
            print(f"{cod:22s} {len(filas):6d} filas  {desc}")
    with open(f"{destino}/indicadores.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["indicador", "fuente", "descripcion"])
        for cod, (fuente, desc) in INDICADORES.items():
            w.writerow([cod, "WDI" if fuente == 2 else "WGI", desc])


if __name__ == "__main__":
    main()
