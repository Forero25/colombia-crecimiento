"""GitHub Innovation Graph (CC0): desarrolladores, repositorios y pushes por economía y trimestre.
Fuente: https://github.com/github/innovationgraph"""
import os, urllib.request

BASE = "https://raw.githubusercontent.com/github/innovationgraph/main/data/"
ARCHIVOS = ["developers.csv", "repositories.csv", "git_pushes.csv", "organizations.csv"]


def main(destino="data/raw/innovation_graph"):
    os.makedirs(destino, exist_ok=True)
    for a in ARCHIVOS:
        urllib.request.urlretrieve(BASE + a, f"{destino}/{a}")
        print(a, os.path.getsize(f"{destino}/{a}"))


if __name__ == "__main__":
    main()
