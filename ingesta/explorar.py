"""Exploración de fuentes (solo imprime): columnas y volumen del RUES en datos.gov.co, y archivos de Penn World Table."""
import json, urllib.request, urllib.parse

UA = {"User-Agent": "colombia-crecimiento portfolio project"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


for ds in ["c82u-588k"]:
    meta = json.loads(get(f"https://www.datos.gov.co/api/views/{ds}.json"))
    print(ds, meta["name"], "| actualizado", meta.get("rowsUpdatedAt"), "| licencia", (meta.get("license") or {}).get("name"))
    print("columnas:", [(c["fieldName"], c["dataTypeName"]) for c in meta["columns"]])
    print("total:", get(f"https://www.datos.gov.co/resource/{ds}.json?$select=count(*)"))
    print("muestra:", get(f"https://www.datos.gov.co/resource/{ds}.json?$limit=2")[:1500])

d = json.loads(get("https://dataverse.nl/api/datasets/:persistentId/?persistentId=doi:10.34894/FABVLR"))
v = d["data"]["latestVersion"]
print("PWT version", v.get("versionNumber"), [(f["dataFile"]["id"], f["dataFile"]["filename"], f["dataFile"].get("filesize")) for f in v["files"]])
print("licencia", v.get("license"))
