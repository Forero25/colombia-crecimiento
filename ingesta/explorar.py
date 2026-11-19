"""Exploración de fuentes de Colombia: busca en el catálogo de datos.gov.co conjuntos sobre creación de empresas,
y prueba Penn World Table. Solo imprime; no guarda nada."""
import json, urllib.request, urllib.parse

UA = {"User-Agent": "colombia-crecimiento portfolio project"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


for q in ["matriculas registro mercantil", "creacion de empresas", "RUES", "camara de comercio empresas", "tejido empresarial"]:
    url = "https://api.us.socrata.com/api/catalog/v1?" + urllib.parse.urlencode({"domains": "www.datos.gov.co", "q": q, "limit": 12})
    try:
        d = json.loads(get(url))
        print("\n###", q)
        for r in d["results"]:
            res = r["resource"]
            print(res["id"], "|", res["name"][:90], "|", res.get("data_updated_at", "")[:10], "| filas?", res.get("page_views", {}).get("page_views_total", ""))
    except Exception as e:  # noqa: BLE001
        print("error", q, e)

for url in ["https://dataverse.nl/api/datasets/:persistentId/?persistentId=doi:10.34894/FABVLR",
            "https://www.rug.nl/ggdc/productivity/pwt/"]:
    try:
        b = get(url)
        print("\nPWT", url, len(b), b[:300])
    except Exception as e:  # noqa: BLE001
        print("PWT error", url, e)
