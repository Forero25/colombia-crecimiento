# Colombia frente a sus gemelos

¿Le ha ido bien a Colombia? Depende de con quién se compare. Este proyecto busca a los países que más se parecen a Colombia por su estructura económica, compara su crecimiento desde 2000, pregunta si la creación de empresas y startups lo anticipa y pronostica los próximos años con un modelo evaluado hacia adelante.

- **Artículo:** [nicolasforero.pages.dev/escritos/colombia-gemelos](https://nicolasforero.pages.dev/escritos/colombia-gemelos/)
- **App interactiva:** `app.py` (Shiny for Python), publicada en [Posit Connect Cloud](https://01a1f2ea-37bd-6494-2069-7cdcd16b6f1c.share.connect.posit.cloud/).
- **Método y glosario:** [METODO.md](METODO.md)

## Arquitectura

```
Banco Mundial (WDI, WGI) ─┐
Penn World Table 11.0 ────┤   ingesta/ (Python)        dbt/ (SQL probado)            analisis/ (Python)
RUES (datos.gov.co) ──────┼──> raw.* en PostgreSQL ──> staging.* ──> marts.panel ──> gemelos, crecimiento,   ──> resultados/*.json ──> app.py
GitHub Innovation Graph ──┘                                         marts.rues_anual   emprendimiento, pronóstico
```

- **Docker Compose:** `docker compose up --build --abort-on-container-exit` levanta PostgreSQL 16, espera a que esté listo y corre el pipeline completo (`correr.sh`). GitHub Actions lo ejecuta el día 2 de cada mes y guarda los resultados.
- **dbt:** modelos `staging` (países, indicadores, GitHub, RUES, PWT) y `marts` (panel país-año, universo de análisis, RUES anual), con 22 pruebas: unicidad, nulos, rangos plausibles y cobertura de la región.
- **Pruebas en Python** (`tests/`): el método de gemelos recupera un clon, el panel detecta un efecto que existe y no inventa uno que no existe, el objetivo del pronóstico no filtra información del futuro y los resultados son coherentes (el modelo supera al ingenuo; el RUES agregado cuadra con Confecámaras).

## Lo que este proyecto no hace

- **No mide el capital de riesgo.** No hay datos abiertos por país; LAVCA y Crunchbase son de pago. Se cita como contexto, no entra en los modelos.
- **No prueba causalidad.** El panel con efectos fijos muestra asociaciones dentro de cada país a lo largo del tiempo; no descarta que un tercer factor mueva a la vez empresas y crecimiento.
- **No es un pronóstico oficial.** Los intervalos son anchos a propósito: el crecimiento de un país es difícil de predecir, y el modelo lo dice.
- **No publica datos personales.** Del RUES solo se piden conteos agregados a la API de datos.gov.co.
- **Las empresas nuevas no son startups.** La densidad del Banco Mundial cuenta sociedades de responsabilidad limitada nuevas, de cualquier tipo; es la mejor medida comparable entre países, no una medida de startups tecnológicas. Los desarrolladores en GitHub son una señal complementaria del ecosistema tecnológico.

## Fuentes y licencias

- Banco Mundial, World Development Indicators y Worldwide Governance Indicators (CC BY 4.0).
- Feenstra, Inklaar y Timmer, Penn World Table 11.0, DataverseNL (CC BY 4.0).
- Registro Único Empresarial y Social (RUES), datos.gov.co, conjunto c82u-588k (CC BY-SA 4.0).
- GitHub Innovation Graph (CC0).
- Confecámaras, informes de dinámica de creación de empresas (solo para validar).

Código bajo licencia MIT. José Nicolás Forero Urrego.
