"""Colombia frente a sus gemelos: crecimiento, emprendimiento y pronóstico.

App en Shiny for Python. Lee los resultados que produce el pipeline (PostgreSQL + dbt + Python) de este repositorio.
José Nicolás Forero Urrego · https://nicolasforero.pages.dev
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_plotly

AQUI = Path(__file__).parent
R = {f.stem: json.load(open(f, encoding="utf-8")) for f in (AQUI / "resultados").glob("*.json")}
P = pd.read_csv(AQUI / "publicado" / "panel_resumido.csv")
G, C, E, F = R["gemelos"], R["crecimiento"], R["emprendimiento"], R["pronostico"]
NOMBRE = P.groupby("iso3").pais.last().to_dict()
ESTABLES = G["gemelos_estables"]
AZUL, ROSA, MENTA, AMBAR, LAVANDA, TINTA, GRIS = "#4F6BD8", "#EBA3B0", "#8CCFB8", "#F5B482", "#B9A7E8", "#1F2430", "#C9CED6"
COL_GRUPO = {"Colombia": ROSA, "Gemelos": AZUL, "Latinoamérica": AMBAR, "Mundo": GRIS}


def num(x, d=1):
    if x is None or x != x:
        return "–"
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def pct(x, d=0):
    return "–" if x is None or x != x else num(100 * x, d) + " %"


def figura(fig, alto=380):
    fig.update_layout(height=alto, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, system-ui", color=TINTA, size=12), legend=dict(orientation="h", y=-0.2),
                      hoverlabel=dict(bgcolor="white"), modebar=dict(bgcolor="rgba(0,0,0,0)", color="#9CA3AF", activecolor=TINTA))
    fig.update_xaxes(gridcolor="#ECE8E0", zeroline=False)
    fig.update_yaxes(gridcolor="#ECE8E0", zeroline=False)
    return fig


def tabla(df, cols, fmts):
    cab = "".join(f"<th class='{'n' if c in fmts else ''}'>{t}</th>" for c, t in cols)
    filas = "".join("<tr>" + "".join(f"<td class='{'n' if c in fmts else ''}'>{fmts[c](r[c]) if c in fmts else r[c]}</td>" for c, _ in cols) + "</tr>"
                    for _, r in df.iterrows())
    return ui.HTML(f"<table class='tabla'><thead><tr>{cab}</tr></thead><tbody>{filas}</tbody></table>")


CSS = """
:root { --bs-body-bg: #F6F4EF; --bs-body-color: #1F2430; --bs-primary: #4F6BD8; --bs-border-color: #ECE8E0;
        --bs-body-font-family: Inter, system-ui, -apple-system, 'Segoe UI', sans-serif; }
body { background: #F6F4EF; } .navbar { background: #F6F4EF !important; border-bottom: 1px solid #ECE8E0; }
.navbar-brand { font-family: Georgia, serif; font-size: 1.3rem; }
.card { border: 1px solid #ECE8E0; box-shadow: none; border-radius: 14px; }
.card-header { background: transparent; font-weight: 600; border-bottom: 1px solid #ECE8E0; }
.bslib-value-box { border: 1px solid #ECE8E0 !important; border-radius: 14px; }
.bslib-value-box .value-box-title { color: #6B7280; font-size: .85rem; } .bslib-value-box .value-box-value { font-family: Georgia, serif; font-size: 1.8rem; }
.lead { font-size: 1.05rem; max-width: 62rem; color: #374151; } .nota { color: #6B7280; font-size: .85rem; }
table.tabla { width: 100%; font-size: .9rem; } table.tabla td, table.tabla th { padding: .38rem .5rem; border-bottom: 1px solid #ECE8E0; }
table.tabla th { color: #6B7280; font-weight: 600; font-size: .8rem; } table.tabla td.n, table.tabla th.n { text-align: right; font-variant-numeric: tabular-nums; }
footer.pie { color: #6B7280; font-size: .8rem; margin: 1.5rem 0 1rem; }
"""
pie = ui.tags.footer({"class": "pie"}, "Datos: Banco Mundial (WDI y WGI, CC BY 4.0), Penn World Table 11.0 (CC BY 4.0), RUES en datos.gov.co (CC BY-SA 4.0) y GitHub Innovation Graph (CC0). ",
                     "Código: ", ui.a("github.com/Forero25/colombia-crecimiento", href="https://github.com/Forero25/colombia-crecimiento"), " · ",
                     ui.a("José Nicolás Forero Urrego", href="https://nicolasforero.pages.dev"))


def tarjeta(t, *c, **kw):
    return ui.card(ui.card_header(t), *c, **kw)


rec = G["reciente"]
pr1 = F["pronostico"]["h1"]
app_ui = ui.page_navbar(
    ui.nav_panel("Gemelos",
        ui.p({"class": "lead"}, f"Comparé {rec['n_paises']} países por su estructura económica (2015-2024). "
             f"De los {len(ESTABLES)} gemelos estables de Colombia, {sum(P[P.iso3.isin(ESTABLES)].groupby('iso3').latinoamerica.first())} son de la región y el resto no: "
             "lo que los une es ser economías de ingreso medio que dependen de materias primas."),
        ui.layout_column_wrap(
            ui.value_box("Gemelos estables", str(len(ESTABLES))),
            ui.value_box("Países comparados", str(rec["n_paises"])),
            ui.value_box("Grupos encontrados", str(rec["k"])),
            width=1 / 3),
        tarjeta("Mapa de economías (componentes principales)", output_widget("g_mapa")),
        ui.layout_column_wrap(
            tarjeta("Qué tan estable es cada gemelo", ui.output_ui("t_estab")),
            tarjeta("Colombia frente a sus gemelos y la región", ui.output_ui("t_rasgos")), width=1 / 2)),
    ui.nav_panel("Crecimiento",
        tarjeta("Ingreso por persona (PPA), índice 2000 = 100 (mediana de cada grupo)", output_widget("g_tray")),
        ui.layout_column_wrap(
            tarjeta("Crecimiento anual del PIB por persona (%)", ui.output_ui("t_periodos")),
            tarjeta("¿De dónde vino el crecimiento? (puntos por año, 1995-2023)", output_widget("g_cont")), width=1 / 2),
        tarjeta("Convergencia: crecimiento 2000-2024 contra ingreso inicial", output_widget("g_conv"))),
    ui.nav_panel("Emprendimiento",
        ui.layout_column_wrap(
            tarjeta("Empresas nuevas por cada 1.000 adultos (2015-2022)", output_widget("g_dens")),
            tarjeta("Desarrolladores en GitHub por cada 1.000 habitantes (2023-2025)", output_widget("g_gh")), width=1 / 2),
        tarjeta("Sociedades nuevas en Colombia por mes (RUES)", output_widget("g_rues")),
        tarjeta("¿Crear empresas anticipa crecer? Panel de países con efectos fijos", ui.output_ui("t_panel"))),
    ui.nav_panel("Pronóstico",
        ui.layout_column_wrap(
            ui.value_box(f"Crecimiento del PIB por persona {pr1['anios'][0]}", num(pr1["media"], 1) + " %"),
            ui.value_box("Intervalo del 80 %", f"{num(pr1['bajo'], 1)} a {num(pr1['alto'], 1)} %"),
            ui.value_box("Error medio del modelo (1 año)", num(F["evaluacion"]["h1"]["mae"]["boosting"], 2) + " pp"), width=1 / 3),
        tarjeta("Evaluación hacia adelante: error absoluto medio (puntos porcentuales)", ui.output_ui("t_eval")),
        tarjeta("Colombia: lo que predijo cada modelo y lo que pasó (1 año)", output_widget("g_back"))),
    ui.nav_panel("Explorar",
        ui.layout_sidebar(
            ui.sidebar(ui.input_select("pais", "País", {k: v for k, v in sorted(NOMBRE.items(), key=lambda x: x[1])}, selected="PER"),
                       ui.input_radio_buttons("var", "Variable", {"crec_pib_pc": "Crecimiento del PIB por persona", "pib_pc_ppa": "Ingreso por persona (PPA)",
                                                                   "inversion_pib": "Inversión (% PIB)", "densidad_empresas": "Empresas nuevas por 1.000 adultos",
                                                                   "inflacion": "Inflación"}), open="desktop"),
            tarjeta("Colombia frente al país elegido", output_widget("g_exp")))),
    ui.nav_panel("Método", ui.div({"class": "lead"}, ui.markdown(open(AQUI / "METODO.md", encoding="utf-8").read()))),
    title="Colombia frente a sus gemelos", header=ui.tags.style(CSS), footer=pie, fillable=False)


def server(input, output, session):
    @render_plotly
    def g_mapa():
        m = pd.DataFrame(rec["mapa"])
        cols = [MENTA, AZUL, AMBAR, LAVANDA, ROSA, GRIS, "#9CA3AF", "#6B7280", "#D1D5DB", "#A7F3D0"]
        fig = go.Figure()
        for g, d in m.groupby("grupo"):
            fig.add_trace(go.Scatter(x=d.pc1, y=d.pc2, mode="markers", marker=dict(size=8, color=cols[g % 10]), name=f"Grupo {g + 1}", text=d.pais,
                                     hovertemplate="%{text}<extra></extra>"))
        for iso in ESTABLES + ["COL"]:
            r = m[m.iso3 == iso]
            if len(r):
                fig.add_annotation(x=r.pc1.iloc[0], y=r.pc2.iloc[0], text=r.pais.iloc[0], showarrow=False, yshift=11,
                                   font=dict(size=11, color=ROSA if iso == "COL" else TINTA))
        fig.update_xaxes(title=f"Componente 1 ({pct(rec['varianza_pca'][0])})")
        fig.update_yaxes(title=f"Componente 2 ({pct(rec['varianza_pca'][1])})")
        return figura(fig, 480)

    @render.ui
    def t_estab():
        d = pd.DataFrame(rec["estabilidad"]).head(12)
        return ui.div(tabla(d, [("pais", "País"), ("frecuencia", "Veces entre los 10 más cercanos")], {"frecuencia": pct}),
                      ui.p({"class": "nota"}, "500 repeticiones quitando 3 rasgos al azar y el 10 % de los países. Estables: 75 % o más."))

    @render.ui
    def t_rasgos():
        d = pd.DataFrame({"rasgo": [G["rasgos"][k] for k in rec["colombia"]], "col": rec["colombia"].values(),
                          "gem": [rec["mediana_gemelos"][k] for k in rec["colombia"]], "lat": [rec["mediana_latam"][k] for k in rec["colombia"]]})
        return tabla(d, [("rasgo", "Rasgo"), ("col", "Colombia"), ("gem", "Gemelos"), ("lat", "Latinoamérica")],
                     {"col": lambda v: num(v, 1), "gem": lambda v: num(v, 1), "lat": lambda v: num(v, 1)})

    @render_plotly
    def g_tray():
        fig = go.Figure()
        for g, s in C["trayectoria"].items():
            x = sorted(int(k) for k in s)
            fig.add_trace(go.Scatter(x=x, y=[s[str(a)] for a in x], mode="lines", name=g, line=dict(color=COL_GRUPO[g], width=3 if g == "Colombia" else 2)))
        return figura(fig)

    @render.ui
    def t_periodos():
        d = pd.DataFrame(C["por_periodo"]).T.reset_index().rename(columns={"index": "grupo"})
        cols = [c for c in d.columns if c != "grupo"]
        return tabla(d, [("grupo", "")] + [(c, c) for c in cols], {c: lambda v: num(v, 2) for c in cols})

    @render_plotly
    def g_cont():
        c = C["contabilidad"]["1995-2023"]
        fig = go.Figure()
        for comp, col, nom in [("capital", AZUL, "Capital"), ("capital_humano", MENTA, "Capital humano"), ("productividad", AMBAR, "Productividad (PTF)")]:
            fig.add_trace(go.Bar(x=list(c), y=[c[g][comp] for g in c], name=nom, marker_color=col))
        fig.update_layout(barmode="relative")
        return figura(fig, 340)

    @render_plotly
    def g_conv():
        d = pd.DataFrame(C["convergencia"]["puntos"])
        fig = go.Figure(go.Scatter(x=np.exp(d.log_ini), y=d.crec, mode="markers", text=d.iso3.map(NOMBRE),
                                   marker=dict(size=7, color=[ROSA if i == "COL" else (AZUL if i in ESTABLES else GRIS) for i in d.iso3]),
                                   hovertemplate="%{text}<br>%{y:.2f} % por año<extra></extra>"))
        fig.update_xaxes(type="log", title="PIB por persona en 2000 (PPA, escala log)")
        fig.update_yaxes(title="Crecimiento anual 2000-2024 (%)")
        return figura(fig, 420)

    def disp(d, titulo_x, titulo_y):
        d = pd.DataFrame(d["puntos"])
        fig = go.Figure(go.Scatter(x=d.y, y=d.v, mode="markers", text=d.pais,
                                   marker=dict(size=7, color=[ROSA if i == "COL" else (AZUL if i in ESTABLES else (AMBAR if l else GRIS)) for i, l in zip(d.iso3, d.lat)]),
                                   hovertemplate="%{text}<br>%{y:.2f}<extra></extra>"))
        o = d.sort_values("y")
        fig.add_trace(go.Scatter(x=o.y, y=o.esperado, mode="lines", line=dict(color=TINTA, dash="dot"), name="Esperado por ingreso"))
        fig.update_xaxes(type="log", title=titulo_x)
        fig.update_yaxes(type="log", title=titulo_y)
        fig.update_layout(showlegend=False)
        return figura(fig, 360)

    @render_plotly
    def g_dens():
        return disp(E["densidad"], "PIB por persona (PPA)", "Empresas nuevas por 1.000 adultos")

    @render_plotly
    def g_gh():
        return disp(E["github"], "PIB por persona (PPA)", "Desarrolladores por 1.000 habitantes")

    @render_plotly
    def g_rues():
        m = pd.DataFrame(E["rues"]["mensual"])
        fig = go.Figure(go.Scatter(x=pd.to_datetime(m.mes), y=m.n, mode="lines", line=dict(color=AZUL)))
        return figura(fig, 300)

    @render.ui
    def t_panel():
        p = E["panel"]
        d = pd.DataFrame([{"rel": "Densidad de hoy → crecimiento de los 3 años siguientes", **p["densidad_a_crecimiento"]},
                          {"rel": "Crecimiento de hoy → cambio en la densidad en 3 años", **p["crecimiento_a_densidad"]}])
        return ui.div(tabla(d, [("rel", "Relación"), ("coef", "Coeficiente"), ("ee", "Error estándar"), ("p", "Valor p"), ("n", "Observaciones")],
                            {"coef": lambda v: num(v, 3), "ee": lambda v: num(v, 3), "p": lambda v: num(v, 2), "n": lambda v: num(v, 0)}),
                      ui.p({"class": "nota"}, "Efectos fijos de país y de año; errores agrupados por país. Ninguna de las dos relaciones es significativa."))

    @render.ui
    def t_eval():
        rows = []
        for h, nom in [("h1", "1 año"), ("h3", "3 años")]:
            ev = F["evaluacion"][h]
            rows.append({"h": nom, **{k: v for k, v in ev["mae"].items()}})
        d = pd.DataFrame(rows)
        f2 = lambda v: num(v, 2)
        return tabla(d, [("h", "Horizonte"), ("ingenuo", "Ingenuo"), ("ridge", "Ridge"), ("boosting", "Boosting"), ("boosting_sin_emprendimiento", "Boosting sin emprendimiento")],
                     {"ingenuo": f2, "ridge": f2, "boosting": f2, "boosting_sin_emprendimiento": f2})

    @render_plotly
    def g_back():
        d = pd.DataFrame(F["evaluacion"]["h1"]["colombia"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=d["T"], y=d.y, mode="lines+markers", name="Observado", line=dict(color=TINTA, width=3)))
        for c, col, n in [("ingenuo", GRIS, "Ingenuo"), ("ridge", AMBAR, "Ridge"), ("boosting", AZUL, "Boosting")]:
            fig.add_trace(go.Scatter(x=d["T"], y=d[c], mode="lines+markers", name=n, line=dict(color=col)))
        fig.update_yaxes(title="Crecimiento del PIB por persona (%)")
        return figura(fig)

    @render_plotly
    def g_exp():
        v = input.var()
        fig = go.Figure()
        for iso, col in [("COL", ROSA), (input.pais(), AZUL)]:
            d = P[P.iso3 == iso].sort_values("anio")
            fig.add_trace(go.Scatter(x=d.anio, y=d[v], mode="lines", name=NOMBRE.get(iso, iso), line=dict(color=col, width=2.5)))
        if v == "pib_pc_ppa":
            fig.update_yaxes(type="log")
        return figura(fig, 420)


app = App(app_ui, server)
