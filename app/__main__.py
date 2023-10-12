from datetime import datetime

import dash_bootstrap_components as dbc
import dash_daq as daq
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objs as go
import uvicorn
from dash import Dash, State, dash_table, dcc, html
from dash.dependencies import Input, Output
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

from .monitoero_activo import endpoint as monitoero_activo_enpoint
from .monitoero_activo.endpoint import df

app_dash = Dash(title="Petroli", requests_pathname_prefix="/dash/", update_title=None)

app_dash.layout = html.Div(
    [
        dcc.Interval(id="update_value", interval=1 * 1000),
        html.Div(
            [
                html.H1(children="Graficos de PETROLI", style={"textAlign": "center"}),
                html.H5("ID Activo petrolero"),
                dcc.Dropdown(
                    id="id_activo_petroleo",
                    options=sorted(df["id_activo_petroleo"].unique()),
                    value=df["id_activo_petroleo"][0],
                ),
            ]
        ),
        html.Div(
            [
                dash_table.DataTable(
                    id="table",
                    columns=[{"name": i, "id": i} for i in df.columns],
                    page_size=10,
                    style_table={"overflow-x": "auto"},
                    sort_action="native",
                ),
                dcc.Graph(
                    id="live-graph-presion",
                    animate=True,
                    style={"display": "flex", "flex-direction": "column"},
                ),
                dcc.Graph(
                    id="live-graph-flujo",
                    animate=True,
                    style={"display": "flex", "flex-direction": "column"},
                ),
            ]
        ),
        html.Div(
            [
                daq.Gauge(
                    showCurrentValue=True,
                    label="Almacenamiento",
                    style={
                        "color": "blue",
                        "fontFamily": "sans-serif",
                        "fontWeight": "bold",
                    },
                    scale={"start": 0, "interval": 10, "labelInterval": 1},
                    id="daq_gauge1",
                    min=0,
                    max=100,
                    value=0,
                    units="t",
                    color="blue",
                ),
                daq.Gauge(
                    showCurrentValue=True,
                    label="Temperatura",
                    style={
                        "color": "red",
                        "fontFamily": "sans-serif",
                        "fontWeight": "bold",
                    },
                    scale={"start": 0, "interval": 20, "labelInterval": 1},
                    id="daq_gauge2",
                    min=-15,
                    max=200,
                    value=0,
                    units="°C",
                    color="red",
                ),
            ],
            className="d-grid gap-2",
        ),
        html.Div(
            [
                dcc.Graph(id="graph"),
                html.H1(children="Descargar todos los datos", style={"textAlign": "center"}),
                dcc.Download(id="download"),
                dcc.Dropdown(
                    options=[
                        {"label": "Excel file", "value": "excel"},
                        {"label": "CSV file", "value": "csv"},
                    ],
                    id="dropdown",
                    placeholder="Choose download file type. Default is CSV format!",
                ),
                dbc.Col(
                    [
                        dbc.Button("Download Data", id="btn_csv"),
                    ]
                ),
            ]
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


@app_dash.callback(
    Output("table", "data"),
    [
        Input("update_value", "n_intervals"),
        Input("id_activo_petroleo", "value"),
    ],
)
def update_graph(n_intervals, id_activo_petroleo=df["id_activo_petroleo"][0]):
    dff: pd.DataFrame = df.loc[df["id_activo_petroleo"] == id_activo_petroleo].copy()
    return dff.to_dict("records")


@app_dash.callback(
    Output("download", "data"),
    Input("btn_csv", "n_clicks"),
    State("dropdown", "value"),
    prevent_initial_call=True,
)
def func(n_clicks_btn, download_type):
    if download_type == "csv":
        return dcc.send_data_frame(
            df.to_csv,
            f"reporte-petroli-{datetime.now().strftime('%m/%d/%Y_%H:%M:%S')}.csv",
        )
    else:
        return dcc.send_data_frame(
            df.to_excel, f"reporte-petroli-{datetime.now().strftime('%m/%d/%Y_%H:%M:%S')}.xlsx"
        )


@app_dash.callback(
    Output("live-graph-presion", "figure"),
    Input("update_value", "n_intervals"),
    Input("id_activo_petroleo", "value"),
)
def update_graph_scatter(n_intervals, id_activo_petroleo=df["id_activo_petroleo"][0]):
    dff = df.loc[df["id_activo_petroleo"] == id_activo_petroleo].copy()
    dff["timestamp"] = pd.to_datetime(dff["timestamp"], format="mixed")

    data = plotly.graph_objs.Scatter(
        x=list(dff["timestamp"]),
        y=dff["presion"],
        name="Scatter",
        mode="lines+markers+text",
        textfont=dict(color="#E58606"),
        marker=dict(color="#5D69B1", size=8),
        line=dict(color="#52BCA3", width=1),
    )

    seconds_ago = pd.Timedelta(seconds=500)

    return {
        "data": [data],
        "layout": go.Layout(
            plot_bgcolor="rgba(255, 255, 255, 0)",
            paper_bgcolor="rgba(255, 255, 255, 0)",
            title={
                "text": "<b>Presión vs Tiempo</b>",
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            titlefont={"color": "black", "size": 24},
            margin=dict(t=50, r=10),
            xaxis=dict(
                range=[max(dff["timestamp"]) - seconds_ago, dff["timestamp"].max()],
                title="<b>Hora (MM:SS)</b>",
                color="black",
                showline=True,
                showgrid=True,
                linecolor="black",
                linewidth=1,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="black"),
            ),
            yaxis=dict(
                range=[min(dff["presion"]), max(dff["presion"])],
                title="<b>Presion (Pa)</b>",
                color="black",
                zeroline=False,
                showline=True,
                showgrid=True,
                linecolor="black",
                linewidth=1,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="black"),
            ),
        ),
    }


@app_dash.callback(
    Output("live-graph-flujo", "figure"),
    Input("update_value", "n_intervals"),
    Input("id_activo_petroleo", "value"),
)
def update_graph_scatter(n_intervals, id_activo_petroleo=df["id_activo_petroleo"][0]):
    dff = df.loc[df["id_activo_petroleo"] == id_activo_petroleo].copy()
    dff["timestamp"] = pd.to_datetime(dff["timestamp"], format="mixed")

    data = plotly.graph_objs.Scatter(
        x=list(dff["timestamp"]),
        y=dff["flujo"],
        name="Scatter",
        mode="lines+markers+text",
        textfont=dict(color="#E58606"),
        marker=dict(color="#5D69B1", size=8),
        line=dict(color="#52BCA3", width=1),
    )

    seconds_ago = pd.Timedelta(seconds=500)

    return {
        "data": [data],
        "layout": go.Layout(
            plot_bgcolor="rgba(255, 255, 255, 0)",
            paper_bgcolor="rgba(255, 255, 255, 0)",
            title={
                "text": "<b>Flujo vs Tiempo</b>",
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            titlefont={"color": "black", "size": 24},
            margin=dict(t=50, r=10),
            xaxis=dict(
                range=[max(dff["timestamp"]) - seconds_ago, dff["timestamp"].max()],
                title="<b>Hora (MM:SS)</b>",
                color="black",
                showline=True,
                showgrid=True,
                linecolor="black",
                linewidth=1,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="black"),
            ),
            yaxis=dict(
                range=[min(dff["flujo"]), max(dff["flujo"])],
                title="<b>Flujo (gpm)</b>",
                color="black",
                zeroline=False,
                showline=True,
                showgrid=True,
                linecolor="black",
                linewidth=1,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="black"),
            ),
        ),
    }


@app_dash.callback(
    Output("id_activo_petroleo", "options"),
    [
        Input("update_value", "n_intervals"),
    ],
)
def update_confirmed(n_intervals):
    return sorted(df["id_activo_petroleo"].unique())


@app_dash.callback(
    Output("daq_gauge1", "value"),
    [
        Input("update_value", "n_intervals"),
        Input("id_activo_petroleo", "value"),
    ],
)
def update_confirmed(n_intervals, id_activo_petroleo=df["id_activo_petroleo"][0]):
    global df
    dff: pd.DataFrame = df.loc[df["id_activo_petroleo"] == id_activo_petroleo].copy()
    get_storage = dff["almacenamiento_disponible"].tail(1).iloc[0]
    return get_storage


@app_dash.callback(
    Output("daq_gauge2", "value"),
    [
        Input("update_value", "n_intervals"),
        Input("id_activo_petroleo", "value"),
    ],
)
def update_confirmed(n_intervals, id_activo_petroleo=df["id_activo_petroleo"][0]):
    global df
    dff: pd.DataFrame = df.loc[df["id_activo_petroleo"] == id_activo_petroleo].copy()
    get_temp = dff["temperatura"].tail(1).iloc[0]
    return get_temp


@app_dash.callback(
    Output("graph", "figure"),
    [
        Input("update_value", "n_intervals"),
        Input("id_activo_petroleo", "value"),
    ],
)
def generate_chart(n_intervals, id_activo_petroleo=df["id_activo_petroleo"][0]):
    global df
    dff: pd.DataFrame = df.loc[df["id_activo_petroleo"] == id_activo_petroleo].copy()
    fig = px.scatter_mapbox(
        dff,
        lat="latitud",
        lon="longitud",
        zoom=3,
    )
    fig.update_layout(mapbox_style="open-street-map")
    return fig


app = FastAPI()

app.include_router(
    monitoero_activo_enpoint.router,
    prefix="/v1/monitoero_activo",
    tags=["monitoero_activo"],
)

app.mount("/dash", WSGIMiddleware(app_dash.server))


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000)
