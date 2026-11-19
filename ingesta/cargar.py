"""Carga los CSV crudos al esquema raw de PostgreSQL (COPY). Lee la conexión de variables de entorno."""
import csv, glob, os
import psycopg

TABLAS = {
    "raw.paises": ("data/raw/paises.csv", "iso3 text, iso2 text, pais text, region text, ingreso text, lat text, lon text"),
    "raw.banco_mundial": ("data/raw/banco_mundial.csv", "iso3 text, indicador text, anio int, valor double precision"),
    "raw.indicadores": ("data/raw/indicadores.csv", "indicador text, fuente text, descripcion text"),
    "raw.gh_developers": ("data/raw/innovation_graph/developers.csv", "developers bigint, iso2_code text, year int, quarter int"),
    "raw.gh_repositories": ("data/raw/innovation_graph/repositories.csv", "repositories bigint, iso2_code text, year int, quarter int"),
    "raw.gh_git_pushes": ("data/raw/innovation_graph/git_pushes.csv", "git_pushes bigint, iso2_code text, year int, quarter int"),
    "raw.gh_organizations": ("data/raw/innovation_graph/organizations.csv", "organizations bigint, iso2_code text, year int, quarter int"),
}


def conexion():
    return psycopg.connect(host=os.environ.get("PGHOST", "localhost"), port=os.environ.get("PGPORT", "5432"),
                           user=os.environ.get("PGUSER", "postgres"), password=os.environ.get("PGPASSWORD", ""),
                           dbname=os.environ.get("PGDATABASE", "crecimiento"))


def main():
    with conexion() as con, con.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw")
        for tabla, (ruta, cols) in TABLAS.items():
            if not os.path.exists(ruta):
                print("falta", ruta)
                continue
            cur.execute(f"DROP TABLE IF EXISTS {tabla} CASCADE; CREATE TABLE {tabla} ({cols})")
            nombres = [c.split()[0] for c in cols.split(", ")]
            with open(ruta, newline="", encoding="utf-8") as f:
                r = csv.reader(f)
                next(r)
                with cur.copy(f"COPY {tabla} ({', '.join(nombres)}) FROM STDIN") as cp:
                    for fila in r:
                        cp.write_row([None if v == "" else v for v in fila[:len(nombres)]])
            cur.execute(f"SELECT count(*) FROM {tabla}")
            print(tabla, cur.fetchone()[0])


if __name__ == "__main__":
    main()
