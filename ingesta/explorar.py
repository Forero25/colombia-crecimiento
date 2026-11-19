"""Exploración del RUES en datos.gov.co: ¿se puede agregar por año sin bajar datos personales?"""
import json, urllib.request, urllib.parse

UA = {"User-Agent": "colombia-crecimiento portfolio project"}
B = "https://www.datos.gov.co/resource/c82u-588k.json?"


def get(q):
    url = B + urllib.parse.urlencode(q)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
            return r.read()[:1500]
    except Exception as e:  # noqa: BLE001
        return f"ERROR {e}".encode()


print("formato fechas:", get({"$select": "fecha_matricula, fecha_cancelacion, estado_matricula, organizacion_juridica, categoria_matricula, cod_ciiu_act_econ_pri, camara_comercio", "$limit": 5}))
print("substring:", get({"$select": "substring(fecha_matricula, 1, 4) as anio, count(*) as n", "$group": "anio", "$order": "anio", "$limit": 100}))
print("estados:", get({"$select": "estado_matricula, count(*) as n", "$group": "estado_matricula"}))
print("organizacion:", get({"$select": "organizacion_juridica, count(*) as n", "$group": "organizacion_juridica"}))
print("categoria:", get({"$select": "categoria_matricula, count(*) as n", "$group": "categoria_matricula"}))
