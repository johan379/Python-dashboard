import pandas as pd
import plotly.express as px
import dash
from dash import html, Input, Output, dcc, dash_table

from database import obtenerestudiantes

def creartablero(server):

    appnotas = dash.Dash(
        __name__,
        server=server,
        url_base_pathname="/dashprincipal/",
        suppress_callback_exceptions=True
    )

    # ── Layout ────────────────────────────────────────────────────────────────
    appnotas.layout = html.Div(style={"fontFamily": "Arial, sans-serif",
                                      "backgroundColor": "#f0f2f5", "minHeight": "100vh"}, children=[

        html.H1("TABLERO CONTROL DE NOTAS",
                style={"textAlign": "center", "backgroundColor": "#1E1BD2",
                       "color": "white", "padding": "20px", "margin": "0"}),

        # ── Filtros ──
        html.Div(style={"backgroundColor": "white", "padding": "20px",
                        "margin": "15px", "borderRadius": "10px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"}, children=[

            html.H3("Filtros", style={"marginTop": "0", "color": "#1E1BD2"}),

            html.Div(style={"display": "flex", "gap": "30px", "flexWrap": "wrap"}, children=[

                html.Div(style={"flex": "1", "minWidth": "200px"}, children=[
                    html.Label("Carrera:", style={"fontWeight": "bold"}),
                    # PUNTO 2: valor None para mostrar todo tras cargue masivo
                    dcc.Dropdown(id="filtro_carrera", placeholder="Todas las carreras",
                                 clearable=True)
                ]),

                html.Div(style={"flex": "2", "minWidth": "250px"}, children=[
                    html.Label("Rango de edad:", style={"fontWeight": "bold"}),
                    dcc.RangeSlider(id="slider_edad", min=0, max=100, step=1,
                                    value=[0, 100],
                                    tooltip={"placement": "bottom", "always_visible": True})
                ]),

                html.Div(style={"flex": "2", "minWidth": "250px"}, children=[
                    html.Label("Rango de promedio:", style={"fontWeight": "bold"}),
                    dcc.RangeSlider(id="slider_promedio", min=0, max=5, step=0.1,
                                    value=[0, 5],
                                    tooltip={"placement": "bottom", "always_visible": True})
                ]),

                html.Div(style={"flex": "1", "minWidth": "180px"}, children=[
                    html.Label("Buscar estudiante:", style={"fontWeight": "bold"}),
                    dcc.Input(id="busqueda", type="text",
                              placeholder="Nombre...",
                              style={"width": "100%", "padding": "6px",
                                     "borderRadius": "5px", "border": "1px solid #ccc"})
                ]),
            ]),
        ]),

        # ── KPIs ──
        html.Div(id="kpis", style={"display": "flex", "justifyContent": "space-around",
                                   "padding": "0 15px", "flexWrap": "wrap", "gap": "10px"}),

        html.Br(),

        # ── PUNTO 6: Alerta estudiantes en riesgo ──
        html.Div(id="alerta_riesgo", style={"margin": "0 15px"}),

        html.Br(),

        # ── Tabla principal ──
        html.Div(style={"backgroundColor": "white", "padding": "20px", "margin": "15px",
                        "borderRadius": "10px", "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"}, children=[
            html.H3("Listado de Estudiantes", style={"color": "#1E1BD2", "marginTop": "0"}),
            dcc.Loading(
                dash_table.DataTable(
                    id="tabla",
                    page_size=8,
                    filter_action="native",
                    sort_action="native",
                    row_selectable="multi",
                    selected_rows=[],
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "center", "padding": "8px"},
                    style_header={"backgroundColor": "#1E1BD2", "color": "white",
                                  "fontWeight": "bold"},
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#f9f9f9"}
                    ]
                ), type="circle"
            ),
        ]),

        html.Br(),

        # ── PUNTO 5: Ranking Top 10 ──
        html.Div(style={"backgroundColor": "white", "padding": "20px", "margin": "15px",
                        "borderRadius": "10px", "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"}, children=[
            html.H3("🏆 Ranking Top 10 Estudiantes", style={"color": "#1E1BD2", "marginTop": "0"}),
            html.Div(id="ranking_tabla")
        ]),

        html.Br(),

        # ── Gráficos ──
        html.Div(style={"backgroundColor": "white", "padding": "20px", "margin": "15px",
                        "borderRadius": "10px", "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"}, children=[
            dcc.Loading(dcc.Graph(id="gra_detallado"), type="default"),
        ]),

        html.Br(),

        html.Div(style={"margin": "0 15px"}, children=[
            dcc.Tabs([
                dcc.Tab(label="📊 Histograma",    children=[dcc.Graph(id="histograma")]),
                dcc.Tab(label="🔵 Dispersión",    children=[dcc.Graph(id="dispersion")]),
                dcc.Tab(label="🥧 Desempeño",     children=[dcc.Graph(id="pie")]),
                dcc.Tab(label="📈 Prom. Carrera", children=[dcc.Graph(id="barras")]),
            ])
        ]),

        # Intervalo de actualización automática (Punto 2)
        dcc.Interval(id="intervalo", interval=5000, n_intervals=0),

    ])

    # ── Callback principal ─────────────────────────────────────────────────────
    @appnotas.callback(
        Output("filtro_carrera", "options"),
        Output("filtro_carrera", "value"),
        Output("slider_edad",    "min"),
        Output("slider_edad",    "max"),
        Output("slider_edad",    "value"),
        Output("tabla",          "data"),
        Output("tabla",          "columns"),
        Output("kpis",           "children"),
        Output("histograma",     "figure"),
        Output("dispersion",     "figure"),
        Output("pie",            "figure"),
        Output("barras",         "figure"),
        Output("alerta_riesgo",  "children"),   # PUNTO 6
        Output("ranking_tabla",  "children"),   # PUNTO 5

        Input("filtro_carrera",  "value"),
        Input("slider_edad",     "value"),
        Input("slider_promedio", "value"),
        Input("busqueda",        "value"),
        Input("intervalo",       "n_intervals"),
    )
    def actualizar_comp(carrera, rangoedad, rangoprome, busqueda, n_intervals):

        dataf = obtenerestudiantes()

        if dataf.empty:
            fig_vacio = px.scatter(title="Sin datos")
            opciones = []
            sin_datos = html.P("No hay estudiantes registrados.",
                               style={"color": "gray", "textAlign": "center"})
            return (opciones, None, 0, 100, [0, 100],
                    [], [], [], fig_vacio, fig_vacio, fig_vacio, fig_vacio,
                    sin_datos, sin_datos)

        # ── PUNTO 2: opciones del dropdown siempre frescas ──
        opciones = [{"label": c, "value": c} for c in sorted(dataf["Carrera"].unique())]

        # Aplicar filtro de carrera (si hay selección)
        filtro = dataf.copy()
        if carrera:
            filtro = filtro[filtro["Carrera"] == carrera]

        # Actualizar rangos del slider de edad con datos reales
        edad_min = int(dataf["Edad"].min())
        edad_max = int(dataf["Edad"].max())

        if rangoedad is None or rangoedad[0] < edad_min or rangoedad[1] > edad_max:
            rangoedad = [edad_min, edad_max]

        filtro = filtro[
            (filtro["Edad"]     >= rangoedad[0]) &
            (filtro["Edad"]     <= rangoedad[1]) &
            (filtro["Promedio"] >= rangoprome[0]) &
            (filtro["Promedio"] <= rangoprome[1])
        ]

        if busqueda:
            filtro = filtro[
                filtro.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)
            ]

        # ── KPIs ──
        prom_avg  = round(filtro["Promedio"].mean(), 2) if not filtro.empty else 0
        total     = len(filtro)
        prom_max  = round(filtro["Promedio"].max(), 2)  if not filtro.empty else 0

        kpis = [
            html.Div([html.H4("Promedio General"), html.H2(prom_avg)],
                     style={"backgroundColor": "#3498db", "color": "white",
                            "padding": "15px", "borderRadius": "10px",
                            "textAlign": "center", "minWidth": "150px"}),
            html.Div([html.H4("Total Estudiantes"), html.H2(total)],
                     style={"backgroundColor": "#2ecc71", "color": "white",
                            "padding": "15px", "borderRadius": "10px",
                            "textAlign": "center", "minWidth": "150px"}),
            html.Div([html.H4("Promedio Máximo"), html.H2(prom_max)],
                     style={"backgroundColor": "#e67e22", "color": "white",
                            "padding": "15px", "borderRadius": "10px",
                            "textAlign": "center", "minWidth": "150px"}),
        ]

        # ── Gráficos ──
        histo = px.histogram(filtro, x="Promedio", nbins=10,
                             title="Distribución de Promedios",
                             color_discrete_sequence=["#3498db"])

        dispersion = px.scatter(filtro, x="Edad", y="Promedio", color="Desempeño",
                                trendline="ols", title="Edad vs Promedio")

        pie = px.pie(filtro, names="Desempeño", title="Distribución por Desempeño")

        promedios = dataf.groupby("Carrera")["Promedio"].mean().reset_index()
        barras = px.bar(promedios, x="Carrera", y="Promedio", color="Carrera",
                        title="Promedio General por Carrera")

        # ── PUNTO 5: Ranking Top 10 ──
        top10 = (dataf.nlargest(10, "Promedio")
                      [["Nombre", "Carrera", "Promedio"]]
                      .reset_index(drop=True))
        top10.index += 1  # empezar desde 1

        filas_ranking = []
        for pos, row in top10.iterrows():
            medalla = {1: "🥇", 2: "🥈", 3: "🥉"}.get(pos, f"#{pos}")
            color_fila = "#fff9e6" if pos <= 3 else "white"
            filas_ranking.append(
                html.Tr([
                    html.Td(medalla,         style={"padding": "10px", "textAlign": "center",
                                                    "fontSize": "18px"}),
                    html.Td(row["Nombre"],   style={"padding": "10px"}),
                    html.Td(row["Carrera"],  style={"padding": "10px"}),
                    html.Td(f'{row["Promedio"]:.2f}',
                            style={"padding": "10px", "textAlign": "center",
                                   "fontWeight": "bold", "color": "#1E1BD2"}),
                ], style={"backgroundColor": color_fila})
            )

        ranking_tabla = html.Table(
            [html.Thead(html.Tr([
                html.Th("Pos.",     style={"padding": "10px", "backgroundColor": "#1E1BD2",
                                           "color": "white"}),
                html.Th("Nombre",   style={"padding": "10px", "backgroundColor": "#1E1BD2",
                                           "color": "white"}),
                html.Th("Carrera",  style={"padding": "10px", "backgroundColor": "#1E1BD2",
                                           "color": "white"}),
                html.Th("Promedio", style={"padding": "10px", "backgroundColor": "#1E1BD2",
                                           "color": "white"}),
            ])),
             html.Tbody(filas_ranking)],
            style={"width": "100%", "borderCollapse": "collapse",
                   "border": "1px solid #ddd"}
        ) if filas_ranking else html.P("No hay datos para el ranking.",
                                       style={"color": "gray"})

        # ── PUNTO 6: Alerta estudiantes en riesgo ──
        en_riesgo = dataf[dataf["Promedio"] < 3.0][["Nombre", "Carrera", "Promedio"]]
        alerta_riesgo = None

        if not en_riesgo.empty:
            filas_riesgo = [
                html.Tr([
                    html.Td(r["Nombre"],  style={"padding": "8px"}),
                    html.Td(r["Carrera"], style={"padding": "8px"}),
                    html.Td(f'{r["Promedio"]:.2f}',
                            style={"padding": "8px", "textAlign": "center",
                                   "color": "red", "fontWeight": "bold"}),
                ])
                for _, r in en_riesgo.iterrows()
            ]
            alerta_riesgo = html.Div([
                html.H3(" Estudiantes en Riesgo Académico (Promedio < 3.0)",
                        style={"color": "#c0392b", "marginTop": "0"}),
                html.Table(
                    [html.Thead(html.Tr([
                        html.Th("Nombre",   style={"padding": "8px", "backgroundColor": "#e74c3c",
                                                    "color": "white"}),
                        html.Th("Carrera",  style={"padding": "8px", "backgroundColor": "#e74c3c",
                                                    "color": "white"}),
                        html.Th("Promedio", style={"padding": "8px", "backgroundColor": "#e74c3c",
                                                    "color": "white"}),
                    ])),
                     html.Tbody(filas_riesgo)],
                    style={"width": "100%", "borderCollapse": "collapse",
                           "border": "1px solid #e74c3c"}
                )
            ], style={"backgroundColor": "#fdecea", "border": "2px solid #e74c3c",
                      "borderRadius": "10px", "padding": "20px"})

        # ── Gráfico detallado (sin selección aún) ──
        return (
            opciones,
            carrera,           # PUNTO 2: mantiene el valor actual (o None = todas)
            edad_min, edad_max,
            rangoedad,
            filtro.to_dict("records"),
            [{"name": i, "id": i} for i in filtro.columns],
            kpis,
            histo, dispersion, pie, barras,
            alerta_riesgo,
            ranking_tabla
        )

    #  Callback gráfico detallado por selección
    @appnotas.callback(
        Output("gra_detallado", "figure"),
        Input("tabla", "derived_virtual_data"),
        Input("tabla", "derived_virtual_selected_rows")
    )
    def actualizartab(rows, selected_rows):
        if not rows:
            return px.scatter(title="Sin datos — registre o cargue estudiantes")
        dff = pd.DataFrame(rows)
        if selected_rows:
            dff = dff.iloc[selected_rows]
        if dff.empty or "Edad" not in dff.columns:
            return px.scatter(title="Sin datos seleccionados")
        fig = px.scatter(dff, x="Edad", y="Promedio", color="Desempeño",
                         size="Promedio",
                         title="Análisis detallado (seleccione filas de la tabla)",
                         trendline="ols")
        return fig

    return appnotas
