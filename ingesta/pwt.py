"""Penn World Table 11.0 (Feenstra, Inklaar y Timmer; CC BY 4.0), desde DataverseNL.
Se guardan las columnas que usa la descomposición del crecimiento."""
import io, os, urllib.request
import pandas as pd

URL = "https://dataverse.nl/api/access/datafile/554030"   # pwt110.dta
COLS = ["countrycode", "country", "year", "rgdpna", "rkna", "emp", "avh", "hc", "labsh", "rtfpna", "pop", "rgdpo", "ctfp"]


def main(destino="data/raw"):
    os.makedirs(destino, exist_ok=True)
    req = urllib.request.Request(URL, headers={"User-Agent": "colombia-crecimiento portfolio project"})
    with urllib.request.urlopen(req, timeout=300) as r:
        df = pd.read_stata(io.BytesIO(r.read()))
    df[[c for c in COLS if c in df]].to_csv(f"{destino}/pwt110.csv", index=False)
    print("pwt", df.shape, df.year.min(), df.year.max())


if __name__ == "__main__":
    main()
