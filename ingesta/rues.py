"""Creación de empresas en Colombia desde el RUES (datos.gov.co, conjunto c82u-588k, CC BY-SA 4.0).

El conjunto tiene más de 9 millones de registros con datos personales (nombres, cédulas). Aquí NO se descarga
ningún registro: se piden a la API solo conteos agregados (año-mes, cámara de comercio, tipo de matrícula,
organización jurídica y sector CIIU a dos dígitos). Se excluyen las matrículas por traslado de domicilio,
que no son empresas nuevas."""
import csv, json, os, sys, time, urllib.parse, urllib.request

B = "https://www.datos.gov.co/resource/c82u-588k.json?"
UA = {"User-Agent": "colombia-crecimiento portfolio project (github.com/Forero25/colombia-crecimiento)"}
FILTRO = ("fecha_matricula >= '20050101' AND fecha_matricula < '20270101' "
          "AND estado_matricula != 'MATRÍCULA NUEVA, CONSTITUCIÓN POR TRASLADO'")


def pedir(q, intentos=4):
    url = B + urllib.parse.urlencode(q)
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            print("reintento", e, file=sys.stderr)
            time.sleep(10 * (i + 1))
    raise SystemExit("No se pudo consultar el RUES")


def agregar(select, group, destino, cols):
    filas, off, lote = [], 0, 50000
    while True:
        d = pedir({"$select": select + ", count(*) as n", "$where": FILTRO, "$group": group,
                   "$order": group, "$limit": lote, "$offset": off})
        filas += d
        if len(d) < lote:
            break
        off += lote
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols + ["n"])
        for x in filas:
            w.writerow([x.get(c, "") for c in cols] + [x["n"]])
    print(destino, len(filas), "filas", sum(int(x["n"]) for x in filas), "matrículas")


def main(destino="data/raw/rues"):
    os.makedirs(destino, exist_ok=True)
    agregar("substring(fecha_matricula, 1, 6) as ym, camara_comercio, categoria_matricula, organizacion_juridica",
            "ym, camara_comercio, categoria_matricula, organizacion_juridica", f"{destino}/mensual_camara.csv",
            ["ym", "camara_comercio", "categoria_matricula", "organizacion_juridica"])
    agregar("substring(fecha_matricula, 1, 4) as anio, categoria_matricula, substring(cod_ciiu_act_econ_pri, 1, 2) as ciiu2",
            "anio, categoria_matricula, ciiu2", f"{destino}/anual_sector.csv", ["anio", "categoria_matricula", "ciiu2"])


if __name__ == "__main__":
    main()
