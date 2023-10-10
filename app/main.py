import dash_daq as daq
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objs as go
import uvicorn
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

from .obtener_datos import (
    obtener_datos_activo_id_activo_petroleo,
    obtener_todos_datos_activo_petroleo,
)

df = pd.DataFrame(obtener_todos_datos_activo_petroleo())

app_dash = Dash(__name__, requests_pathname_prefix="/dash/")

app_dash.layout = html.Div(
    [
        dcc.Interval(id="update_value", interval=2 * 1000),
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
                dcc.Graph(
                    id="live-graph",
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
            ]
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


@app_dash.callback(
    Output("live-graph", "figure"),
    Input("update_value", "n_intervals"),
    Input("id_activo_petroleo", "value"),
)
def update_graph_scatter(n_intervals, id_activo_petroleo=df["id_activo_petroleo"][0]):
    global df

    df = pd.DataFrame(obtener_datos_activo_id_activo_petroleo(id_activo_petroleo))

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

    data = plotly.graph_objs.Scatter(
        x=list(df["timestamp"]),
        y=df["presion"],
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
                range=[max(df["timestamp"]) - seconds_ago, df["timestamp"].max()],
                title="<b>Hora (HH::MM:SS)</b>",
                color="black",
                showline=True,
                showgrid=True,
                linecolor="black",
                linewidth=1,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="black"),
            ),
            yaxis=dict(
                range=[min(df["presion"]), max(df["presion"])],
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
    Output("daq_gauge1", "value"),
    [
        Input("update_value", "n_intervals"),
    ],
)
def update_confirmed(n_intervals):
    get_temp = df["almacenamiento_disponible"].head(1).iloc[0]
    return get_temp


@app_dash.callback(
    Output("daq_gauge2", "value"),
    [
        Input("update_value", "n_intervals"),
    ],
)
def update_confirmed(n_intervals):
    get_temp = df["temperatura"].head(1).iloc[0]
    return get_temp


@app_dash.callback(
    Output("graph", "figure"),
    [
        Input("update_value", "n_intervals"),
    ],
)
def generate_chart(n_intervals):
    fig = px.scatter_mapbox(
        df,
        lat="latitud",
        lon="longitud",
        zoom=3,
    )
    fig.update_layout(mapbox_style="open-street-map")
    return fig


app = FastAPI()

app.mount("/dash", WSGIMiddleware(app_dash.server))

if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True, port=8080)
